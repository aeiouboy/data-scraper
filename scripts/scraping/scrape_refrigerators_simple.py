#!/usr/bin/env python3
"""
Simple script to scrape refrigerator categories from Thai Watsadu and HomePro
"""

import asyncio
import json
import logging
from datetime import datetime
import sys
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).parent))

from src.services.firecrawl_client import FirecrawlClient
from src.scrapers.thaiwatsadu_scraper import ThaiWatsaduScraper
from src.scrapers.homepro_scraper import HomeProScraper
from src.services.supabase_service import SupabaseService

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Category URLs
CATEGORIES = [
    {
        "retailer": "TWD",
        "name": "Refrigerators",
        "url": "https://www.thaiwatsadu.com/en/category/%E0%B8%95%E0%B8%B9%E0%B9%89%E0%B9%80%E0%B8%A2%E0%B9%87%E0%B8%99-630301",
        "thai_name": "ตู้เย็น"
    },
    {
        "retailer": "HP",
        "name": "Refrigerators",
        "url": "https://www.homepro.co.th/c/APP09",
        "thai_name": "ตู้เย็น"
    }
]

async def scrape_with_firecrawl(url: str) -> dict:
    """Scrape a URL using Firecrawl API"""
    client = FirecrawlClient()
    
    try:
        logger.info(f"Scraping URL: {url}")
        result = await client.scrape(url)
        
        if result and result.get('success'):
            logger.info(f"Successfully scraped page")
            return result
        else:
            logger.error(f"Failed to scrape: {result}")
            return None
            
    except Exception as e:
        logger.error(f"Error scraping: {str(e)}")
        return None

async def analyze_twd_refrigerators():
    """Analyze Thai Watsadu refrigerator category"""
    logger.info("\n" + "="*60)
    logger.info("Analyzing Thai Watsadu Refrigerators")
    logger.info("="*60)
    
    url = CATEGORIES[0]['url']
    
    # First, let's scrape and analyze the page structure
    scraped_data = await scrape_with_firecrawl(url)
    
    if scraped_data:
        # Save raw data for analysis
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"twd_refrigerators_raw_{timestamp}.json"
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(scraped_data, f, ensure_ascii=False, indent=2)
        
        logger.info(f"Saved raw data to {filename}")
        
        # Extract markdown content
        if scraped_data.get('markdown'):
            md_filename = f"twd_refrigerators_content_{timestamp}.md"
            with open(md_filename, 'w', encoding='utf-8') as f:
                f.write(scraped_data['markdown'])
            logger.info(f"Saved markdown to {md_filename}")
        
        # Try to extract product information
        markdown = scraped_data.get('markdown', '')
        products = []
        
        # Look for product patterns in the content
        lines = markdown.split('\n')
        for i, line in enumerate(lines):
            # Look for price indicators
            if '฿' in line or 'THB' in line:
                # Extract price
                import re
                price_match = re.search(r'฿\s*([\d,]+(?:\.\d{2})?)', line)
                if price_match:
                    price = float(price_match.group(1).replace(',', ''))
                    
                    # Look for product name in previous lines
                    product_name = None
                    for j in range(max(0, i-5), i):
                        if lines[j].strip() and not any(x in lines[j] for x in ['฿', 'THB', 'Filter', 'Sort']):
                            product_name = lines[j].strip()
                            break
                    
                    if product_name and price:
                        products.append({
                            'name': product_name,
                            'price': price,
                            'retailer': 'TWD'
                        })
        
        logger.info(f"Found {len(products)} potential products")
        
        # Save products
        if products:
            products_filename = f"twd_refrigerators_products_{timestamp}.json"
            with open(products_filename, 'w', encoding='utf-8') as f:
                json.dump({
                    'category': CATEGORIES[0],
                    'products_count': len(products),
                    'products': products[:10]  # Save first 10 as sample
                }, f, ensure_ascii=False, indent=2)
            logger.info(f"Saved products to {products_filename}")
    
    # Now try with the actual scraper
    logger.info("\nTrying with ThaiWatsaduScraper...")
    try:
        scraper = ThaiWatsaduScraper()
        # Try to get category products
        logger.info("Note: ThaiWatsaduScraper may need specific category handling")
    except Exception as e:
        logger.error(f"Error with scraper: {str(e)}")

async def analyze_homepro_refrigerators():
    """Analyze HomePro refrigerator category"""
    logger.info("\n" + "="*60)
    logger.info("Analyzing HomePro Refrigerators")
    logger.info("="*60)
    
    url = CATEGORIES[1]['url']
    
    # Scrape and analyze
    scraped_data = await scrape_with_firecrawl(url)
    
    if scraped_data:
        # Save raw data
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"homepro_refrigerators_raw_{timestamp}.json"
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(scraped_data, f, ensure_ascii=False, indent=2)
        
        logger.info(f"Saved raw data to {filename}")
        
        # Extract markdown
        if scraped_data.get('markdown'):
            md_filename = f"homepro_refrigerators_content_{timestamp}.md"
            with open(md_filename, 'w', encoding='utf-8') as f:
                f.write(scraped_data['markdown'])
            logger.info(f"Saved markdown to {md_filename}")
        
        # Extract products
        markdown = scraped_data.get('markdown', '')
        products = []
        
        lines = markdown.split('\n')
        for i, line in enumerate(lines):
            if '฿' in line:
                import re
                price_match = re.search(r'฿\s*([\d,]+(?:\.\d{2})?)', line)
                if price_match:
                    price = float(price_match.group(1).replace(',', ''))
                    
                    # HomePro might have different structure
                    product_name = None
                    for j in range(max(0, i-3), i):
                        if lines[j].strip() and '฿' not in lines[j]:
                            product_name = lines[j].strip()
                            break
                    
                    if product_name and price:
                        products.append({
                            'name': product_name,
                            'price': price,
                            'retailer': 'HP'
                        })
        
        logger.info(f"Found {len(products)} potential products")
        
        # Save products
        if products:
            products_filename = f"homepro_refrigerators_products_{timestamp}.json"
            with open(products_filename, 'w', encoding='utf-8') as f:
                json.dump({
                    'category': CATEGORIES[1],
                    'products_count': len(products),
                    'products': products[:10]
                }, f, ensure_ascii=False, indent=2)
            logger.info(f"Saved products to {products_filename}")

async def main():
    """Main function"""
    logger.info("Starting refrigerator category analysis")
    
    # Analyze each retailer
    await analyze_twd_refrigerators()
    await asyncio.sleep(3)  # Pause between retailers
    
    await analyze_homepro_refrigerators()
    
    logger.info("\n" + "="*60)
    logger.info("Analysis complete! Check the generated files:")
    logger.info("- *_raw_*.json: Raw Firecrawl response")
    logger.info("- *_content_*.md: Extracted markdown content")
    logger.info("- *_products_*.json: Parsed product information")
    logger.info("="*60)

if __name__ == "__main__":
    asyncio.run(main())