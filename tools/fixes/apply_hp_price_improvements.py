#!/usr/bin/env python3
"""
Apply improved price extraction to HP products with missing prices
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
        logging.FileHandler('apply_hp_price_improvements.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class HPPriceImprover:
    """Apply improved price extraction to HP products with missing prices"""
    
    def __init__(self):
        self.supabase = SupabaseService()
        self.improved_strategy = ImprovedNativeStrategy()
    
    async def apply_improvements_to_hp_products(self, limit: int = 50) -> Dict[str, Any]:
        """Apply improved extraction to HP products with missing prices"""
        logger.info(f"Applying improved price extraction to HP products (limit: {limit})...")
        
        # Get HP products with missing prices
        result = self.supabase.client.table('products')\
            .select('id, sku, name, brand, category, url, current_price, original_price')\
            .eq('retailer_code', 'HP')\
            .is_('current_price', 'null')\
            .limit(limit)\
            .execute()
        
        hp_products = result.data
        logger.info(f"Found {len(hp_products)} HP products with missing prices")
        
        results = {
            'total_processed': len(hp_products),
            'successful_updates': 0,
            'failed_updates': 0,
            'updates': []
        }
        
        for product in hp_products:
            try:
                logger.info(f"Processing product: {product['sku']} - {product['name']}")
                
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
                
                # Update price if found
                if price_result.get('current_price'):
                    updates['current_price'] = price_result['current_price']
                    improvements.append('price')
                
                if price_result.get('original_price'):
                    updates['original_price'] = price_result['original_price']
                
                if price_result.get('discount_percentage'):
                    updates['discount_percentage'] = price_result['discount_percentage']
                
                # Update brand if found and currently missing
                if brand_result and not product.get('brand'):
                    updates['brand'] = brand_result
                    improvements.append('brand')
                
                # Update category if found and currently generic/missing
                if category_result and (not product.get('category') or product.get('category') == 'Other'):
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
                            'product_id': product['id'],
                            'sku': product['sku'],
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
                logger.error(f"Error processing product {product['sku']}: {str(e)}")
                results['failed_updates'] += 1
        
        logger.info(f"Improvement application complete: {results['successful_updates']}/{results['total_processed']} successful")
        return results

async def main():
    """Main function to run the HP price improvements"""
    improver = HPPriceImprover()
    
    print("🔧 HP PRICE EXTRACTION IMPROVEMENTS")
    print("=" * 50)
    
    # Apply improvements to HP products with missing prices
    print("\n💰 Applying improved price extraction to HP products...")
    results = await improver.apply_improvements_to_hp_products(limit=50)
    
    # Save results
    with open('hp_price_improvements_results.json', 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\n📊 Results:")
    print(f"  Total processed: {results['total_processed']}")
    print(f"  ✅ Successful updates: {results['successful_updates']}")
    print(f"  ❌ Failed updates: {results['failed_updates']}")
    print(f"  📈 Success rate: {results['successful_updates']/results['total_processed']*100:.1f}%")
    
    # Show summary of improvements
    if results['updates']:
        print(f"\n📊 Summary of improvements:")
        improvement_counts = {}
        for update in results['updates']:
            for improvement in update['improvements']:
                improvement_counts[improvement] = improvement_counts.get(improvement, 0) + 1
        
        for improvement, count in improvement_counts.items():
            print(f"  - {improvement}: {count} products")
    
    print(f"\n📁 Files created:")
    print(f"  - hp_price_improvements_results.json")
    print(f"  - apply_hp_price_improvements.log")

if __name__ == "__main__":
    asyncio.run(main())