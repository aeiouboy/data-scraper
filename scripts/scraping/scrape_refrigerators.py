#!/usr/bin/env python3
"""
Scrape refrigerator categories from Thai Watsadu and HomePro
"""

import asyncio
import json
import logging
from datetime import datetime
from typing import List, Dict, Any

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent))

from src.services.firecrawl_client import FirecrawlClient
from src.services.supabase_service import SupabaseService
from src.core.multi_retailer_manager import MultiRetailerManager

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
        "category": "Refrigerators",
        "url": "https://www.thaiwatsadu.com/en/category/%E0%B8%95%E0%B8%B9%E0%B9%89%E0%B9%80%E0%B8%A2%E0%B9%87%E0%B8%99-630301",
        "thai_name": "ตู้เย็น"
    },
    {
        "retailer": "HP",
        "category": "Refrigerators",
        "url": "https://www.homepro.co.th/c/APP09",
        "thai_name": "ตู้เย็น"
    }
]

async def scrape_category_with_firecrawl(url: str, retailer: str) -> Dict[str, Any]:
    """Scrape a category page using Firecrawl"""
    client = FirecrawlClient()
    
    try:
        logger.info(f"Scraping {retailer} category: {url}")
        
        # Use Firecrawl to scrape the page
        result = await client.scrape_url(
            url,
            options={
                "formats": ["markdown", "html"],
                "waitFor": 3000,
                "screenshot": False,
                "onlyMainContent": True
            }
        )
        
        if result and result.get("success"):
            logger.info(f"Successfully scraped {retailer} category page")
            return result
        else:
            logger.error(f"Failed to scrape {retailer}: {result}")
            return None
            
    except Exception as e:
        logger.error(f"Error scraping {retailer}: {str(e)}")
        return None

async def extract_products_from_page(scraped_data: Dict[str, Any], retailer: str) -> List[Dict[str, Any]]:
    """Extract product information from scraped page data"""
    products = []
    
    try:
        markdown_content = scraped_data.get("markdown", "")
        
        if retailer == "TWD":
            # Thai Watsadu specific extraction
            logger.info("Extracting products from Thai Watsadu page")
            
            # Look for product patterns in markdown
            lines = markdown_content.split('\n')
            current_product = {}
            
            for line in lines:
                line = line.strip()
                
                # Look for price patterns (฿ followed by numbers)
                if '฿' in line:
                    import re
                    price_match = re.search(r'฿[\s]*([\d,]+(?:\.\d{2})?)', line)
                    if price_match:
                        current_product['price'] = float(price_match.group(1).replace(',', ''))
                
                # Look for product links
                if '/product/' in line:
                    url_match = re.search(r'https?://[^\s\)]+/product/[^\s\)]+', line)
                    if url_match:
                        current_product['url'] = url_match.group(0)
                
                # Look for product names (usually before price or in links)
                if current_product.get('price') and not current_product.get('name'):
                    # Extract text before price
                    name_match = re.search(r'^(.*?)(?:\s*฿)', line)
                    if name_match:
                        current_product['name'] = name_match.group(1).strip()
                
                # If we have a complete product, add it
                if current_product.get('name') and current_product.get('price'):
                    current_product['retailer'] = retailer
                    current_product['category'] = 'Refrigerators'
                    products.append(current_product)
                    current_product = {}
                    
        elif retailer == "HP":
            # HomePro specific extraction
            logger.info("Extracting products from HomePro page")
            
            # Similar extraction logic for HomePro
            lines = markdown_content.split('\n')
            current_product = {}
            
            for line in lines:
                line = line.strip()
                
                # HomePro price format
                if '฿' in line or 'THB' in line:
                    import re
                    price_match = re.search(r'(?:฿|THB)\s*([\d,]+(?:\.\d{2})?)', line)
                    if price_match:
                        current_product['price'] = float(price_match.group(1).replace(',', ''))
                
                # Look for product URLs
                if '/p/' in line:
                    url_match = re.search(r'https?://[^\s\)]+/p/[^\s\)]+', line)
                    if url_match:
                        current_product['url'] = url_match.group(0)
                
                # Product names often appear before prices
                if current_product.get('price') and not current_product.get('name'):
                    name_match = re.search(r'^(.*?)(?:\s*(?:฿|THB))', line)
                    if name_match:
                        current_product['name'] = name_match.group(1).strip()
                
                if current_product.get('name') and current_product.get('price'):
                    current_product['retailer'] = retailer
                    current_product['category'] = 'Refrigerators'
                    products.append(current_product)
                    current_product = {}
        
        logger.info(f"Extracted {len(products)} products from {retailer}")
        return products
        
    except Exception as e:
        logger.error(f"Error extracting products from {retailer}: {str(e)}")
        return []

