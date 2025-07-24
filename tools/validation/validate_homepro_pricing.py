#!/usr/bin/env python3
"""
Validation script to compare database pricing data with actual browser data
"""
import asyncio
import sys
import os
import random
import logging
from datetime import datetime
sys.path.append(os.path.join(os.path.dirname(__file__), '../..'))

from src.scrapers.homepro_scraper import HomeProScraper
from src.services.supabase_service import SupabaseService
import aiohttp
import ssl
from bs4 import BeautifulSoup
import re
import json

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(f'validation_homepro_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class HomePriceValidator:
    def __init__(self):
        self.db_service = SupabaseService()
        self.scraper = None
        
    async def initialize(self):
        """Initialize the scraper for validation"""
        self.scraper = HomeProScraper(use_native=True)
        
    async def get_sample_products(self, limit=20):
        """Get a sample of HomePro products from database"""
        try:
            # Get all HomePro products
            products = await self.db_service.get_products(
                filters={'retailer_code': 'HP'},
                limit=1000
            )
            
            if not products:
                logger.error("No HomePro products found in database")
                return []
            
            logger.info(f"Found {len(products)} HomePro products in database")
            
            # Filter products with valid pricing data
            valid_products = []
            for product in products:
                if (product.get('current_price') and 
                    product.get('current_price', 0) > 0 and
                    product.get('sku')):
                    valid_products.append(product)
            
            logger.info(f"Found {len(valid_products)} products with valid pricing data")
            
            # Return random sample
            sample_size = min(limit, len(valid_products))
            sample = random.sample(valid_products, sample_size)
            
            logger.info(f"Selected {len(sample)} products for validation")
            return sample
            
        except Exception as e:
            logger.error(f"Error getting sample products: {str(e)}")
            return []
    
    async def validate_product_pricing(self, product_data):
        """Validate a single product's pricing against browser data"""
        sku = product_data.get('sku')
        db_current_price = product_data.get('current_price', 0)
        db_original_price = product_data.get('original_price', 0)
        product_name = product_data.get('name', 'Unknown')
        
        logger.info(f"🔍 Validating product: {sku} - {product_name}")
        logger.info(f"📊 DB Current Price: ฿{db_current_price}")
        logger.info(f"📊 DB Original Price: ฿{db_original_price}")
        
        # Construct HomePro URL
        product_url = f"https://www.homepro.co.th/p/{sku}"
        
        try:
            # Scrape current pricing data
            browser_data = await self.scraper.scrape_single_product(product_url)
            
            if not browser_data:
                logger.error(f"❌ Failed to scrape product {sku}")
                return {
                    'sku': sku,
                    'name': product_name,
                    'status': 'scrape_failed',
                    'db_current_price': db_current_price,
                    'db_original_price': db_original_price,
                    'browser_current_price': None,
                    'browser_original_price': None,
                    'price_match': False,
                    'error': 'Failed to scrape product'
                }
            
            browser_current_price = browser_data.get('current_price', 0)
            browser_original_price = browser_data.get('original_price', 0)
            
            logger.info(f"🌐 Browser Current Price: ฿{browser_current_price}")
            logger.info(f"🌐 Browser Original Price: ฿{browser_original_price}")
            
            # Compare prices with tolerance
            current_price_match = abs(float(db_current_price) - float(browser_current_price)) < 0.01
            original_price_match = True  # Default to true if no original price
            
            if db_original_price and browser_original_price:
                original_price_match = abs(float(db_original_price) - float(browser_original_price)) < 0.01
            
            overall_match = current_price_match and original_price_match
            
            # Log results
            if overall_match:
                logger.info(f"✅ Price validation PASSED for {sku}")
            else:
                logger.warning(f"❌ Price validation FAILED for {sku}")
                if not current_price_match:
                    logger.warning(f"   Current price mismatch: DB ฿{db_current_price} vs Browser ฿{browser_current_price}")
                if not original_price_match:
                    logger.warning(f"   Original price mismatch: DB ฿{db_original_price} vs Browser ฿{browser_original_price}")
            
            return {
                'sku': sku,
                'name': product_name,
                'status': 'validated',
                'db_current_price': db_current_price,
                'db_original_price': db_original_price,
                'browser_current_price': browser_current_price,
                'browser_original_price': browser_original_price,
                'current_price_match': current_price_match,
                'original_price_match': original_price_match,
                'overall_match': overall_match,
                'price_difference': float(browser_current_price) - float(db_current_price) if browser_current_price else None
            }
            
        except Exception as e:
            logger.error(f"❌ Error validating product {sku}: {str(e)}")
            return {
                'sku': sku,
                'name': product_name,
                'status': 'validation_error',
                'db_current_price': db_current_price,
                'db_original_price': db_original_price,
                'browser_current_price': None,
                'browser_original_price': None,
                'price_match': False,
                'error': str(e)
            }
    
    async def run_validation(self, sample_size=20):
        """Run validation on a sample of products"""
        logger.info(f"🚀 Starting HomePro price validation with {sample_size} products")
        
        # Initialize
        await self.initialize()
        
        # Get sample products
        sample_products = await self.get_sample_products(sample_size)
        
        if not sample_products:
            logger.error("No products to validate")
            return
        
        # Validate each product
        validation_results = []
        failed_validations = []
        passed_validations = []
        
        try:
            for i, product_data in enumerate(sample_products, 1):
                logger.info(f"📋 Validating product {i}/{len(sample_products)}")
                
                result = await self.validate_product_pricing(product_data)
                validation_results.append(result)
                
                if result['status'] == 'validated' and result['overall_match']:
                    passed_validations.append(result)
                else:
                    failed_validations.append(result)
                
                # Progress update
                logger.info(f"📊 Progress: {i}/{len(sample_products)} | Passed: {len(passed_validations)} | Failed: {len(failed_validations)}")
                
                # Add delay between validations
                if i < len(sample_products):
                    await asyncio.sleep(2)
                    
        except Exception as e:
            logger.error(f"❌ Fatal error during validation: {str(e)}")
            
        finally:
            # Cleanup
            if self.scraper:
                await self.scraper.close()
            
            # Generate report
            self.generate_validation_report(validation_results, passed_validations, failed_validations)
    
    def generate_validation_report(self, all_results, passed_results, failed_results):
        """Generate a comprehensive validation report"""
        total_count = len(all_results)
        passed_count = len(passed_results)
        failed_count = len(failed_results)
        
        logger.info("🏁 VALIDATION REPORT:")
        logger.info(f"📊 Total products validated: {total_count}")
        logger.info(f"✅ Passed validations: {passed_count} ({passed_count/total_count*100:.1f}%)")
        logger.info(f"❌ Failed validations: {failed_count} ({failed_count/total_count*100:.1f}%)")
        
        if failed_results:
            logger.info("\n❌ FAILED VALIDATIONS:")
            for result in failed_results:
                logger.info(f"   SKU: {result['sku']}")
                logger.info(f"   Name: {result['name']}")
                logger.info(f"   Status: {result['status']}")
                if result.get('price_difference'):
                    logger.info(f"   Price difference: ฿{result['price_difference']:.2f}")
                if result.get('error'):
                    logger.info(f"   Error: {result['error']}")
                logger.info("   ---")
        
        # Calculate statistics
        if passed_results:
            price_differences = [r['price_difference'] for r in passed_results if r.get('price_difference') is not None]
            if price_differences:
                avg_difference = sum(price_differences) / len(price_differences)
                max_difference = max(price_differences)
                min_difference = min(price_differences)
                
                logger.info(f"\n📈 PRICE DIFFERENCE STATISTICS:")
                logger.info(f"   Average difference: ฿{avg_difference:.2f}")
                logger.info(f"   Maximum difference: ฿{max_difference:.2f}")
                logger.info(f"   Minimum difference: ฿{min_difference:.2f}")
        
        # Overall assessment
        if passed_count / total_count >= 0.95:
            logger.info("🎉 ASSESSMENT: Excellent - 95%+ accuracy!")
        elif passed_count / total_count >= 0.90:
            logger.info("✅ ASSESSMENT: Good - 90%+ accuracy")
        elif passed_count / total_count >= 0.80:
            logger.info("⚠️  ASSESSMENT: Fair - 80%+ accuracy, some issues to address")
        else:
            logger.info("❌ ASSESSMENT: Poor - <80% accuracy, significant issues detected")

async def main():
    """Main function to run validation"""
    import argparse
    parser = argparse.ArgumentParser(description='Validate HomePro pricing data')
    parser.add_argument('--sample-size', type=int, default=20,
                       help='Number of products to validate (default: 20)')
    parser.add_argument('--specific-sku', type=str,
                       help='Validate a specific SKU only')
    
    args = parser.parse_args()
    
    validator = HomePriceValidator()
    
    if args.specific_sku:
        # Validate specific product
        logger.info(f"🎯 Validating specific SKU: {args.specific_sku}")
        try:
            await validator.initialize()
            product_data = {
                'sku': args.specific_sku,
                'current_price': 0,  # Will be populated from database
                'original_price': 0,
                'name': 'Specific Product'
            }
            result = await validator.validate_product_pricing(product_data)
            validator.generate_validation_report([result], [result] if result['overall_match'] else [], [] if result['overall_match'] else [result])
        finally:
            if validator.scraper:
                await validator.scraper.close()
    else:
        # Run full validation
        await validator.run_validation(args.sample_size)

if __name__ == "__main__":
    asyncio.run(main())