#!/usr/bin/env python3
"""
Test script to verify HomePro pricing fix for product 1288319
"""
import asyncio
import sys
import os
sys.path.append('/Users/chongraktanaka/Documents/Project/ris data scrap')

from src.scrapers.homepro_scraper import HomeProScraper
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def test_homepro_pricing():
    """Test HomePro pricing extraction for problematic product"""
    
    # The problematic product URL
    test_url = "https://www.homepro.co.th/p/1288319"
    
    logger.info(f"Testing HomePro pricing fix for product: {test_url}")
    
    scraper = HomeProScraper(use_native=True)
    
    try:
        # Test single product scraping
        result = await scraper.scrape_single_product(test_url)
        
        if result:
            logger.info(f"✅ Successfully scraped product!")
            logger.info(f"Product Name: {result.get('name', 'N/A')}")
            logger.info(f"Current Price: ฿{result.get('current_price', 'N/A')}")
            logger.info(f"Original Price: ฿{result.get('original_price', 'N/A')}")
            logger.info(f"Brand: {result.get('brand', 'N/A')}")
            logger.info(f"Category: {result.get('category', 'N/A')}")
            logger.info(f"Strategy Used: {result.get('scrape_strategy', 'N/A')}")
            
            # Check if pricing is now correct
            current_price = result.get('current_price')
            original_price = result.get('original_price')
            
            if current_price and isinstance(current_price, (int, float)):
                if 30000 <= current_price <= 35000:
                    logger.info("✅ Current price looks correct (around ฿32,190)")
                else:
                    logger.warning(f"❌ Current price still seems incorrect: ฿{current_price}")
            
            if original_price and isinstance(original_price, (int, float)):
                if 40000 <= original_price <= 50000:
                    logger.info("✅ Original price looks correct (around ฿45,990)")
                else:
                    logger.warning(f"❌ Original price still seems incorrect: ฿{original_price}")
            
        else:
            logger.error("❌ Failed to scrape product")
            
    except Exception as e:
        logger.error(f"❌ Error during test: {str(e)}")
        
    finally:
        await scraper.close()

if __name__ == "__main__":
    asyncio.run(test_homepro_pricing())