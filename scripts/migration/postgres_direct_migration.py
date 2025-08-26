#!/usr/bin/env python3
"""
Direct PostgreSQL migration using psycopg2
"""
import asyncio
import asyncpg
import logging
import os
import sys
from pathlib import Path
from urllib.parse import urlparse

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class PostgresMigration:
    """Execute SQL migration using direct PostgreSQL connection"""
    
    def __init__(self):
        self.postgres_url = os.getenv('POSTGRES_URL_NON_POOLING') or os.getenv('POSTGRES_URL')
        if not self.postgres_url:
            raise ValueError("Missing POSTGRES_URL environment variable")
    
    async def run_migration(self):
        """Execute the complete migration"""
        logger.info("🚀 Starting PostgreSQL direct migration...")
        logger.info("=" * 60)
        
        try:
            # Parse the connection URL
            parsed = urlparse(self.postgres_url)
            
            # Connect to database
            conn = await asyncpg.connect(
                host=parsed.hostname,
                port=parsed.port,
                user=parsed.username,
                password=parsed.password,
                database=parsed.path[1:],  # Remove leading slash
                ssl='require'
            )
            
            logger.info("✅ Connected to PostgreSQL database")
            
            # Read the migration SQL
            migration_file = project_root / "scripts/migration/EXECUTE_IN_SUPABASE.sql"
            with open(migration_file, 'r', encoding='utf-8') as f:
                sql_content = f.read()
            
            # Split into individual statements
            statements = self._extract_sql_statements(sql_content)
            
            success_count = 0
            total_statements = len(statements)
            
            # Execute each statement
            async with conn.transaction():
                for i, statement in enumerate(statements, 1):
                    if statement.strip() and not statement.strip().startswith('--'):
                        try:
                            logger.info(f"Executing statement {i}/{total_statements}...")
                            await conn.execute(statement)
                            success_count += 1
                            logger.info(f"✅ Statement {i} completed")
                        except Exception as e:
                            logger.error(f"❌ Statement {i} failed: {e}")
                            # Continue with other statements
                            continue
            
            # Test the migration
            await self._test_migration(conn)
            
            # Close connection
            await conn.close()
            
            logger.info(f"\n🎉 Migration completed!")
            logger.info(f"✅ {success_count}/{total_statements} statements executed successfully")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Migration failed: {e}")
            return False
    
    def _extract_sql_statements(self, sql_content: str) -> list:
        """Extract executable SQL statements from the migration file"""
        statements = []
        current_statement = ""
        in_function = False
        
        lines = sql_content.split('\n')
        
        for line in lines:
            line = line.strip()
            
            # Skip comments and empty lines
            if not line or line.startswith('--'):
                continue
            
            current_statement += line + ' '
            
            # Handle function definitions
            if 'CREATE OR REPLACE FUNCTION' in line.upper() or 'CREATE FUNCTION' in line.upper():
                in_function = True
            
            # End of statement
            if line.endswith(';'):
                if in_function and '$$ LANGUAGE plpgsql' in current_statement.upper():
                    in_function = False
                
                if not in_function or '$$ LANGUAGE plpgsql' in current_statement.upper():
                    statements.append(current_statement.strip())
                    current_statement = ""
        
        # Add any remaining statement
        if current_statement.strip():
            statements.append(current_statement.strip())
        
        return statements
    
    async def _test_migration(self, conn):
        """Test the migration by verifying tables and functions"""
        logger.info("\n🧪 Testing migration...")
        
        try:
            # Test table creation
            result = await conn.fetch("SELECT count(*) as count FROM matching_results;")
            logger.info(f"✅ matching_results table: {result[0]['count']} rows")
            
            result = await conn.fetch("SELECT count(*) as count FROM matching_metadata;")
            logger.info(f"✅ matching_metadata table: {result[0]['count']} rows")
            
            # Test functions
            try:
                result = await conn.fetch("SELECT * FROM get_match_quality_metrics();")
                logger.info("✅ Database functions working")
            except Exception as e:
                logger.warning(f"⚠️ Functions test failed: {e}")
            
            # Test view
            try:
                result = await conn.fetch("SELECT count(*) as count FROM match_analytics_view;")
                logger.info(f"✅ match_analytics_view: {result[0]['count']} rows")
            except Exception as e:
                logger.warning(f"⚠️ View test failed: {e}")
            
        except Exception as e:
            logger.error(f"❌ Migration test failed: {e}")
            raise


async def main():
    """Main migration execution"""
    print("🚀 PostgreSQL Direct Migration")
    print("=" * 50)
    print("This will execute the SQL migration directly via PostgreSQL connection")
    print("")
    
    try:
        migration = PostgresMigration()
        success = await migration.run_migration()
        
        if success:
            print("\n📋 Next Steps:")
            print("1. Test API endpoints: http://localhost:8001/api/v2/matches/stats")
            print("2. Import sample data: python scripts/migration/import_sample_matches.py")
            print("3. Run full data export when ready")
            return 0
        else:
            print("\n❌ Migration failed")
            return 1
            
    except Exception as e:
        print(f"\n❌ Migration error: {e}")
        print("\n🔧 Alternative: Manual SQL execution")
        print("Copy the SQL from: scripts/migration/EXECUTE_IN_SUPABASE.sql")
        print("Paste into Supabase Dashboard → SQL Editor")
        return 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))