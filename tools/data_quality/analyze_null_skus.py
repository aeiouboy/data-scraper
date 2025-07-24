#!/usr/bin/env python3
"""
Analyze products with null SKU values and prepare for rescraping
"""

import asyncio
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
from src.services.supabase_service import SupabaseService
from src.scrapers.base_scraper import BaseScraper
from src.scrapers.homepro_scraper import HomeProScraper
from src.scrapers.thaiwatsadu_scraper import ThaiWatsaduScraper
from src.scrapers.globalhouse_scraper import GlobalHouseScraper
from src.scrapers.dohome_scraper import DoHomeScraper
from src.scrapers.boonthavorn_scraper import BoonthavornScraper
from src.scrapers.megahome_scraper import MegaHomeScraper
import json

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('null_sku_analysis.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class NullSKUAnalyzer:
    """Analyze and rescrap products with null SKU values"""
    
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
        
    async def analyze_null_skus(self) -> Dict[str, Any]:
        """Analyze products with null SKU values"""
        logger.info("Starting null SKU analysis...")
        
        try:
            # Query for products with null SKUs
            result = self.supabase.client.table('products')\
                .select('id, sku, name, brand, category, retailer_code, url, scraped_at')\
                .is_('sku', 'null')\
                .execute()
            
            null_sku_products = result.data
            
            # Group by retailer
            by_retailer = {}
            for product in null_sku_products:
                retailer = product['retailer_code']
                if retailer not in by_retailer:
                    by_retailer[retailer] = []
                by_retailer[retailer].append(product)
            
            # Summary statistics
            total_null_skus = len(null_sku_products)
            retailer_counts = {k: len(v) for k, v in by_retailer.items()}
            
            analysis = {
                'total_null_skus': total_null_skus,
                'by_retailer': retailer_counts,
                'products': by_retailer,
                'analysis_time': datetime.now().isoformat()
            }
            
            logger.info(f"Found {total_null_skus} products with null SKUs")
            logger.info(f"Retailer breakdown: {retailer_counts}")
            
            return analysis
            
        except Exception as e:
            logger.error(f"Error analyzing null SKUs: {str(e)}")
            return {'error': str(e)}
    
    async def analyze_missing_data(self) -> Dict[str, Any]:
        """Analyze products with missing critical data"""
        logger.info("Starting missing data analysis...")
        
        try:
            # Query for products with missing critical data
            result = self.supabase.client.table('products')\
                .select('id, sku, name, brand, category, retailer_code, url, current_price, availability, scraped_at')\
                .execute()
            
            products = result.data
            
            missing_data = {
                'null_sku': [],
                'null_name': [],
                'null_brand': [],
                'null_category': [],
                'null_price': [],
                'null_availability': [],
                'multiple_issues': []
            }
            
            for product in products:
                issues = []
                
                if not product.get('sku'):
                    missing_data['null_sku'].append(product)
                    issues.append('sku')
                
                if not product.get('name'):
                    missing_data['null_name'].append(product)
                    issues.append('name')
                
                if not product.get('brand'):
                    missing_data['null_brand'].append(product)
                    issues.append('brand')
                
                if not product.get('category'):
                    missing_data['null_category'].append(product)
                    issues.append('category')
                
                if not product.get('current_price'):
                    missing_data['null_price'].append(product)
                    issues.append('price')
                
                if not product.get('availability'):
                    missing_data['null_availability'].append(product)
                    issues.append('availability')
                
                if len(issues) > 1:
                    missing_data['multiple_issues'].append({
                        'product': product,
                        'issues': issues
                    })
            
            # Summary statistics
            analysis = {
                'total_products': len(products),
                'missing_data_counts': {k: len(v) for k, v in missing_data.items() if k != 'multiple_issues'},
                'multiple_issues_count': len(missing_data['multiple_issues']),
                'missing_data': missing_data,
                'analysis_time': datetime.now().isoformat()
            }
            
            logger.info(f"Missing data analysis completed")
            logger.info(f"Total products: {len(products)}")
            for issue, count in analysis['missing_data_counts'].items():
                logger.info(f"Products with missing {issue}: {count}")
            
            return analysis
            
        except Exception as e:
            logger.error(f"Error analyzing missing data: {str(e)}")
            return {'error': str(e)}
    
    async def rescrap_products(self, products_to_rescrap: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Rescrap products with null SKUs"""
        logger.info(f"Starting to rescrap {len(products_to_rescrap)} products...")
        
        results = {
            'total_attempted': len(products_to_rescrap),
            'successful': 0,
            'failed': 0,
            'errors': []
        }
        
        for product in products_to_rescrap:
            try:
                retailer_code = product['retailer_code']
                url = product['url']
                product_id = product['id']
                
                if retailer_code not in self.scrapers:
                    logger.warning(f"No scraper available for retailer: {retailer_code}")
                    results['failed'] += 1
                    results['errors'].append({
                        'product_id': product_id,
                        'error': f"No scraper for retailer {retailer_code}"
                    })
                    continue
                
                scraper = self.scrapers[retailer_code]
                
                # Scrape the product
                logger.info(f"Rescraping product {product_id} from {retailer_code}: {url}")
                scraped_product = await scraper.scrape_product(url)
                
                if scraped_product:
                    # Update the product in database
                    await self.supabase.upsert_product(scraped_product)
                    results['successful'] += 1
                    logger.info(f"Successfully rescraped product {product_id}")
                else:
                    results['failed'] += 1
                    results['errors'].append({
                        'product_id': product_id,
                        'error': "Failed to scrape product"
                    })
                    logger.error(f"Failed to scrape product {product_id}")
                
            except Exception as e:
                results['failed'] += 1
                results['errors'].append({
                    'product_id': product.get('id', 'unknown'),
                    'error': str(e)
                })
                logger.error(f"Error rescraping product {product.get('id', 'unknown')}: {str(e)}")
        
        logger.info(f"Rescraping completed. Success: {results['successful']}, Failed: {results['failed']}")
        return results
    
    async def run_full_analysis_and_rescrap(self) -> Dict[str, Any]:
        """Run complete analysis and rescraping workflow"""
        logger.info("Starting full analysis and rescraping workflow...")
        
        # Step 1: Analyze null SKUs
        null_sku_analysis = await self.analyze_null_skus()
        
        if 'error' in null_sku_analysis:
            return null_sku_analysis
        
        # Step 2: Analyze all missing data
        missing_data_analysis = await self.analyze_missing_data()
        
        if 'error' in missing_data_analysis:
            return missing_data_analysis
        
        # Step 3: Prepare products for rescraping (focus on null SKUs first)
        products_to_rescrap = []
        for retailer, products in null_sku_analysis['products'].items():
            products_to_rescrap.extend(products)
        
        # Step 4: Rescrap products
        rescrap_results = await self.rescrap_products(products_to_rescrap)
        
        # Step 5: Re-analyze after rescraping
        post_rescrap_analysis = await self.analyze_null_skus()
        
        final_results = {
            'initial_null_sku_analysis': null_sku_analysis,
            'missing_data_analysis': missing_data_analysis,
            'rescrap_results': rescrap_results,
            'post_rescrap_analysis': post_rescrap_analysis,
            'completed_at': datetime.now().isoformat()
        }
        
        return final_results

async def main():
    """Main function to run the analysis"""
    analyzer = NullSKUAnalyzer()
    
    # Just run analysis first
    logger.info("Running null SKU analysis...")
    analysis = await analyzer.analyze_null_skus()
    
    # Save analysis to file
    with open('null_sku_analysis.json', 'w') as f:
        json.dump(analysis, f, indent=2)
    
    logger.info("Analysis saved to null_sku_analysis.json")
    
    # Also run missing data analysis
    logger.info("Running missing data analysis...")
    missing_analysis = await analyzer.analyze_missing_data()
    
    # Save missing data analysis to file
    with open('missing_data_analysis.json', 'w') as f:
        json.dump(missing_analysis, f, indent=2)
    
    logger.info("Missing data analysis saved to missing_data_analysis.json")
    
    # Print summary
    print(f"\n=== NULL SKU ANALYSIS SUMMARY ===")
    print(f"Total products with null SKUs: {analysis.get('total_null_skus', 0)}")
    print(f"By retailer: {analysis.get('by_retailer', {})}")
    
    print(f"\n=== MISSING DATA ANALYSIS SUMMARY ===")
    print(f"Total products: {missing_analysis.get('total_products', 0)}")
    print(f"Missing data counts: {missing_analysis.get('missing_data_counts', {})}")
    
    # Ask user if they want to proceed with rescraping
    if analysis.get('total_null_skus', 0) > 0:
        response = input(f"\nFound {analysis['total_null_skus']} products with null SKUs. Do you want to rescrap them? (y/n): ")
        if response.lower() == 'y':
            logger.info("Starting rescraping process...")
            full_results = await analyzer.run_full_analysis_and_rescrap()
            
            # Save full results
            with open('full_rescrap_results.json', 'w') as f:
                json.dump(full_results, f, indent=2)
            
            logger.info("Full rescraping results saved to full_rescrap_results.json")
            
            print(f"\n=== RESCRAPING RESULTS ===")
            print(f"Total attempted: {full_results['rescrap_results']['total_attempted']}")
            print(f"Successful: {full_results['rescrap_results']['successful']}")
            print(f"Failed: {full_results['rescrap_results']['failed']}")
            print(f"Remaining null SKUs: {full_results['post_rescrap_analysis']['total_null_skus']}")
        else:
            print("Rescraping skipped.")
    else:
        print("No products with null SKUs found. All products appear to have SKU values.")

if __name__ == "__main__":
    asyncio.run(main())