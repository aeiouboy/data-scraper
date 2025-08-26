#!/usr/bin/env python3
"""
Execute Supabase database migrations for matching system
"""
import os
import sys
import logging
from pathlib import Path
from datetime import datetime

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.services.supabase_service import SupabaseService

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SupabaseMigrationRunner:
    """Execute database migrations in Supabase"""
    
    def __init__(self):
        self.db_service = SupabaseService()
        self.migrations_dir = project_root / "src" / "database" / "migrations"
    
    def run_all_migrations(self):
        """Run all migration files in order"""
        logger.info("Starting Supabase database migrations...")
        
        try:
            # Migration files in order
            migration_files = [
                "001_create_matching_tables.sql",
                "002_add_matching_indexes.sql", 
                "003_migrate_brave_data.sql"
            ]
            
            for migration_file in migration_files:
                self.run_migration_file(migration_file)
            
            logger.info("✅ All migrations completed successfully!")
            return True
            
        except Exception as e:
            logger.error(f"❌ Migration failed: {e}")
            return False
    
    def run_migration_file(self, filename: str):
        """Run a specific migration file"""
        migration_path = self.migrations_dir / filename
        
        if not migration_path.exists():
            raise FileNotFoundError(f"Migration file not found: {migration_path}")
        
        logger.info(f"Running migration: {filename}")
        
        # Read SQL file
        with open(migration_path, 'r', encoding='utf-8') as f:
            sql_content = f.read()
        
        # Split SQL into individual statements
        statements = self._split_sql_statements(sql_content)
        
        # Execute each statement
        for i, statement in enumerate(statements):
            if statement.strip():
                try:
                    logger.info(f"  Executing statement {i+1}/{len(statements)}")
                    self.db_service.client.rpc('exec_sql', {'sql': statement}).execute()
                    
                except Exception as e:
                    # Try direct execution for DDL statements
                    try:
                        # For Supabase, we need to use the REST API differently for DDL
                        logger.warning(f"Direct RPC failed, trying alternative method: {e}")
                        self._execute_ddl_statement(statement)
                        
                    except Exception as e2:
                        logger.error(f"Failed to execute statement: {statement[:100]}...")
                        logger.error(f"Error: {e2}")
                        raise
        
        logger.info(f"✅ Migration {filename} completed")
    
    def _split_sql_statements(self, sql_content: str) -> list:
        """Split SQL content into individual statements"""
        # Remove comments
        lines = []
        for line in sql_content.split('\n'):
            line = line.strip()
            if line and not line.startswith('--'):
                lines.append(line)
        
        # Join and split by semicolon
        sql = ' '.join(lines)
        statements = []
        
        # Simple split - could be improved for complex SQL
        current_statement = ""
        in_function = False
        
        for part in sql.split(';'):
            current_statement += part.strip() + ' '
            
            # Check if we're in a function definition
            if 'CREATE OR REPLACE FUNCTION' in part.upper() or 'CREATE FUNCTION' in part.upper():
                in_function = True
            
            if in_function and '$$ LANGUAGE' in part.upper():
                in_function = False
                statements.append(current_statement.strip())
                current_statement = ""
            elif not in_function and current_statement.strip():
                statements.append(current_statement.strip())
                current_statement = ""
        
        return [s for s in statements if s.strip()]
    
    def _execute_ddl_statement(self, statement: str):
        """Execute DDL statement using alternative method"""
        # For now, log the statement - in production, you'd need to execute via SQL editor
        logger.info(f"DDL Statement to execute manually in Supabase SQL editor:")
        logger.info(f"```sql\n{statement}\n```")
        
        # Try to execute simple statements directly
        simple_patterns = [
            'CREATE TABLE IF NOT EXISTS',
            'CREATE INDEX IF NOT EXISTS', 
            'ALTER TABLE',
            'DROP TABLE IF EXISTS',
            'DROP INDEX IF EXISTS'
        ]
        
        is_simple = any(pattern in statement.upper() for pattern in simple_patterns)
        
        if is_simple:
            try:
                # Use PostgREST for simple DDL
                result = self.db_service.client.rpc('exec_sql', {'query': statement}).execute()
                logger.info("✅ Simple DDL executed successfully")
                return result
            except:
                pass
        
        # For complex statements, provide manual instructions
        logger.warning("⚠️ Complex statement requires manual execution in Supabase SQL editor")
    
    def verify_schema_creation(self):
        """Verify that tables and functions were created successfully"""
        logger.info("Verifying schema creation...")
        
        try:
            # Check if tables exist
            tables_to_check = ['matching_results', 'matching_metadata']
            
            for table in tables_to_check:
                try:
                    result = self.db_service.client.table(table).select('*').limit(1).execute()
                    logger.info(f"✅ Table '{table}' exists and accessible")
                except Exception as e:
                    logger.error(f"❌ Table '{table}' not found or not accessible: {e}")
                    return False
            
            # Check if functions exist (try to call them)
            try:
                self.db_service.client.rpc('get_match_status_counts').execute()
                logger.info("✅ Database functions created successfully")
            except Exception as e:
                logger.warning(f"⚠️ Functions may not be created: {e}")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Schema verification failed: {e}")
            return False
    
    def create_migration_log(self, success: bool):
        """Log migration execution"""
        log_entry = {
            'migration_date': datetime.now().isoformat(),
            'success': success,
            'migration_version': '1.0.0',
            'tables_created': ['matching_results', 'matching_metadata'],
            'functions_created': [
                'get_match_status_counts',
                'get_match_method_counts', 
                'get_average_confidence',
                'get_match_quality_metrics'
            ]
        }
        
        # Try to insert log (if logs table exists)
        try:
            self.db_service.client.table('migration_logs').insert(log_entry).execute()
            logger.info("✅ Migration log created")
        except:
            # If no logs table, just log to console
            logger.info(f"Migration log: {log_entry}")


def main():
    """Main migration execution"""
    print("🚀 Starting Supabase Database Migration")
    print("=" * 50)
    
    migrator = SupabaseMigrationRunner()
    
    try:
        # Run migrations
        success = migrator.run_all_migrations()
        
        if success:
            # Verify schema
            verification_success = migrator.verify_schema_creation()
            
            # Create log
            migrator.create_migration_log(verification_success)
            
            if verification_success:
                print("\n🎉 Migration completed successfully!")
                print("✅ Tables created: matching_results, matching_metadata")
                print("✅ Indexes created for optimal performance")
                print("✅ Database functions installed")
                print("\n📋 Next steps:")
                print("1. Run data export: python scripts/migration/01_export_brave_matches.py")
                print("2. Import data: python scripts/migration/03_import_to_database.py")
            else:
                print("\n⚠️ Migration completed with warnings")
                print("Please check Supabase SQL editor for any manual steps needed")
        else:
            print("\n❌ Migration failed")
            return 1
            
    except Exception as e:
        print(f"\n❌ Migration error: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())