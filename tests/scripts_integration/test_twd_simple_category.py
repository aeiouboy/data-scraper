#!/usr/bin/env python3
"""
Simple test to verify Thai Watsadu category scraping
"""
import asyncio
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.scrapers.thaiwatsadu_scraper import ThaiWatsaduScraper


async def test_simple_category():
    """Test category scraping with minimal configuration"""
    scraper = ThaiWatsaduScraper()
    category_url = "https://www.thaiwatsadu.com/en/category/เครื่องปรับอากาศติดผนัง-630201"
    
    print("Testing Thai Watsadu Category Scraping")
    print("="*60)
    print(f"URL: {category_url}")
    print()
    
    # First, test URL discovery only
    print("1. Testing URL Discovery...")
    urls = await scraper._discover_product_urls(category_url, max_pages=1)
    print(f"   Found {len(urls)} product URLs")
    
    if urls:
        print(f"   First URL: {urls[0]}")
        print()
        
        # Test scraping just the first product
        print("2. Testing Single Product Scrape...")
        product = await scraper.scrape_product(urls[0])
        
        if product:
            print(f"   ✓ Successfully scraped: {product.name}")
            print(f"   SKU: {product.sku}")
            print(f"   Price: {product.current_price}")
        else:
            print("   ✗ Failed to scrape product")
        
        print()
        
        # Now test the full category scrape with just 1 page and 3 products
        print("3. Testing Category Scrape (limited)...")
        result = await scraper.scrape_category(
            category_url=category_url,
            max_pages=1,
            max_concurrent=1
        )
        
        print(f"\n   Category Scrape Results:")
        print(f"   - Discovered: {result.get('discovered', 0)}")
        print(f"   - Success: {result.get('success', 0)}")
        print(f"   - Failed: {result.get('failed', 0)}")
        
        if result.get('discovered', 0) == 1:
            print("\n   ⚠️  ISSUE FOUND: Only 1 product discovered!")
            print("   This explains why the user sees 'only finding 1 product'")
        
    else:
        print("   ✗ No URLs discovered!")


if __name__ == "__main__":
    asyncio.run(test_simple_category())