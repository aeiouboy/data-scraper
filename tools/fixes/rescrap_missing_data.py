#!/usr/bin/env python3
"""
Rescrap products with missing critical data (brand, category, price)
"""

import asyncio
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
import json
from src.services.supabase_service import SupabaseService
from src.scrapers.base_scraper import BaseScraper
from src.scrapers.homepro_scraper import HomeProScraper
from src.scrapers.thaiwatsadu_scraper import ThaiWatsaduScraper
from src.scrapers.globalhouse_scraper import GlobalHouseScraper
from src.scrapers.dohome_scraper import DoHomeScraper
from src.scrapers.boonthavorn_scraper import BoonthavornScraper
from src.scrapers.megahome_scraper import MegaHomeScraper

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('rescrap_missing_data.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class MissingDataRecraper:
    """Rescrap products with missing critical data"""
    
    def __init__(self):
        self.supabase = SupabaseService()
        self.scrapers = {
            'HP': HomeProScraper(),
            'TWD': ThaiWatsaduScraper(),
            'GH': GlobalHouseScraper(),
            'DH': DoHomeScraper(),
            'BT': BoonthavornScraper(),
            'MH': MegaHomeScraper()
        }
    
    async def get_products_with_missing_data(self, limit: int = 100) -> Dict[str, List[Dict[str, Any]]]:
        """Get products with missing critical data"""
        logger.info(f"Getting products with missing data (limit: {limit})...")
        
        try:
            # Get all products
            result = self.supabase.client.table('products')\
                .select('id, sku, name, brand, category, retailer_code, url, current_price, availability, scraped_at')\
                .limit(limit)\
                .execute()
            
            products = result.data
            
            missing_data_products = {
                'missing_brand': [],
                'missing_category': [],
                'missing_price': [],
                'multiple_issues': []
            }
            
            for product in products:
                issues = []
                
                # Check for missing brand
                if not product.get('brand'):
                    missing_data_products['missing_brand'].append(product)
                    issues.append('brand')
                
                # Check for missing category (or generic 'Other' category)
                if not product.get('category') or product.get('category') == 'Other':
                    missing_data_products['missing_category'].append(product)
                    issues.append('category')
                
                # Check for missing price
                if not product.get('current_price'):
                    missing_data_products['missing_price'].append(product)
                    issues.append('price')
                
                # Track products with multiple issues
                if len(issues) > 1:
                    missing_data_products['multiple_issues'].append({
                        'product': product,
                        'issues': issues
                    })
            
            logger.info(f"Found products with missing data:")
            logger.info(f"  - Missing brand: {len(missing_data_products['missing_brand'])}")
            logger.info(f"  - Missing category: {len(missing_data_products['missing_category'])}")
            logger.info(f"  - Missing price: {len(missing_data_products['missing_price'])}")
            logger.info(f"  - Multiple issues: {len(missing_data_products['multiple_issues'])}")
            
            return missing_data_products
            
        except Exception as e:
            logger.error(f"Error getting products with missing data: {str(e)}")
            return {}
    
    async def rescrap_product(self, product: Dict[str, Any]) -> Dict[str, Any]:
        """Rescrap a single product"""
        try:
            retailer_code = product['retailer_code']
            url = product['url']
            product_id = product['id']
            
            if retailer_code not in self.scrapers:
                logger.warning(f"No scraper available for retailer: {retailer_code}")
                return {
                    'product_id': product_id,
                    'success': False,
                    'error': f"No scraper for retailer {retailer_code}"
                }
            
            scraper = self.scrapers[retailer_code]
            
            # Log what we're trying to rescrap
            logger.info(f"Rescraping product {product_id} from {retailer_code}: {url}")
            
            # Scrape the product using the appropriate method
            scraped_product = None
            if retailer_code == 'HP':
                # HomePro uses scrape_single_product
                scraped_result = await scraper.scrape_single_product(url)
                if scraped_result:
                    # Convert dict result to Product object
                    from src.models.product import Product
                    scraped_product = Product(**scraped_result)
            else:
                # Other scrapers use scrape_product
                scraped_product = await scraper.scrape_product(url)
            
            if scraped_product:
                # Update the product in database
                await self.supabase.upsert_product(scraped_product)
                
                # Check what data was improved
                improvements = []
                if scraped_product.brand and not product.get('brand'):
                    improvements.append('brand')
                if scraped_product.category and (not product.get('category') or product.get('category') == 'Other'):
                    improvements.append('category')
                if scraped_product.current_price and not product.get('current_price'):
                    improvements.append('price')
                
                logger.info(f"Successfully rescraped product {product_id}, improved: {improvements}")
                
                return {
                    'product_id': product_id,
                    'success': True,
                    'improvements': improvements,
                    'scraped_data': {
                        'brand': scraped_product.brand,
                        'category': scraped_product.category,
                        'current_price': float(scraped_product.current_price) if scraped_product.current_price else None
                    }
                }
            else:
                logger.error(f"Failed to scrape product {product_id}")
                return {
                    'product_id': product_id,
                    'success': False,
                    'error': "Failed to scrape product"
                }
                
        except Exception as e:
            logger.error(f"Error rescraping product {product.get('id', 'unknown')}: {str(e)}")
            return {
                'product_id': product.get('id', 'unknown'),
                'success': False,
                'error': str(e)
            }
    
    async def rescrap_products_batch(self, products: List[Dict[str, Any]], batch_size: int = 10) -> Dict[str, Any]:
        """Rescrap products in batches"""
        logger.info(f"Starting to rescrap {len(products)} products in batches of {batch_size}...")
        
        results = {
            'total_attempted': len(products),
            'successful': 0,
            'failed': 0,
            'improvements': {
                'brand': 0,
                'category': 0,
                'price': 0
            },
            'errors': [],
            'details': []
        }
        
        # Process in batches to avoid overwhelming the system
        for i in range(0, len(products), batch_size):
            batch = products[i:i + batch_size]
            logger.info(f"Processing batch {i//batch_size + 1}/{(len(products) + batch_size - 1)//batch_size}")
            
            # Process batch concurrently
            batch_tasks = [self.rescrap_product(product) for product in batch]
            batch_results = await asyncio.gather(*batch_tasks, return_exceptions=True)
            
            # Process results
            for result in batch_results:
                if isinstance(result, Exception):
                    results['failed'] += 1
                    results['errors'].append(str(result))
                elif result['success']:
                    results['successful'] += 1
                    results['details'].append(result)
                    
                    # Track improvements
                    for improvement in result.get('improvements', []):
                        if improvement in results['improvements']:
                            results['improvements'][improvement] += 1
                else:
                    results['failed'] += 1
                    results['errors'].append(result.get('error', 'Unknown error'))
            
            # Add a small delay between batches to be respectful
            await asyncio.sleep(1)
        
        logger.info(f"Rescraping completed.")
        logger.info(f"Success: {results['successful']}, Failed: {results['failed']}")
        logger.info(f"Improvements - Brand: {results['improvements']['brand']}, Category: {results['improvements']['category']}, Price: {results['improvements']['price']}")
        
        return results
    
    async def run_targeted_rescraping(self, target_issues: List[str] = None, limit: int = 100) -> Dict[str, Any]:
        """Run targeted rescraping for specific issues"""
        if target_issues is None:
            target_issues = ['missing_brand', 'missing_category', 'missing_price']
        
        logger.info(f"Starting targeted rescraping for: {target_issues}")
        
        # Get products with missing data
        missing_data_products = await self.get_products_with_missing_data(limit=limit)
        
        if not missing_data_products:
            return {'error': 'Failed to get products with missing data'}
        
        # Collect products to rescrap based on target issues
        products_to_rescrap = []
        seen_product_ids = set()
        
        for issue in target_issues:
            if issue in missing_data_products:
                for product in missing_data_products[issue]:
                    if product['id'] not in seen_product_ids:
                        products_to_rescrap.append(product)
                        seen_product_ids.add(product['id'])
        
        if not products_to_rescrap:
            logger.info("No products found that need rescraping")
            return {
                'message': 'No products found that need rescraping',
                'missing_data_summary': {k: len(v) for k, v in missing_data_products.items() if k != 'multiple_issues'}
            }
        
        # Rescrap the products
        rescrap_results = await self.rescrap_products_batch(products_to_rescrap)
        
        # Get updated statistics
        updated_missing_data = await self.get_products_with_missing_data(limit=limit)
        
        final_results = {
            'initial_missing_data': {k: len(v) for k, v in missing_data_products.items() if k != 'multiple_issues'},
            'rescrap_results': rescrap_results,
            'updated_missing_data': {k: len(v) for k, v in updated_missing_data.items() if k != 'multiple_issues'},
            'completed_at': datetime.now().isoformat()
        }
        
        return final_results

async def main():
    """Main function to run the rescraping"""
    recraper = MissingDataRecraper()
    
    print("🔍 MISSING DATA ANALYSIS AND RESCRAPING TOOL")
    print("=" * 50)
    
    # Show options
    print("\nOptions:")
    print("1. Just analyze missing data (no rescraping)")
    print("2. Rescrap products with missing brand data")
    print("3. Rescrap products with missing category data")
    print("4. Rescrap products with missing price data")
    print("5. Rescrap all products with missing data")
    print("6. Custom rescraping (specify issues)")
    
    choice = input("\nEnter your choice (1-6): ").strip()
    
    if choice == "1":
        # Just analyze
        logger.info("Running analysis only...")
        missing_data = await recraper.get_products_with_missing_data(limit=1000)
        
        with open('current_missing_data_analysis.json', 'w') as f:
            json.dump(missing_data, f, indent=2)
        
        print(f"\n📊 ANALYSIS RESULTS:")
        print(f"Products with missing brand: {len(missing_data.get('missing_brand', []))}")
        print(f"Products with missing category: {len(missing_data.get('missing_category', []))}")
        print(f"Products with missing price: {len(missing_data.get('missing_price', []))}")
        print(f"Products with multiple issues: {len(missing_data.get('multiple_issues', []))}")
        print(f"\nDetailed analysis saved to current_missing_data_analysis.json")
        
    elif choice == "2":
        # Rescrap missing brand
        results = await recraper.run_targeted_rescraping(['missing_brand'], limit=200)
        
        with open('brand_rescraping_results.json', 'w') as f:
            json.dump(results, f, indent=2)
        
        print(f"\n✅ BRAND RESCRAPING RESULTS:")
        print(f"Total attempted: {results['rescrap_results']['total_attempted']}")
        print(f"Successful: {results['rescrap_results']['successful']}")
        print(f"Failed: {results['rescrap_results']['failed']}")
        print(f"Brand improvements: {results['rescrap_results']['improvements']['brand']}")
        
    elif choice == "3":
        # Rescrap missing category
        results = await recraper.run_targeted_rescraping(['missing_category'], limit=200)
        
        with open('category_rescraping_results.json', 'w') as f:
            json.dump(results, f, indent=2)
        
        print(f"\n✅ CATEGORY RESCRAPING RESULTS:")
        print(f"Total attempted: {results['rescrap_results']['total_attempted']}")
        print(f"Successful: {results['rescrap_results']['successful']}")
        print(f"Failed: {results['rescrap_results']['failed']}")
        print(f"Category improvements: {results['rescrap_results']['improvements']['category']}")
        
    elif choice == "4":
        # Rescrap missing price
        results = await recraper.run_targeted_rescraping(['missing_price'], limit=200)
        
        with open('price_rescraping_results.json', 'w') as f:
            json.dump(results, f, indent=2)
        
        print(f"\n✅ PRICE RESCRAPING RESULTS:")
        print(f"Total attempted: {results['rescrap_results']['total_attempted']}")
        print(f"Successful: {results['rescrap_results']['successful']}")
        print(f"Failed: {results['rescrap_results']['failed']}")
        print(f"Price improvements: {results['rescrap_results']['improvements']['price']}")
        
    elif choice == "5":
        # Rescrap all missing data
        results = await recraper.run_targeted_rescraping(['missing_brand', 'missing_category', 'missing_price'], limit=500)
        
        with open('full_rescraping_results.json', 'w') as f:
            json.dump(results, f, indent=2)
        
        print(f"\n✅ FULL RESCRAPING RESULTS:")
        print(f"Total attempted: {results['rescrap_results']['total_attempted']}")
        print(f"Successful: {results['rescrap_results']['successful']}")
        print(f"Failed: {results['rescrap_results']['failed']}")
        print(f"Improvements:")
        print(f"  - Brand: {results['rescrap_results']['improvements']['brand']}")
        print(f"  - Category: {results['rescrap_results']['improvements']['category']}")
        print(f"  - Price: {results['rescrap_results']['improvements']['price']}")
        
    elif choice == "6":
        # Custom rescraping
        print("\nAvailable issues: missing_brand, missing_category, missing_price")
        issues_input = input("Enter issues to target (comma-separated): ").strip()
        target_issues = [issue.strip() for issue in issues_input.split(',')]
        
        limit_input = input("Enter limit (default 100): ").strip()
        limit = int(limit_input) if limit_input else 100
        
        results = await recraper.run_targeted_rescraping(target_issues, limit=limit)
        
        with open('custom_rescraping_results.json', 'w') as f:
            json.dump(results, f, indent=2)
        
        print(f"\n✅ CUSTOM RESCRAPING RESULTS:")
        print(f"Total attempted: {results['rescrap_results']['total_attempted']}")
        print(f"Successful: {results['rescrap_results']['successful']}")
        print(f"Failed: {results['rescrap_results']['failed']}")
        print(f"Improvements: {results['rescrap_results']['improvements']}")
        
    else:
        print("❌ Invalid choice. Please run the script again.")

if __name__ == "__main__":
    asyncio.run(main())