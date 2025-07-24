#!/usr/bin/env python3
"""
Re-scrape all existing HomePro categories to fix pricing data after scraper improvements
"""
import asyncio
import sys
import os
import logging
from datetime import datetime
sys.path.append(os.path.join(os.path.dirname(__file__), '../..'))

from src.scrapers.homepro_scraper import HomeProScraper
from src.services.supabase_service import SupabaseService

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(f'rescrape_homepro_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# HomePro main categories to re-scrape
HOMEPRO_CATEGORIES = [
    {
        'code': 'APP',
        'name': 'Appliances',
        'url': 'https://www.homepro.co.th/c/APP',
        'priority': 'high'
    },
    {
        'code': 'FUR',
        'name': 'Furniture & Decor',
        'url': 'https://www.homepro.co.th/c/FUR',
        'priority': 'high'
    },
    {
        'code': 'FLO',
        'name': 'Floor & Wall',
        'url': 'https://www.homepro.co.th/c/FLO',
        'priority': 'high'
    },
    {
        'code': 'TVA',
        'name': 'TV, Audio, Gaming',
        'url': 'https://www.homepro.co.th/c/TVA',
        'priority': 'high'
    },
    {
        'code': 'HHP',
        'name': 'Storage & Household',
        'url': 'https://www.homepro.co.th/c/HHP',
        'priority': 'medium'
    },
    {
        'code': 'TOO',
        'name': 'Tools & Hardware',
        'url': 'https://www.homepro.co.th/c/TOO',
        'priority': 'medium'
    },
    {
        'code': 'CON',
        'name': 'Construction Materials',
        'url': 'https://www.homepro.co.th/c/CON',
        'priority': 'medium'
    },
    {
        'code': 'SMA',
        'name': 'Small Appliances',
        'url': 'https://www.homepro.co.th/c/SMA',
        'priority': 'medium'
    },
    {
        'code': 'LIG',
        'name': 'Lighting',
        'url': 'https://www.homepro.co.th/c/LIG',
        'priority': 'low'
    },
    {
        'code': 'GAR',
        'name': 'Garden & Outdoor',
        'url': 'https://www.homepro.co.th/c/GAR',
        'priority': 'low'
    }
]

class HomeProreScrapeManager:
    def __init__(self):
        self.scraper = None
        self.db_service = SupabaseService()
        
    async def initialize(self):
        """Initialize the scraper"""
        self.scraper = HomeProScraper(use_native=True)
        logger.info("HomePro scraper initialized with native strategy")
        
    async def get_existing_products_count(self):
        """Get count of existing HomePro products"""
        try:
            result = await self.db_service.get_products_by_retailer('HP')
            return len(result) if result else 0
        except Exception as e:
            logger.error(f"Error getting existing products count: {str(e)}")
            return 0
    
    async def scrape_category(self, category_info, max_pages=50):
        """Scrape a single category with progress tracking"""
        category_code = category_info['code']
        category_name = category_info['name']
        category_url = category_info['url']
        
        logger.info(f"🔄 Starting re-scrape of {category_name} ({category_code})")
        logger.info(f"📄 URL: {category_url}")
        logger.info(f"📊 Max pages: {max_pages}")
        
        try:
            # Track initial product count
            initial_count = await self.get_existing_products_count()
            
            # Scrape the category
            results = await self.scraper.scrape_category(category_url, max_pages=max_pages)
            
            # Track final product count
            final_count = await self.get_existing_products_count()
            new_products = final_count - initial_count
            
            logger.info(f"✅ Completed {category_name}: {len(results)} products processed, {new_products} new/updated")
            
            return {
                'category': category_name,
                'code': category_code,
                'products_processed': len(results),
                'new_products': new_products,
                'success': True
            }
            
        except Exception as e:
            logger.error(f"❌ Error scraping {category_name}: {str(e)}")
            return {
                'category': category_name,
                'code': category_code,
                'products_processed': 0,
                'new_products': 0,
                'success': False,
                'error': str(e)
            }
    
    async def scrape_all_categories(self, priority_filter=None, max_pages_per_category=50):
        """Scrape all categories with optional priority filtering"""
        
        # Filter categories by priority if specified
        categories_to_scrape = HOMEPRO_CATEGORIES
        if priority_filter:
            categories_to_scrape = [c for c in HOMEPRO_CATEGORIES if c['priority'] == priority_filter]
        
        logger.info(f"🚀 Starting re-scrape of {len(categories_to_scrape)} HomePro categories")
        logger.info(f"📄 Max pages per category: {max_pages_per_category}")
        
        if priority_filter:
            logger.info(f"🎯 Priority filter: {priority_filter}")
        
        # Track overall progress
        total_categories = len(categories_to_scrape)
        completed_categories = 0
        total_products_processed = 0
        total_new_products = 0
        failed_categories = []
        
        # Initialize scraper
        await self.initialize()
        
        try:
            # Process each category
            for i, category_info in enumerate(categories_to_scrape, 1):
                logger.info(f"📋 Processing category {i}/{total_categories}: {category_info['name']}")
                
                # Scrape the category
                result = await self.scrape_category(category_info, max_pages=max_pages_per_category)
                
                # Update progress
                completed_categories += 1
                total_products_processed += result['products_processed']
                total_new_products += result['new_products']
                
                if not result['success']:
                    failed_categories.append(result)
                
                # Progress report
                logger.info(f"📊 Progress: {completed_categories}/{total_categories} categories completed")
                logger.info(f"📈 Total products processed: {total_products_processed}")
                logger.info(f"🆕 Total new/updated products: {total_new_products}")
                
                # Add delay between categories to be respectful
                if i < total_categories:
                    logger.info("⏱️ Waiting 5 seconds before next category...")
                    await asyncio.sleep(5)
                    
        except Exception as e:
            logger.error(f"❌ Fatal error during scraping: {str(e)}")
            
        finally:
            # Cleanup
            if self.scraper:
                await self.scraper.close()
            
            # Final report
            logger.info("🏁 FINAL REPORT:")
            logger.info(f"✅ Successfully completed: {completed_categories - len(failed_categories)}/{total_categories} categories")
            logger.info(f"📊 Total products processed: {total_products_processed}")
            logger.info(f"🆕 Total new/updated products: {total_new_products}")
            
            if failed_categories:
                logger.info(f"❌ Failed categories: {len(failed_categories)}")
                for failure in failed_categories:
                    logger.error(f"   - {failure['category']} ({failure['code']}): {failure.get('error', 'Unknown error')}")
            
            return {
                'total_categories': total_categories,
                'completed_categories': completed_categories,
                'total_products_processed': total_products_processed,
                'total_new_products': total_new_products,
                'failed_categories': failed_categories
            }

async def main():
    """Main function to run the re-scraping"""
    
    import argparse
    parser = argparse.ArgumentParser(description='Re-scrape HomePro categories with fixed pricing')
    parser.add_argument('--priority', choices=['high', 'medium', 'low'], 
                       help='Only scrape categories with this priority')
    parser.add_argument('--max-pages', type=int, default=50,
                       help='Maximum pages per category (default: 50)')
    parser.add_argument('--dry-run', action='store_true',
                       help='Show what would be scraped without actually scraping')
    
    args = parser.parse_args()
    
    if args.dry_run:
        logger.info("🔍 DRY RUN MODE - showing what would be scraped:")
        categories_to_show = HOMEPRO_CATEGORIES
        if args.priority:
            categories_to_show = [c for c in HOMEPRO_CATEGORIES if c['priority'] == args.priority]
        
        for i, category in enumerate(categories_to_show, 1):
            logger.info(f"{i}. {category['name']} ({category['code']}) - Priority: {category['priority']}")
        
        logger.info(f"Total categories to scrape: {len(categories_to_show)}")
        logger.info(f"Max pages per category: {args.max_pages}")
        return
    
    # Run the scraping
    manager = HomeProreScrapeManager()
    result = await manager.scrape_all_categories(
        priority_filter=args.priority,
        max_pages_per_category=args.max_pages
    )
    
    # Success summary
    if result['failed_categories']:
        logger.warning(f"⚠️  Completed with {len(result['failed_categories'])} failures")
    else:
        logger.info("🎉 All categories completed successfully!")

if __name__ == "__main__":
    asyncio.run(main())