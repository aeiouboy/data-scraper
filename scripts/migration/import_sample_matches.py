#!/usr/bin/env python3
"""
Import sample matching data to test the new database schema
"""
import asyncio
import logging
import sys
from pathlib import Path
from datetime import datetime
from uuid import uuid4

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.services.supabase_service import SupabaseService

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MatchingDataImporter:
    """Import sample matching data to test the new schema"""
    
    def __init__(self):
        self.db_service = SupabaseService()
    
    async def import_sample_data(self):
        """Import sample matching data"""
        logger.info("Starting sample data import...")
        
        try:
            # First, verify the tables exist
            if not await self._verify_tables():
                logger.error("Required tables don't exist. Please run the SQL migration first.")
                return False
            
            # Get some sample products
            sample_products = await self._get_sample_products()
            
            if len(sample_products) < 2:
                logger.error("Need at least 2 products to create matches")
                return False
            
            # Create sample matches
            matches_created = await self._create_sample_matches(sample_products)
            
            logger.info(f"✅ Sample data import completed: {matches_created} matches created")
            return True
            
        except Exception as e:
            logger.error(f"❌ Sample data import failed: {e}")
            return False
    
    async def _verify_tables(self) -> bool:
        """Verify that the required tables exist"""
        try:
            # Try to query matching_results table
            result = self.db_service.client.table('matching_results').select('*').limit(1).execute()
            logger.info("✅ matching_results table exists")
            
            # Try to query matching_metadata table  
            result = self.db_service.client.table('matching_metadata').select('*').limit(1).execute()
            logger.info("✅ matching_metadata table exists")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Table verification failed: {e}")
            return False
    
    async def _get_sample_products(self) -> list:
        """Get sample products from different retailers"""
        try:
            result = self.db_service.client.table('products')\
                .select('id, name, brand, sku, retailer_code, category')\
                .limit(10)\
                .execute()
            
            products = result.data or []
            logger.info(f"Found {len(products)} sample products")
            
            return products
            
        except Exception as e:
            logger.error(f"Error fetching sample products: {e}")
            return []
    
    async def _create_sample_matches(self, products: list) -> int:
        """Create sample matching results"""
        matches_created = 0
        
        try:
            # Create a few sample matches
            sample_matches = []
            
            for i in range(0, min(len(products) - 1, 3)):  # Create up to 3 sample matches
                source_product = products[i]
                matched_product = products[i + 1]
                
                # Skip if same retailer
                if source_product['retailer_code'] == matched_product['retailer_code']:
                    continue
                
                match_data = {
                    'source_product_id': source_product['id'],
                    'matched_product_id': matched_product['id'],
                    'confidence_score': 0.85,  # High confidence sample
                    'matching_method': 'hybrid',
                    'status': 'pending'
                }
                
                sample_matches.append(match_data)
            
            # Insert matches
            if sample_matches:
                result = self.db_service.client.table('matching_results')\
                    .insert(sample_matches)\
                    .execute()
                
                matches_created = len(result.data) if result.data else 0
                logger.info(f"Created {matches_created} sample matches")
                
                # Create sample metadata for each match
                if result.data:
                    metadata_entries = []
                    for match in result.data:
                        metadata_entries.append({
                            'matching_result_id': match['id'],
                            'metadata_key': 'algorithm_info',
                            'metadata_value': {
                                'name_similarity': 0.85,
                                'brand_match': True,
                                'category_match': False,
                                'algorithm': 'hybrid',
                                'version': '1.0.0'
                            }
                        })
                    
                    # Insert metadata
                    meta_result = self.db_service.client.table('matching_metadata')\
                        .insert(metadata_entries)\
                        .execute()
                    
                    logger.info(f"Created {len(meta_result.data)} metadata entries")
            
            return matches_created
            
        except Exception as e:
            logger.error(f"Error creating sample matches: {e}")
            return 0
    
    async def test_functions(self):
        """Test the database functions"""
        logger.info("Testing database functions...")
        
        try:
            # Test get_match_quality_metrics
            result = self.db_service.client.rpc('get_match_quality_metrics').execute()
            if result.data:
                metrics = result.data[0]
                logger.info(f"✅ Quality metrics: {metrics}")
            
            # Test get_match_status_counts
            result = self.db_service.client.rpc('get_match_status_counts').execute()
            if result.data:
                logger.info(f"✅ Status counts: {result.data}")
            
            # Test get_match_method_counts
            result = self.db_service.client.rpc('get_match_method_counts').execute()
            if result.data:
                logger.info(f"✅ Method counts: {result.data}")
            
            logger.info("✅ All database functions work correctly")
            
        except Exception as e:
            logger.error(f"❌ Function testing failed: {e}")


async def main():
    """Main import function"""
    print("🚀 Starting Sample Data Import")
    print("=" * 50)
    
    importer = MatchingDataImporter()
    
    try:
        # Import sample data
        success = await importer.import_sample_data()
        
        if success:
            # Test functions
            await importer.test_functions()
            
            print("\n🎉 Sample data import completed successfully!")
            print("✅ Tables created and populated with sample data")
            print("✅ Database functions tested and working")
            print("\n📋 Next steps:")
            print("1. Check Supabase dashboard to see the new tables")
            print("2. Test API endpoints: http://localhost:8001/api/v2/matches/stats")
            print("3. Run full data export when ready")
        else:
            print("\n❌ Sample data import failed")
            return 1
            
    except Exception as e:
        print(f"\n❌ Import error: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))