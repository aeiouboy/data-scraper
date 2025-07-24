#!/usr/bin/env python3
"""
Import manually scraped data from Excel files into Supabase database
"""
import json
import asyncio
import logging
from datetime import datetime
from typing import List, Dict, Any
from pathlib import Path
import sys

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.append(str(project_root))

from src.services.supabase_service import SupabaseService
from src.models.product import Product
from decimal import Decimal

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class ManualDataImporter:
    """Import manually scraped data into database"""
    
    def __init__(self):
        self.supabase = SupabaseService()
        self.processed_data_file = project_root / "data" / "processed_import_data.json"
        
    async def load_processed_data(self) -> List[Dict[str, Any]]:
        """Load the processed data from JSON file"""
        try:
            if not self.processed_data_file.exists():
                logger.error(f"Processed data file not found: {self.processed_data_file}")
                return []
            
            with open(self.processed_data_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            logger.info(f"Loaded {len(data)} products from processed data file")
            return data
            
        except Exception as e:
            logger.error(f"Error loading processed data: {str(e)}")
            return []
    
    def convert_to_product_model(self, product_data: Dict[str, Any]) -> Product:
        """Convert processed data to Product model"""
        try:
            # Convert price strings to Decimal if needed
            current_price = None
            original_price = None
            
            if product_data.get('current_price') is not None:
                current_price = Decimal(str(product_data['current_price']))
            
            if product_data.get('original_price') is not None:
                original_price = Decimal(str(product_data['original_price']))
            
            # Create Product instance
            product = Product(
                sku=product_data['sku'],
                retailer_code=product_data['retailer_code'],
                name=product_data['name'],
                brand=product_data.get('brand'),
                category=product_data.get('category'),
                current_price=current_price,
                original_price=original_price,
                discount_percentage=product_data.get('discount_percentage'),
                availability=product_data.get('availability', 'unknown'),
                url=product_data.get('url'),
                image_url=product_data.get('image_url'),
                description=product_data.get('description'),
                specifications=product_data.get('specifications'),
                features=product_data.get('features'),
                usage_instructions=product_data.get('usage_instructions'),
                monitoring_tier=product_data.get('monitoring_tier', 'standard'),
                matching_hash=product_data.get('matching_hash'),
                scraped_at=datetime.fromisoformat(product_data['scraped_at'].replace('Z', '+00:00'))
            )
            
            return product
            
        except Exception as e:
            logger.error(f"Error converting product data: {str(e)}")
            logger.error(f"Product data: {product_data}")
            raise
    
    async def backup_existing_data(self) -> bool:
        """Create backup of existing products before import"""
        try:
            logger.info("Creating backup of existing products...")
            
            # Get all existing products
            all_products = await self.supabase.search_products(limit=10000)
            total_products = all_products['total']
            
            if total_products == 0:
                logger.info("No existing products found, skipping backup")
                return True
            
            # Create backup file
            backup_file = project_root / f"backup_products_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            
            products_backup = []
            page = 1
            page_size = 1000
            
            while len(products_backup) < total_products:
                batch = await self.supabase.search_products(
                    page=page,
                    limit=page_size
                )
                products_backup.extend(batch['products'])
                page += 1
                
                if len(batch['products']) < page_size:
                    break
            
            # Save backup
            with open(backup_file, 'w', encoding='utf-8') as f:
                json.dump(products_backup, f, indent=2, default=str)
            
            logger.info(f"Backup created: {backup_file} ({len(products_backup)} products)")
            return True
            
        except Exception as e:
            logger.error(f"Error creating backup: {str(e)}")
            return False
    
    async def check_existing_skus(self, products: List[Dict[str, Any]]) -> Dict[str, str]:
        """Check which SKUs already exist in database"""
        try:
            logger.info("Checking for existing SKUs...")
            
            skus = [p['sku'] for p in products]
            retailer_codes = list(set(p['retailer_code'] for p in products))
            
            existing_skus = {}
            
            for retailer_code in retailer_codes:
                retailer_skus = [p['sku'] for p in products if p['retailer_code'] == retailer_code]
                
                # Batch check existing SKUs for this retailer
                existing_products = await self.supabase.get_products_by_skus_batch(
                    skus=retailer_skus,
                    retailer_code=retailer_code
                )
                
                for sku, product in existing_products.items():
                    existing_skus[f"{retailer_code}_{sku}"] = product['id']
            
            logger.info(f"Found {len(existing_skus)} existing SKUs")
            return existing_skus
            
        except Exception as e:
            logger.error(f"Error checking existing SKUs: {str(e)}")
            return {}
    
    async def import_products_batch(
        self, 
        products: List[Product], 
        batch_size: int = 100
    ) -> Dict[str, int]:
        """Import products in batches"""
        
        total_products = len(products)
        imported = 0
        updated = 0
        failed = 0
        
        logger.info(f"Starting import of {total_products} products in batches of {batch_size}")
        
        for i in range(0, total_products, batch_size):
            batch = products[i:i + batch_size]
            batch_num = (i // batch_size) + 1
            total_batches = (total_products + batch_size - 1) // batch_size
            
            logger.info(f"Processing batch {batch_num}/{total_batches} ({len(batch)} products)")
            
            batch_imported = 0
            batch_updated = 0
            batch_failed = 0
            
            for product in batch:
                try:
                    # Check if product exists
                    existing = await self.supabase.get_product_by_sku(product.sku)
                    
                    # Upsert product
                    result = await self.supabase.upsert_product(product)
                    
                    if result:
                        if existing:
                            batch_updated += 1
                        else:
                            batch_imported += 1
                    else:
                        batch_failed += 1
                        logger.warning(f"Failed to import product: {product.sku}")
                
                except Exception as e:
                    batch_failed += 1
                    logger.error(f"Error importing product {product.sku}: {str(e)}")
            
            imported += batch_imported
            updated += batch_updated
            failed += batch_failed
            
            logger.info(f"Batch {batch_num} completed: {batch_imported} imported, {batch_updated} updated, {batch_failed} failed")
            
            # Small delay between batches to avoid overwhelming the database
            await asyncio.sleep(0.5)
        
        return {
            'imported': imported,
            'updated': updated,
            'failed': failed,
            'total': total_products
        }
    
    async def validate_import(self, original_count: int) -> bool:
        """Validate the import by checking database counts"""
        try:
            logger.info("Validating import...")
            
            # Get current product count
            current_stats = await self.supabase.search_products(limit=1)
            current_count = current_stats['total']
            
            logger.info(f"Products in database after import: {current_count}")
            logger.info(f"Expected minimum increase: {original_count}")
            
            # Check that we have products for both retailers
            hp_stats = await self.supabase.search_products(
                filters={'retailer_code': 'HP'},
                limit=1
            )
            twd_stats = await self.supabase.search_products(
                filters={'retailer_code': 'TWD'},
                limit=1
            )
            
            logger.info(f"HomePro products: {hp_stats['total']}")
            logger.info(f"Thai Watsadu products: {twd_stats['total']}")
            
            return hp_stats['total'] > 0 and twd_stats['total'] > 0
            
        except Exception as e:
            logger.error(f"Error validating import: {str(e)}")
            return False
    
    async def run_import(self, create_backup: bool = True) -> bool:
        """Run the complete import process"""
        try:
            start_time = datetime.now()
            logger.info("=" * 60)
            logger.info("STARTING MANUAL DATA IMPORT")
            logger.info("=" * 60)
            
            # 1. Load processed data
            logger.info("Step 1: Loading processed data...")
            products_data = await self.load_processed_data()
            
            if not products_data:
                logger.error("No data to import")
                return False
            
            logger.info(f"Loaded {len(products_data)} products")
            
            # 2. Create backup if requested
            if create_backup:
                logger.info("Step 2: Creating backup...")
                backup_success = await self.backup_existing_data()
                if not backup_success:
                    logger.warning("Backup failed, but continuing with import...")
            else:
                logger.info("Step 2: Skipping backup (not requested)")
            
            # 3. Convert to Product models
            logger.info("Step 3: Converting to Product models...")
            products = []
            conversion_failures = 0
            
            for i, product_data in enumerate(products_data):
                try:
                    product = self.convert_to_product_model(product_data)
                    products.append(product)
                except Exception as e:
                    conversion_failures += 1
                    logger.error(f"Failed to convert product {i}: {str(e)}")
            
            logger.info(f"Converted {len(products)} products ({conversion_failures} failures)")
            
            if not products:
                logger.error("No valid products to import")
                return False
            
            # 4. Import products
            logger.info("Step 4: Importing products...")
            import_results = await self.import_products_batch(products, batch_size=50)
            
            # 5. Validate import
            logger.info("Step 5: Validating import...")
            validation_success = await self.validate_import(len(products_data))
            
            # 6. Report results
            end_time = datetime.now()
            duration = end_time - start_time
            
            logger.info("=" * 60)
            logger.info("IMPORT COMPLETED")
            logger.info("=" * 60)
            logger.info(f"Duration: {duration}")
            logger.info(f"Products imported: {import_results['imported']}")
            logger.info(f"Products updated: {import_results['updated']}")
            logger.info(f"Products failed: {import_results['failed']}")
            logger.info(f"Total processed: {import_results['total']}")
            logger.info(f"Success rate: {((import_results['imported'] + import_results['updated']) / import_results['total'] * 100):.1f}%")
            logger.info(f"Validation: {'PASSED' if validation_success else 'FAILED'}")
            
            return validation_success and import_results['failed'] == 0
            
        except Exception as e:
            logger.error(f"Import process failed: {str(e)}")
            return False

async def main():
    """Main function to run the import"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Import manually scraped data to database')
    parser.add_argument('--no-backup', action='store_true', help='Skip creating backup')
    parser.add_argument('--dry-run', action='store_true', help='Validate data without importing')
    
    args = parser.parse_args()
    
    importer = ManualDataImporter()
    
    if args.dry_run:
        logger.info("DRY RUN MODE - Validating data only")
        products_data = await importer.load_processed_data()
        
        if products_data:
            logger.info(f"Found {len(products_data)} products ready for import")
            
            # Test conversion of first few products
            test_count = min(5, len(products_data))
            logger.info(f"Testing conversion of {test_count} products...")
            
            for i in range(test_count):
                try:
                    product = importer.convert_to_product_model(products_data[i])
                    logger.info(f"✓ Product {i+1}: {product.sku} - {product.name[:50]}...")
                except Exception as e:
                    logger.error(f"✗ Product {i+1} conversion failed: {str(e)}")
            
            logger.info("Dry run completed")
        else:
            logger.error("No data found for import")
    else:
        # Run actual import
        success = await importer.run_import(create_backup=not args.no_backup)
        
        if success:
            logger.info("🎉 Import completed successfully!")
        else:
            logger.error("❌ Import failed!")
        
        return 0 if success else 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)