#!/usr/bin/env python3
"""
Fix specific products shown in the screenshot with missing data
"""

import asyncio
import logging
from typing import List, Dict, Any
import json
import requests
from bs4 import BeautifulSoup
from src.scrapers.strategies.improved_native_strategy import ImprovedNativeStrategy
from src.services.supabase_service import SupabaseService

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('fix_specific_products.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class SpecificProductFixer:
    """Fix specific products with missing data"""
    
    def __init__(self):
        self.supabase = SupabaseService()
        self.improved_strategy = ImprovedNativeStrategy()
    
    async def fix_specific_products(self, skus: List[str]) -> Dict[str, Any]:
        """Fix specific products by SKU"""
        logger.info(f"Fixing {len(skus)} specific products...")
        
        results = {
            'total_processed': len(skus),
            'successful_updates': 0,
            'failed_updates': 0,
            'updates': []
        }
        
        for sku in skus:
            try:
                logger.info(f"Processing product: {sku}")
                
                # Get product from database
                product_result = self.supabase.client.table('products')\
                    .select('*')\
                    .eq('sku', sku)\
                    .single()\
                    .execute()
                
                if not product_result.data:
                    logger.error(f"Product {sku} not found")
                    results['failed_updates'] += 1
                    continue
                
                product = product_result.data
                logger.info(f"Product: {product['name']}")
                
                # Fetch the product page
                response = requests.get(product['url'], timeout=30)
                if response.status_code != 200:
                    logger.error(f"Failed to fetch {product['url']}: {response.status_code}")
                    results['failed_updates'] += 1
                    continue
                
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # Extract improved data
                price_result = self.improved_strategy.extract_improved_price(soup, product['url'])
                brand_result = self.improved_strategy.extract_improved_brand(soup, product['url'])
                category_result = self.improved_strategy.extract_improved_category(soup, product['url'])
                
                # Prepare updates
                updates = {}
                improvements = []
                
                # Update price if found and currently missing
                if price_result.get('current_price') and not product.get('current_price'):
                    updates['current_price'] = price_result['current_price']
                    improvements.append('price')
                
                if price_result.get('original_price') and not product.get('original_price'):
                    updates['original_price'] = price_result['original_price']
                
                if price_result.get('discount_percentage'):
                    updates['discount_percentage'] = price_result['discount_percentage']
                
                # Update brand if found and currently missing or "No Brand"
                if brand_result and (not product.get('brand') or product.get('brand') == 'No Brand'):
                    updates['brand'] = brand_result
                    improvements.append('brand')
                
                # Update category if found and currently generic/missing
                if category_result and (not product.get('category') or product.get('category') in ['Other', 'General']):
                    updates['category'] = category_result
                    improvements.append('category')
                
                # Apply updates if any
                if updates:
                    update_result = self.supabase.client.table('products')\
                        .update(updates)\
                        .eq('id', product['id'])\
                        .execute()
                    
                    if update_result.data:
                        results['successful_updates'] += 1
                        logger.info(f"✅ Updated product {product['sku']} - improvements: {improvements}")
                        logger.info(f"   Price: {price_result.get('current_price', 'N/A')}")
                        logger.info(f"   Brand: {brand_result or 'N/A'}")
                        logger.info(f"   Category: {category_result or 'N/A'}")
                        
                        results['updates'].append({
                            'sku': product['sku'],
                            'name': product['name'],
                            'improvements': improvements,
                            'updates': updates
                        })
                    else:
                        results['failed_updates'] += 1
                        logger.error(f"Failed to update product {product['sku']}")
                else:
                    logger.info(f"No improvements found for product {product['sku']}")
                    results['failed_updates'] += 1
                    
            except Exception as e:
                logger.error(f"Error processing product {sku}: {str(e)}")
                results['failed_updates'] += 1
        
        logger.info(f"Specific product fixes complete: {results['successful_updates']}/{results['total_processed']} successful")
        return results

async def main():
    """Main function to fix specific products"""
    fixer = SpecificProductFixer()
    
    # Products from the screenshot that need fixing
    problematic_skus = [
        'HP-0C668A8B',  # No Brand, General category
        '888109300084',  # No Brand, Other category, No Price
        '888134800449',  # No Price
        '1204072',       # No Brand, General category, No Price
        '1288319'        # Has price but could check for improvements
    ]
    
    print("🔧 FIXING SPECIFIC PROBLEMATIC PRODUCTS")
    print("=" * 50)
    
    # Fix specific products
    print(f"\n🎯 Fixing {len(problematic_skus)} specific products...")
    results = await fixer.fix_specific_products(problematic_skus)
    
    # Save results
    with open('specific_products_fix_results.json', 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\n📊 Results:")
    print(f"  Total processed: {results['total_processed']}")
    print(f"  ✅ Successful updates: {results['successful_updates']}")
    print(f"  ❌ Failed updates: {results['failed_updates']}")
    print(f"  📈 Success rate: {results['successful_updates']/results['total_processed']*100:.1f}%")
    
    # Show detailed results
    if results['updates']:
        print(f"\n📋 Detailed improvements:")
        for update in results['updates']:
            print(f"  • {update['sku']}: {', '.join(update['improvements'])}")
            if 'current_price' in update['updates']:
                print(f"    → Price: {update['updates']['current_price']}")
            if 'brand' in update['updates']:
                print(f"    → Brand: {update['updates']['brand']}")
            if 'category' in update['updates']:
                print(f"    → Category: {update['updates']['category']}")
    
    print(f"\n📁 Files created:")
    print(f"  - specific_products_fix_results.json")
    print(f"  - fix_specific_products.log")

if __name__ == "__main__":
    asyncio.run(main())