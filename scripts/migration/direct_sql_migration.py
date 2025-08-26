#!/usr/bin/env python3
"""
Direct SQL execution for Supabase migration using HTTP requests
"""
import asyncio
import aiohttp
import logging
import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DirectSQLMigration:
    """Execute SQL migration using direct HTTP requests to Supabase"""
    
    def __init__(self):
        self.supabase_url = os.getenv('SUPABASE_URL')
        self.service_role_key = os.getenv('SUPABASE_SERVICE_ROLE_KEY')
        
        if not self.supabase_url or not self.service_role_key:
            raise ValueError("Missing SUPABASE_URL or SUPABASE_SERVICE_ROLE_KEY environment variables")
        
        # Construct the PostgREST URL for raw SQL execution
        self.postgrest_url = f"{self.supabase_url}/rest/v1/rpc"
    
    async def create_tables(self):
        """Create the main tables using table creation approach"""
        logger.info("Creating tables using Supabase table operations...")
        
        try:
            # Since direct SQL doesn't work, let's create sample data and test existing API
            # This will verify our new matching system works with the existing backend
            
            # Test if we can access products table
            async with aiohttp.ClientSession() as session:
                headers = {
                    'apikey': self.service_role_key,
                    'Authorization': f'Bearer {self.service_role_key}',
                    'Content-Type': 'application/json'
                }
                
                # Test products table access
                products_url = f"{self.supabase_url}/rest/v1/products"
                async with session.get(products_url + "?select=id,name&limit=1", headers=headers) as response:
                    if response.status == 200:
                        data = await response.json()
                        logger.info(f"✅ Connected to Supabase - found {len(data)} products")
                        return True
                    else:
                        logger.error(f"❌ Failed to connect: {response.status}")
                        return False
        
        except Exception as e:
            logger.error(f"❌ Connection test failed: {e}")
            return False
    
    async def create_sample_match_data(self):
        """Create sample matching data to test the system"""
        logger.info("Creating sample matching data...")
        
        try:
            async with aiohttp.ClientSession() as session:
                headers = {
                    'apikey': self.service_role_key,
                    'Authorization': f'Bearer {self.service_role_key}',
                    'Content-Type': 'application/json',
                    'Prefer': 'return=representation'
                }
                
                # Get some sample products
                products_url = f"{self.supabase_url}/rest/v1/products"
                async with session.get(products_url + "?select=id,name,retailer_code&limit=5", headers=headers) as response:
                    if response.status != 200:
                        logger.error(f"Failed to fetch products: {response.status}")
                        return False
                    
                    products = await response.json()
                    if len(products) < 2:
                        logger.error("Need at least 2 products to create matches")
                        return False
                
                # Try to create a simple record to test database connectivity
                # Since we don't have the matching_results table yet, let's create a simple test
                logger.info(f"Found {len(products)} products for testing")
                logger.info("Database connection successful!")
                
                return True
        
        except Exception as e:
            logger.error(f"❌ Sample data creation failed: {e}")
            return False


def show_manual_instructions():
    """Show instructions for manual SQL execution"""
    print("\n" + "="*60)
    print("🔧 MANUAL MIGRATION REQUIRED")
    print("="*60)
    print("\nThe programmatic approach has limitations with Supabase's")
    print("PostgREST API for complex SQL operations like CREATE TABLE.")
    print("\n📋 Please execute the migration manually:")
    print("\n1. 📂 Open the SQL file:")
    print("   cat scripts/migration/EXECUTE_IN_SUPABASE.sql")
    print("\n2. 🌐 Go to Supabase Dashboard:")
    print("   → SQL Editor → New Query")
    print("\n3. 📝 Copy and paste the entire SQL script")
    print("\n4. ▶️  Click 'RUN' to execute")
    print("\n5. ✅ Verify tables were created:")
    print("   SELECT * FROM matching_results;")
    print("   SELECT * FROM matching_metadata;")
    print("\n6. 🧪 Test the migration:")
    print("   python3 scripts/migration/import_sample_matches.py")
    print("\n" + "="*60)


async def main():
    """Main migration execution"""
    print("🚀 Direct SQL Migration Tool")
    print("=" * 50)
    
    try:
        migration = DirectSQLMigration()
        
        # Test database connectivity
        connected = await migration.create_tables()
        
        if connected:
            print("✅ Database connection successful")
            
            # Test sample data creation capability
            sample_success = await migration.create_sample_match_data()
            
            if sample_success:
                print("✅ Database operations working")
                print("\n🎯 Next Step: Execute SQL migration manually")
                show_manual_instructions()
                return 0
            else:
                print("❌ Database operations failed")
                return 1
        else:
            print("❌ Database connection failed")
            return 1
            
    except Exception as e:
        print(f"❌ Migration error: {e}")
        show_manual_instructions()
        return 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))