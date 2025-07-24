#!/usr/bin/env python3
"""
Optimized version of import with performance improvements
"""
import asyncio
import json
from pathlib import Path
from typing import List, Dict, Any
import sys
from datetime import datetime

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.append(str(project_root))

from src.services.supabase_service import SupabaseService
from src.models.product import Product
from decimal import Decimal
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class OptimizedImporter:
    """Optimized importer with batch operations"""
    
    def __init__(self):
        self.supabase = SupabaseService()
    
    async def batch_upsert_optimized(self, products: List[Product], batch_size: int = 100) -> Dict[str, int]:
        """Optimized batch upsert without double queries"""
        
        total_products = len(products)
        imported = 0
        updated = 0
        failed = 0
        
        logger.info(f"Starting optimized import of {total_products} products")
        
        for i in range(0, total_products, batch_size):
            batch = products[i:i + batch_size]
            batch_num = (i // batch_size) + 1
            total_batches = (total_products + batch_size - 1) // batch_size
            
            logger.info(f"Processing batch {batch_num}/{total_batches} ({len(batch)} products)")
            
            batch_imported = 0
            batch_updated = 0
            batch_failed = 0
            
            # Get all SKUs in batch to check existence in one query
            skus = [p.sku for p in batch]
            
            try:
                # Single query to check which products exist
                existing_response = self.supabase.client.table('products')\
                    .select('sku')\
                    .in_('sku', skus)\
                    .execute()
                
                existing_skus = {item['sku'] for item in existing_response.data}
                logger.info(f"Found {len(existing_skus)} existing products in batch")
                
                # Prepare batch data for upsert
                batch_data = []
                for product in batch:
                    try:
                        product_data = product.to_supabase_dict()
                        batch_data.append(product_data)
                        
                        if product.sku in existing_skus:
                            batch_updated += 1
                        else:
                            batch_imported += 1
                            
                    except Exception as e:
                        logger.error(f"Error preparing product {product.sku}: {e}")
                        batch_failed += 1
                
                # Single batch upsert operation
                if batch_data:
                    result = self.supabase.client.table('products').upsert(
                        batch_data,
                        on_conflict='retailer_code,sku'
                    ).execute()
                    
                    logger.info(f"Batch upsert completed: {len(result.data)} products processed")
                
            except Exception as e:
                logger.error(f"Batch {batch_num} failed: {e}")
                batch_failed = len(batch)
            
            imported += batch_imported
            updated += batch_updated
            failed += batch_failed
            
            logger.info(f"Batch {batch_num} completed: {batch_imported} imported, {batch_updated} updated, {batch_failed} failed")
            
            # Minimal delay
            await asyncio.sleep(0.1)
        
        return {
            'imported': imported,
            'updated': updated, 
            'failed': failed,
            'total': total_products
        }

async def main():
    """Compare performance of optimized vs original import"""
    
    # Load a small sample for testing
    data_file = Path("data/processed_import_data.json")
    
    if not data_file.exists():
        print("❌ Processed data file not found")
        return
    
    with open(data_file, 'r') as f:
        all_data = json.load(f)
    
    # Test with first 100 products
    test_data = all_data[:100]
    
    print(f"🚀 Testing optimized import with {len(test_data)} products")
    
    # Convert to Product objects
    products = []
    for item in test_data:
        try:
            product = Product(
                sku=item['sku'],
                retailer_code=item['retailer_code'],
                name=item['name'],
                brand=item.get('brand'),
                category=item.get('category'),
                current_price=Decimal(str(item['current_price'])) if item.get('current_price') else None,
                original_price=Decimal(str(item['original_price'])) if item.get('original_price') else None,
                discount_percentage=item.get('discount_percentage'),
                availability=item.get('availability', 'unknown'),
                url=item.get('url'),
                image_url=item.get('image_url'),
                description=item.get('description'),
                specifications=item.get('specifications'),
                features=item.get('features'),
                usage_instructions=item.get('usage_instructions'),
                monitoring_tier=item.get('monitoring_tier', 'standard'),
                matching_hash=item.get('matching_hash'),
                scraped_at=datetime.fromisoformat(item['scraped_at'].replace('Z', '+00:00'))
            )
            products.append(product)
        except Exception as e:
            print(f"Error converting product: {e}")
    
    # Time the optimized import
    start_time = datetime.now()
    
    importer = OptimizedImporter()
    results = await importer.batch_upsert_optimized(products, batch_size=50)
    
    end_time = datetime.now()
    duration = end_time - start_time
    
    print(f"\n📊 Optimized Import Results:")
    print(f"  Duration: {duration}")
    print(f"  Products: {results['total']}")
    print(f"  Rate: {results['total'] / duration.total_seconds():.2f} products/second")
    print(f"  Imported: {results['imported']}")
    print(f"  Updated: {results['updated']}")
    print(f"  Failed: {results['failed']}")
    
    # Calculate speed improvement
    original_rate = 1.8  # products per second from current import
    optimized_rate = results['total'] / duration.total_seconds()
    improvement = optimized_rate / original_rate
    
    print(f"\n⚡ Performance Improvement:")
    print(f"  Original rate: {original_rate:.2f} products/second")
    print(f"  Optimized rate: {optimized_rate:.2f} products/second") 
    print(f"  Speed improvement: {improvement:.1f}x faster")

if __name__ == "__main__":
    asyncio.run(main())