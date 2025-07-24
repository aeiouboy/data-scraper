#!/usr/bin/env python3
"""
Test improved price and brand extraction on problematic products
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
        logging.FileHandler('test_improved_extraction.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class ImprovedExtractionTester:
    """Test improved extraction methods on problematic products"""
    
    def __init__(self):
        self.supabase = SupabaseService()
        self.improved_strategy = ImprovedNativeStrategy()
    
    async def test_hp_price_extraction(self) -> Dict[str, Any]:
        """Test improved price extraction on HP products with missing prices"""
        logger.info("Testing improved HP price extraction...")
        
        # Get HP products with missing prices
        result = self.supabase.client.table('products')\
            .select('id, sku, name, brand, category, url, current_price')\
            .eq('retailer_code', 'HP')\
            .is_('current_price', 'null')\
            .limit(10)\
            .execute()
        
        test_products = result.data
        logger.info(f"Testing {len(test_products)} HP products with missing prices")
        
        results = {
            'total_tested': len(test_products),
            'successful_extractions': 0,
            'failed_extractions': 0,
            'test_results': []
        }
        
        for product in test_products:
            try:
                logger.info(f"Testing product: {product['sku']} - {product['name']}")
                
                # Fetch the product page
                response = requests.get(product['url'], timeout=30)
                if response.status_code == 200:
                    soup = BeautifulSoup(response.content, 'html.parser')
                    
                    # Test improved price extraction
                    price_result = self.improved_strategy.extract_improved_price(soup, product['url'])
                    brand_result = self.improved_strategy.extract_improved_brand(soup, product['url'])
                    category_result = self.improved_strategy.extract_improved_category(soup, product['url'])
                    
                    test_result = {
                        'product_id': product['id'],
                        'sku': product['sku'],
                        'name': product['name'],
                        'url': product['url'],
                        'original_price': product['current_price'],
                        'original_brand': product['brand'],
                        'original_category': product['category'],
                        'extracted_price': price_result.get('current_price'),
                        'extracted_original_price': price_result.get('original_price'),
                        'extracted_brand': brand_result,
                        'extracted_category': category_result,
                        'success': bool(price_result.get('current_price'))
                    }
                    
                    results['test_results'].append(test_result)
                    
                    if price_result.get('current_price'):
                        results['successful_extractions'] += 1
                        logger.info(f"✅ Successfully extracted price: {price_result.get('current_price')}")
                    else:
                        results['failed_extractions'] += 1
                        logger.warning(f"❌ Failed to extract price for {product['sku']}")
                
                else:
                    logger.error(f"Failed to fetch {product['url']}: {response.status_code}")
                    results['failed_extractions'] += 1
                    
            except Exception as e:
                logger.error(f"Error testing product {product['sku']}: {str(e)}")
                results['failed_extractions'] += 1
        
        logger.info(f"Price extraction test complete: {results['successful_extractions']}/{results['total_tested']} successful")
        return results
    
    async def test_brand_extraction(self) -> Dict[str, Any]:
        """Test improved brand extraction on products with missing brands"""
        logger.info("Testing improved brand extraction...")
        
        # Get products with missing brands
        result = self.supabase.client.table('products')\
            .select('id, sku, name, brand, category, url, retailer_code')\
            .is_('brand', 'null')\
            .limit(10)\
            .execute()
        
        test_products = result.data
        logger.info(f"Testing {len(test_products)} products with missing brands")
        
        results = {
            'total_tested': len(test_products),
            'successful_extractions': 0,
            'failed_extractions': 0,
            'test_results': []
        }
        
        for product in test_products:
            try:
                logger.info(f"Testing product: {product['sku']} - {product['name']}")
                
                # Fetch the product page
                response = requests.get(product['url'], timeout=30)
                if response.status_code == 200:
                    soup = BeautifulSoup(response.content, 'html.parser')
                    
                    # Test improved brand extraction
                    brand_result = self.improved_strategy.extract_improved_brand(soup, product['url'])
                    
                    test_result = {
                        'product_id': product['id'],
                        'sku': product['sku'],
                        'name': product['name'],
                        'url': product['url'],
                        'retailer_code': product['retailer_code'],
                        'original_brand': product['brand'],
                        'extracted_brand': brand_result,
                        'success': bool(brand_result)
                    }
                    
                    results['test_results'].append(test_result)
                    
                    if brand_result:
                        results['successful_extractions'] += 1
                        logger.info(f"✅ Successfully extracted brand: {brand_result}")
                    else:
                        results['failed_extractions'] += 1
                        logger.warning(f"❌ Failed to extract brand for {product['sku']}")
                
                else:
                    logger.error(f"Failed to fetch {product['url']}: {response.status_code}")
                    results['failed_extractions'] += 1
                    
            except Exception as e:
                logger.error(f"Error testing product {product['sku']}: {str(e)}")
                results['failed_extractions'] += 1
        
        logger.info(f"Brand extraction test complete: {results['successful_extractions']}/{results['total_tested']} successful")
        return results
    
    async def apply_improvements_to_products(self, product_ids: List[str]) -> Dict[str, Any]:
        """Apply improved extraction to specific products and update database"""
        logger.info(f"Applying improvements to {len(product_ids)} products...")
        
        results = {
            'total_processed': len(product_ids),
            'successful_updates': 0,
            'failed_updates': 0,
            'updates': []
        }
        
        for product_id in product_ids:
            try:
                # Get product from database
                product_result = self.supabase.client.table('products')\
                    .select('*')\
                    .eq('id', product_id)\
                    .single()\
                    .execute()
                
                if not product_result.data:
                    logger.error(f"Product {product_id} not found")
                    results['failed_updates'] += 1
                    continue
                
                product = product_result.data
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
                
                # Update price if found and currently missing
                if price_result.get('current_price') and not product.get('current_price'):
                    updates['current_price'] = price_result['current_price']
                    improvements.append('price')
                
                if price_result.get('original_price') and not product.get('original_price'):
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
                        .eq('id', product_id)\
                        .execute()
                    
                    if update_result.data:
                        results['successful_updates'] += 1
                        logger.info(f"✅ Updated product {product['sku']} - improvements: {improvements}")
                        
                        results['updates'].append({
                            'product_id': product_id,
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
                logger.error(f"Error processing product {product_id}: {str(e)}")
                results['failed_updates'] += 1
        
        logger.info(f"Improvement application complete: {results['successful_updates']}/{results['total_processed']} successful")
        return results

async def main():
    """Main function to run the tests"""
    tester = ImprovedExtractionTester()
    
    print("🔧 IMPROVED EXTRACTION TESTING")
    print("=" * 50)
    
    # Test HP price extraction
    print("\n💰 Testing HP price extraction improvements...")
    price_results = await tester.test_hp_price_extraction()
    
    # Save price test results
    with open('hp_price_extraction_test_results.json', 'w') as f:
        json.dump(price_results, f, indent=2)
    
    print(f"Price extraction test results:")
    print(f"  ✅ Successful: {price_results['successful_extractions']}/{price_results['total_tested']}")
    print(f"  ❌ Failed: {price_results['failed_extractions']}/{price_results['total_tested']}")
    
    # Test brand extraction
    print("\n🏷️ Testing brand extraction improvements...")
    brand_results = await tester.test_brand_extraction()
    
    # Save brand test results
    with open('brand_extraction_test_results.json', 'w') as f:
        json.dump(brand_results, f, indent=2)
    
    print(f"Brand extraction test results:")
    print(f"  ✅ Successful: {brand_results['successful_extractions']}/{brand_results['total_tested']}")
    print(f"  ❌ Failed: {brand_results['failed_extractions']}/{brand_results['total_tested']}")
    
    # Ask if user wants to apply improvements to successful test products
    successful_price_products = [
        result['product_id'] for result in price_results['test_results'] 
        if result['success']
    ]
    
    successful_brand_products = [
        result['product_id'] for result in brand_results['test_results'] 
        if result['success']
    ]
    
    all_successful = list(set(successful_price_products + successful_brand_products))
    
    if all_successful:
        print(f"\n🚀 Found {len(all_successful)} products that can be improved")
        response = input("Apply improvements to these products? (y/n): ")
        
        if response.lower() == 'y':
            print("\nApplying improvements...")
            update_results = await tester.apply_improvements_to_products(all_successful)
            
            # Save update results
            with open('improvement_application_results.json', 'w') as f:
                json.dump(update_results, f, indent=2)
            
            print(f"Improvement application results:")
            print(f"  ✅ Successful updates: {update_results['successful_updates']}/{update_results['total_processed']}")
            print(f"  ❌ Failed updates: {update_results['failed_updates']}/{update_results['total_processed']}")
            
            # Show summary of improvements
            if update_results['updates']:
                print(f"\n📊 Summary of improvements:")
                improvement_counts = {}
                for update in update_results['updates']:
                    for improvement in update['improvements']:
                        improvement_counts[improvement] = improvement_counts.get(improvement, 0) + 1
                
                for improvement, count in improvement_counts.items():
                    print(f"  - {improvement}: {count} products")
    else:
        print("\n❌ No products found that can be improved with current test")
    
    print(f"\n📁 Files created:")
    print(f"  - hp_price_extraction_test_results.json")
    print(f"  - brand_extraction_test_results.json")
    if all_successful:
        print(f"  - improvement_application_results.json")

if __name__ == "__main__":
    asyncio.run(main())