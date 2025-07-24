#!/usr/bin/env python3
"""
Scrape the 3 specific HomePro categories with improved data extraction
"""

import asyncio
import sys
import os
import logging

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.scrapers.homepro_scraper import HomeProScraper

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def scrape_categories():
    """Scrape the 3 HomePro categories with improved extraction"""
    
    categories = [
        "https://www.homepro.co.th/c/BED",  # Bedroom/Bedding
        "https://www.homepro.co.th/c/CON",  # Construction  
        "https://www.homepro.co.th/c/CLO"   # Clothing/Closets
    ]
    
    logger.info("🚀 Starting HomePro category scraping with improved data extraction")
    logger.info(f"📋 Categories to scrape: {len(categories)}")
    
    try:
        # Initialize scraper with native strategy for improved extraction
        scraper = HomeProScraper(use_native=True)
        
        all_results = []
        
        for i, category_url in enumerate(categories, 1):
            category_code = category_url.split('/')[-1]
            logger.info(f"\n🔄 [{i}/{len(categories)}] Scraping category: {category_code}")
            logger.info(f"📍 URL: {category_url}")
            
            try:
                # Scrape category with max 20 pages and 3 concurrent workers
                result = await scraper.scrape_category(
                    category_url=category_url,
                    max_pages=20,
                    max_concurrent=3
                )
                
                all_results.append(result)
                
                # Log results
                logger.info(f"✅ Category {category_code} completed:")
                logger.info(f"   🔍 Discovered: {result.get('discovered', 0)} products")
                logger.info(f"   ✅ Success: {result.get('success', 0)} products")
                logger.info(f"   ❌ Failed: {result.get('failed', 0)} products")
                logger.info(f"   📊 Success Rate: {result.get('success_rate', 0):.1f}%")
                
                if result.get('job_id'):
                    logger.info(f"   🆔 Job ID: {result['job_id']}")
                
                # Small delay between categories
                if i < len(categories):
                    logger.info("⏳ Waiting 30 seconds before next category...")
                    await asyncio.sleep(30)
                    
            except Exception as e:
                logger.error(f"❌ Error scraping {category_code}: {str(e)}")
                all_results.append({
                    'category_url': category_url,
                    'error': str(e),
                    'success': 0,
                    'failed': 0,
                    'discovered': 0
                })
        
        # Summary
        logger.info("\n" + "="*50)
        logger.info("📊 SCRAPING SUMMARY")
        logger.info("="*50)
        
        total_discovered = sum(r.get('discovered', 0) for r in all_results)
        total_success = sum(r.get('success', 0) for r in all_results)
        total_failed = sum(r.get('failed', 0) for r in all_results)
        
        logger.info(f"🔍 Total Products Discovered: {total_discovered}")
        logger.info(f"✅ Total Successful Scrapes: {total_success}")
        logger.info(f"❌ Total Failed Scrapes: {total_failed}")
        logger.info(f"📊 Overall Success Rate: {(total_success/(total_success+total_failed)*100) if (total_success+total_failed) > 0 else 0:.1f}%")
        
        logger.info("\n📋 Per-Category Results:")
        for result in all_results:
            category_code = result.get('category_url', '').split('/')[-1]
            if 'error' in result:
                logger.info(f"   {category_code}: ERROR - {result['error']}")
            else:
                logger.info(f"   {category_code}: {result.get('success', 0)}/{result.get('discovered', 0)} products scraped")
        
        # Get final stats
        stats = await scraper.get_scraping_stats()
        if stats.get('products'):
            logger.info(f"\n📈 Updated Database Stats:")
            logger.info(f"   Total Products: {stats['products'].get('total', 0)}")
            logger.info(f"   HomePro Products: {stats['products'].get('by_retailer', {}).get('HP', 0)}")
        
        logger.info("\n🎉 All category scraping completed!")
        
    except Exception as e:
        logger.error(f"💥 Fatal error during scraping: {str(e)}")
        import traceback
        traceback.print_exc()
    
    finally:
        await scraper.close()
        logger.info("🔒 Scraper closed")

if __name__ == "__main__":
    asyncio.run(scrape_categories())