async def save_scraped_data(category_info: Dict[str, Any], scraped_data: Dict[str, Any], products: List[Dict[str, Any]]):
    """Save scraped data to files for analysis"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    retailer = category_info['retailer']
    
    # Save raw scraped data
    raw_filename = f"{retailer.lower()}_refrigerators_raw_{timestamp}.json"
    with open(raw_filename, 'w', encoding='utf-8') as f:
        json.dump(scraped_data, f, ensure_ascii=False, indent=2)
    logger.info(f"Saved raw data to {raw_filename}")
    
    # Save extracted products
    products_filename = f"{retailer.lower()}_refrigerators_products_{timestamp}.json"
    with open(products_filename, 'w', encoding='utf-8') as f:
        json.dump({
            "category": category_info,
            "products_count": len(products),
            "products": products
        }, f, ensure_ascii=False, indent=2)
    logger.info(f"Saved {len(products)} products to {products_filename}")
    
    # Save markdown content separately for easy viewing
    if scraped_data.get("markdown"):
        markdown_filename = f"{retailer.lower()}_refrigerators_content_{timestamp}.md"
        with open(markdown_filename, 'w', encoding='utf-8') as f:
            f.write(scraped_data["markdown"])
        logger.info(f"Saved markdown content to {markdown_filename}")

async def scrape_with_manager(category_info: Dict[str, Any]):
    """Use MultiRetailerManager to scrape category"""
    manager = MultiRetailerManager()
    
    try:
        logger.info(f"\n{'='*60}")
        logger.info(f"Scraping {category_info['retailer']} - {category_info['category']}")
        logger.info(f"URL: {category_info['url']}")
        logger.info(f"{'='*60}")
        
        # Scrape the category
        products = await manager.scrape_category(
            retailer_code=category_info['retailer'],
            category_url=category_info['url'],
            category_name=category_info['category']
        )
        
        logger.info(f"\nScraped {len(products)} products from {category_info['retailer']}")
        
        # Save summary
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        summary_filename = f"{category_info['retailer'].lower()}_refrigerators_summary_{timestamp}.json"
        
        with open(summary_filename, 'w', encoding='utf-8') as f:
            json.dump({
                "category": category_info,
                "scraped_at": timestamp,
                "total_products": len(products),
                "sample_products": products[:5] if products else [],
                "unique_brands": list(set(p.get('brand', 'Unknown') for p in products if p.get('brand')))
            }, f, ensure_ascii=False, indent=2)
        
        logger.info(f"Saved summary to {summary_filename}")
        
        return products
        
    except Exception as e:
        logger.error(f"Error with manager scraping: {str(e)}")
        return []

async def main():
    """Main function to scrape refrigerator categories"""
    logger.info("Starting refrigerator category scraping")
    
    # First, let's try with Firecrawl directly to see the structure
    for category in CATEGORIES:
        try:
            # Method 1: Direct Firecrawl scraping for analysis
            scraped_data = await scrape_category_with_firecrawl(category['url'], category['retailer'])
            
            if scraped_data:
                # Extract products from the scraped data
                products = await extract_products_from_page(scraped_data, category['retailer'])
                
                # Save the data for analysis
                await save_scraped_data(category, scraped_data, products)
            
            # Method 2: Use MultiRetailerManager for proper scraping
            await scrape_with_manager(category)
            
            # Add delay between retailers
            await asyncio.sleep(5)
            
        except Exception as e:
            logger.error(f"Error scraping {category['retailer']}: {str(e)}")
            continue
    
    logger.info("\nRefrigerator scraping completed!")
    logger.info("Check the generated JSON and markdown files for results")

if __name__ == "__main__":
    asyncio.run(main())