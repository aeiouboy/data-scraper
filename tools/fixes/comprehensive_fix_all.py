#!/usr/bin/env python3
"""
Comprehensive fix for all remaining data quality issues
"""

import asyncio
import logging
from typing import List, Dict, Any
import json
import requests
from bs4 import BeautifulSoup
from src.scrapers.strategies.improved_native_strategy import ImprovedNativeStrategy
from src.services.supabase_service import SupabaseService
from concurrent.futures import ThreadPoolExecutor
import time

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('comprehensive_fix_all.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class ComprehensiveFixer:
    """Fix all remaining data quality issues"""
    
    def __init__(self):
        self.supabase = SupabaseService()
        self.improved_strategy = ImprovedNativeStrategy()
        self.stats = {
            'total_processed': 0,
            'successful_updates': 0,
            'failed_updates': 0,
            'price_fixes': 0,
            'brand_fixes': 0,
            'category_fixes': 0
        }
    
    def get_all_problematic_products(self) -> Dict[str, List[Dict[str, Any]]]:
        """Get all products with missing critical data"""
        logger.info("Identifying all problematic products...")
        
        problems = {
            'missing_prices': [],
            'missing_brands': [],
            'generic_categories': []
        }
        
        # Get HP products with missing prices
        result = self.supabase.client.table('products')\
            .select('id, sku, name, brand, category, url, current_price, original_price, retailer_code')\
            .eq('retailer_code', 'HP')\
            .is_('current_price', 'null')\
            .execute()
        problems['missing_prices'].extend(result.data)
        
        # Get TWD products with missing prices
        result = self.supabase.client.table('products')\
            .select('id, sku, name, brand, category, url, current_price, original_price, retailer_code')\
            .eq('retailer_code', 'TWD')\
            .is_('current_price', 'null')\
            .execute()
        problems['missing_prices'].extend(result.data)
        
        # Get products with missing brands
        result = self.supabase.client.table('products')\
            .select('id, sku, name, brand, category, url, current_price, original_price, retailer_code')\
            .is_('brand', 'null')\
            .execute()
        problems['missing_brands'].extend(result.data)
        
        # Get products with generic categories
        result = self.supabase.client.table('products')\
            .select('id, sku, name, brand, category, url, current_price, original_price, retailer_code')\
            .in_('category', ['Other', 'General'])\
            .execute()
        problems['generic_categories'].extend(result.data)
        
        logger.info(f"Found {len(problems['missing_prices'])} products with missing prices")
        logger.info(f"Found {len(problems['missing_brands'])} products with missing brands")
        logger.info(f"Found {len(problems['generic_categories'])} products with generic categories")
        
        return problems
    
    def fix_single_product(self, product: Dict[str, Any]) -> Dict[str, Any]:
        """Fix a single product with improved extraction"""
        try:
            logger.info(f"Processing product: {product['sku']}")
            
            # Fetch the product page
            response = requests.get(product['url'], timeout=30)
            if response.status_code != 200:
                logger.error(f"Failed to fetch {product['url']}: {response.status_code}")
                return {'success': False, 'error': f"HTTP {response.status_code}"}
            
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
                self.stats['price_fixes'] += 1
            
            if price_result.get('original_price') and not product.get('original_price'):
                updates['original_price'] = price_result['original_price']
            
            if price_result.get('discount_percentage'):
                updates['discount_percentage'] = price_result['discount_percentage']
            
            # Update brand if found and currently missing
            if brand_result and not product.get('brand'):
                updates['brand'] = brand_result
                improvements.append('brand')
                self.stats['brand_fixes'] += 1
            
            # Update category if found and currently generic/missing
            if category_result and (not product.get('category') or product.get('category') in ['Other', 'General']):
                updates['category'] = category_result
                improvements.append('category')
                self.stats['category_fixes'] += 1
            
            # Apply updates if any
            if updates:
                update_result = self.supabase.client.table('products')\
                    .update(updates)\
                    .eq('id', product['id'])\
                    .execute()
                
                if update_result.data:
                    self.stats['successful_updates'] += 1
                    logger.info(f"✅ Updated product {product['sku']} - improvements: {improvements}")
                    return {
                        'success': True,
                        'sku': product['sku'],
                        'improvements': improvements,
                        'updates': updates
                    }
                else:
                    self.stats['failed_updates'] += 1
                    return {'success': False, 'error': 'Database update failed'}
            else:
                logger.info(f"No improvements found for product {product['sku']}")
                return {'success': False, 'error': 'No improvements found'}
                
        except Exception as e:
            logger.error(f"Error processing product {product['sku']}: {str(e)}")
            self.stats['failed_updates'] += 1
            return {'success': False, 'error': str(e)}
    
    def fix_products_batch(self, products: List[Dict[str, Any]], batch_size: int = 20) -> List[Dict[str, Any]]:
        """Fix products in batches with threading"""
        results = []
        
        for i in range(0, len(products), batch_size):
            batch = products[i:i+batch_size]
            logger.info(f"Processing batch {i//batch_size + 1}/{(len(products) + batch_size - 1)//batch_size}")
            
            with ThreadPoolExecutor(max_workers=5) as executor:
                batch_results = list(executor.map(self.fix_single_product, batch))
                results.extend(batch_results)
            
            # Add delay between batches to be respectful
            if i + batch_size < len(products):
                time.sleep(2)
        
        return results
    
    def run_comprehensive_fix(self) -> Dict[str, Any]:
        """Run comprehensive fix for all issues"""
        logger.info("Starting comprehensive data quality fix...")
        
        # Get all problematic products
        problems = self.get_all_problematic_products()
        
        # Combine all unique products that need fixing
        all_products = {}
        
        for product in problems['missing_prices']:
            all_products[product['id']] = product
        
        for product in problems['missing_brands']:
            all_products[product['id']] = product
        
        for product in problems['generic_categories']:
            all_products[product['id']] = product
        
        unique_products = list(all_products.values())
        logger.info(f"Total unique products to fix: {len(unique_products)}")
        
        # Fix all products
        results = self.fix_products_batch(unique_products)
        
        # Calculate success metrics
        successful_results = [r for r in results if r.get('success')]
        
        final_results = {
            'total_products': len(unique_products),
            'successful_updates': len(successful_results),
            'failed_updates': len(results) - len(successful_results),
            'price_fixes': self.stats['price_fixes'],
            'brand_fixes': self.stats['brand_fixes'],
            'category_fixes': self.stats['category_fixes'],
            'success_rate': len(successful_results) / len(unique_products) * 100,
            'improvements': successful_results
        }
        
        return final_results

def main():
    """Main function to run comprehensive fix"""
    fixer = ComprehensiveFixer()
    
    print("🔧 COMPREHENSIVE DATA QUALITY FIX")
    print("=" * 50)
    
    # Run comprehensive fix
    print("\n🚀 Running comprehensive fix for all data quality issues...")
    results = fixer.run_comprehensive_fix()
    
    # Save results
    with open('comprehensive_fix_results.json', 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\n📊 COMPREHENSIVE FIX RESULTS:")
    print(f"  Total products processed: {results['total_products']}")
    print(f"  ✅ Successful updates: {results['successful_updates']}")
    print(f"  ❌ Failed updates: {results['failed_updates']}")
    print(f"  📈 Success rate: {results['success_rate']:.1f}%")
    print(f"\n🎯 IMPROVEMENTS BREAKDOWN:")
    print(f"  💰 Price fixes: {results['price_fixes']}")
    print(f"  🏷️ Brand fixes: {results['brand_fixes']}")
    print(f"  📂 Category fixes: {results['category_fixes']}")
    
    print(f"\n📁 Files created:")
    print(f"  - comprehensive_fix_results.json")
    print(f"  - comprehensive_fix_all.log")
    
    print(f"\n✅ Comprehensive fix completed!")

if __name__ == "__main__":
    main()