#!/usr/bin/env python3
"""
Test scraping refrigerator categories using existing scrapers
"""

import asyncio
import json
import logging
from datetime import datetime
import sys
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).parent))

from src.scrapers.thaiwatsadu_scraper import ThaiWatsaduScraper
from src.scrapers.homepro_scraper import HomeProScraper
from src.services.supabase_service import SupabaseService

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def test_twd_refrigerators():
    """Test Thai Watsadu refrigerator scraping"""
    logger.info("\n" + "="*60)
    logger.info("Testing Thai Watsadu Refrigerator Category")
    logger.info("="*60)
    
    url = "https://www.thaiwatsadu.com/en/category/%E0%B8%95%E0%B8%B9%E0%B9%89%E0%B9%80%E0%B8%A2%E0%B9%87%E0%B8%99-630301"
    
    try:
        scraper = ThaiWatsaduScraper()
        supabase = SupabaseService()
        
        # Create a scrape job
        job = await supabase.create_scrape_job(
            job_type='category_scrape',
            target_url=url,
            retailer_code='TWD'
        )
        
        logger.info(f"Created job: {job['id']}")
        
        # Get category products
        products = await scraper.get_category_products(url, max_products=20)
        
        logger.info(f"Found {len(products)} products")
        
        # Save sample products
        if products:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"twd_refrigerators_{timestamp}.json"
            
            sample_data = {
                "retailer": "TWD",
                "category": "Refrigerators",
                "url": url,
                "scraped_at": timestamp,
                "total_products": len(products),
                "sample_products": [
                    {
                        "name": p.name,
                        "sku": p.sku,
                        "brand": p.brand,
                        "price": p.current_price,
                        "original_price": p.original_price,
                        "url": p.url,
                        "availability": p.availability
                    } for p in products[:10]
                ]
            }
            
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(sample_data, f, ensure_ascii=False, indent=2)
            
            logger.info(f"Saved sample to {filename}")
            
            # Show sample brands and price range
            brands = list(set(p.brand for p in products if p.brand))
            prices = [p.current_price for p in products if p.current_price]
            
            logger.info(f"Brands found: {', '.join(brands[:10])}")
            if prices:
                logger.info(f"Price range: ฿{min(prices):,.0f} - ฿{max(prices):,.0f}")
        
        # Update job status
        await supabase.update_scrape_job(job['id'], {
            'status': 'completed' if products else 'failed',
            'success_items': len(products),
            'processed_items': len(products)
        })
        
    except Exception as e:
        logger.error(f"Error testing TWD: {str(e)}")
        import traceback
        traceback.print_exc()

async def test_homepro_refrigerators():
    """Test HomePro refrigerator scraping"""
    logger.info("\n" + "="*60)
    logger.info("Testing HomePro Refrigerator Category")
    logger.info("="*60)
    
    url = "https://www.homepro.co.th/c/APP09"
    
    try:
        scraper = HomeProScraper()
        supabase = SupabaseService()
        
        # Create a scrape job
        job = await supabase.create_scrape_job(
            job_type='category_scrape',
            target_url=url,
            retailer_code='HP'
        )
        
        logger.info(f"Created job: {job['id']}")
        
        # Get category products
        products = await scraper.get_category_products(url, max_products=20)
        
        logger.info(f"Found {len(products)} products")
        
        # Save sample products
        if products:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"homepro_refrigerators_{timestamp}.json"
            
            sample_data = {
                "retailer": "HP",
                "category": "Refrigerators",
                "url": url,
                "scraped_at": timestamp,
                "total_products": len(products),
                "sample_products": [
                    {
                        "name": p.name,
                        "sku": p.sku,
                        "brand": p.brand,
                        "price": p.current_price,
                        "original_price": p.original_price,
                        "url": p.url,
                        "availability": p.availability
                    } for p in products[:10]
                ]
            }
            
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(sample_data, f, ensure_ascii=False, indent=2)
            
            logger.info(f"Saved sample to {filename}")
            
            # Show sample brands and price range
            brands = list(set(p.brand for p in products if p.brand))
            prices = [p.current_price for p in products if p.current_price]
            
            logger.info(f"Brands found: {', '.join(brands[:10])}")
            if prices:
                logger.info(f"Price range: ฿{min(prices):,.0f} - ฿{max(prices):,.0f}")
        
        # Update job status
        await supabase.update_scrape_job(job['id'], {
            'status': 'completed' if products else 'failed',
            'success_items': len(products),
            'processed_items': len(products)
        })
        
    except Exception as e:
        logger.error(f"Error testing HomePro: {str(e)}")
        import traceback
        traceback.print_exc()

async def main():
    """Main function"""
    logger.info("Starting refrigerator category testing")
    
    # Test each retailer
    await test_twd_refrigerators()
    await asyncio.sleep(3)
    
    await test_homepro_refrigerators()
    
    logger.info("\n" + "="*60)
    logger.info("Testing complete! Check the generated JSON files")
    logger.info("="*60)

if __name__ == "__main__":
    asyncio.run(main())