#!/usr/bin/env python3
"""
Simple table creation for matching system
Creates only the essential tables first
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


class SimpleTableMigration:
    """Create essential matching tables"""
    
    def __init__(self):
        self.postgres_url = os.getenv('POSTGRES_URL_NON_POOLING') or os.getenv('POSTGRES_URL')
        if not self.postgres_url:
            raise ValueError("Missing POSTGRES_URL environment variable")
    
    async def run_migration(self):
        """Execute the table creation"""
        logger.info("🚀 Creating matching system tables...")
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
            
            # Create tables step by step
            await self._create_matching_results_table(conn)
            await self._create_matching_metadata_table(conn)
            await self._create_basic_indexes(conn)
            await self._create_update_trigger(conn)
            
            # Test the tables
            await self._test_tables(conn)
            
            # Close connection
            await conn.close()
            
            logger.info("\n🎉 Basic tables created successfully!")
            logger.info("✅ matching_results table")
            logger.info("✅ matching_metadata table")
            logger.info("✅ Basic indexes")
            logger.info("✅ Update triggers")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Migration failed: {e}")
            return False
    
    async def _create_matching_results_table(self, conn):
        """Create matching_results table"""
        sql = '''
        CREATE TABLE IF NOT EXISTS matching_results (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            source_product_id UUID NOT NULL REFERENCES products(id) ON DELETE CASCADE,
            matched_product_id UUID NOT NULL REFERENCES products(id) ON DELETE CASCADE,
            confidence_score DECIMAL(3,2) NOT NULL CHECK (confidence_score >= 0 AND confidence_score <= 1),
            matching_method VARCHAR(20) NOT NULL CHECK (matching_method IN ('name', 'sku', 'brand', 'specifications', 'hybrid')),
            status VARCHAR(10) NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'confirmed', 'rejected')),
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            UNIQUE(source_product_id, matched_product_id)
        );
        '''
        
        await conn.execute(sql)
        logger.info("✅ matching_results table created")
    
    async def _create_matching_metadata_table(self, conn):
        """Create matching_metadata table"""
        sql = '''
        CREATE TABLE IF NOT EXISTS matching_metadata (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            matching_result_id UUID NOT NULL REFERENCES matching_results(id) ON DELETE CASCADE,
            metadata_key VARCHAR(100) NOT NULL,
            metadata_value JSONB NOT NULL,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
        );
        '''
        
        await conn.execute(sql)
        logger.info("✅ matching_metadata table created")
    
    async def _create_basic_indexes(self, conn):
        """Create basic indexes"""
        indexes = [
            "CREATE INDEX IF NOT EXISTS idx_matching_results_source_product ON matching_results(source_product_id);",
            "CREATE INDEX IF NOT EXISTS idx_matching_results_matched_product ON matching_results(matched_product_id);",
            "CREATE INDEX IF NOT EXISTS idx_matching_results_confidence_status ON matching_results(confidence_score DESC, status);",
            "CREATE INDEX IF NOT EXISTS idx_matching_metadata_result_id ON matching_metadata(matching_result_id);",
        ]
        
        for sql in indexes:
            await conn.execute(sql)
        
        logger.info("✅ Basic indexes created")
    
    async def _create_update_trigger(self, conn):
        """Create update trigger"""
        # Create function
        function_sql = '''
        CREATE OR REPLACE FUNCTION update_updated_at_column()
        RETURNS TRIGGER AS $$
        BEGIN
            NEW.updated_at = NOW();
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
        '''
        
        # Create trigger
        trigger_sql = '''
        DROP TRIGGER IF EXISTS update_matching_results_updated_at ON matching_results;
        CREATE TRIGGER update_matching_results_updated_at 
            BEFORE UPDATE ON matching_results 
            FOR EACH ROW 
            EXECUTE FUNCTION update_updated_at_column();
        '''
        
        await conn.execute(function_sql)
        await conn.execute(trigger_sql)
        logger.info("✅ Update trigger created")
    
    async def _test_tables(self, conn):
        """Test table creation"""
        logger.info("\n🧪 Testing tables...")
        
        # Test matching_results table
        result = await conn.fetch("SELECT count(*) as count FROM matching_results;")
        logger.info(f"✅ matching_results: {result[0]['count']} rows")
        
        # Test matching_metadata table
        result = await conn.fetch("SELECT count(*) as count FROM matching_metadata;")
        logger.info(f"✅ matching_metadata: {result[0]['count']} rows")


async def main():
    """Main migration execution"""
    print("🚀 Simple Table Migration")
    print("=" * 50)
    print("This will create the essential matching system tables")
    print("")
    
    try:
        migration = SimpleTableMigration()
        success = await migration.run_migration()
        
        if success:
            print("\n📋 Next Steps:")
            print("1. Test with sample data: python scripts/migration/import_sample_matches.py")
            print("2. Check new API endpoints: http://localhost:8001/api/v2/matches/stats")
            print("3. Add more functions manually in Supabase SQL Editor if needed")
            return 0
        else:
            print("\n❌ Migration failed")
            return 1
            
    except Exception as e:
        print(f"\n❌ Migration error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))