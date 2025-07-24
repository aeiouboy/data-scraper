#!/usr/bin/env python3
"""Test scraping a specific HomePro URL to debug data extraction"""

import asyncio
import sys
import os
import logging

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.scrapers.homepro_scraper import HomeProScraper

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_specific_url():
    """Test scraping the specific URL from user"""
    test_url = "https://www.homepro.co.th/p/270661"
    
    logger.info(f"Testing URL: {test_url}")
    
    try:
        # Initialize scraper with native strategy
        scraper = HomeProScraper(use_native=True)
        
        # Test scraping
        result = await scraper.scrape_single_product(test_url)
        
        if result:
            logger.info("✅ Successfully scraped product!")
            logger.info(f"Product data:")
            for key, value in result.items():
                logger.info(f"  {key}: {value}")
        else:
            logger.error("❌ Failed to scrape product")
            
        # Also test the raw strategy to see what data it extracts
        logger.info("\n" + "="*50)
        logger.info("Testing raw strategy extraction...")
        
        strategy_result = await scraper.strategy.scrape_url(test_url)
        
        if strategy_result.success:
            logger.info(f"✅ Strategy extracted data using: {strategy_result.strategy_used}")
            logger.info(f"Raw data keys: {list(strategy_result.data.keys()) if strategy_result.data else 'None'}")
            
            if strategy_result.data:
                logger.info("Raw extracted fields:")
                for key, value in strategy_result.data.items():
                    logger.info(f"  {key}: {str(value)[:100]}...")
        else:
            logger.error(f"❌ Strategy failed: {strategy_result.error}")
            
    except Exception as e:
        logger.error(f"Error during test: {str(e)}")
        import traceback
        traceback.print_exc()
    
    finally:
        await scraper.close()

if __name__ == "__main__":
    asyncio.run(test_specific_url())