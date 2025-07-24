#!/usr/bin/env python3
"""
Test Thai Watsadu category scraping to debug why only 1 product is found
"""
import asyncio
from src.scrapers.thaiwatsadu_scraper import ThaiWatsaduScraper

async def test_category_scraping():
    """Test scraping the Thai Watsadu air conditioner category"""
    scraper = ThaiWatsaduScraper()
    category_url = "https://www.thaiwatsadu.com/en/category/เครื่องปรับอากาศติดผนัง-630201"
    
    print("Testing Thai Watsadu Category Scraping")
    print("=" * 60)
    print(f"Category URL: {category_url}")
    print()
    
    try:
        # Test with limited pages first
        result = await scraper.scrape_category(
            category_url=category_url,
            max_pages=1,  # Start with just 1 page
            max_concurrent=1
        )
        
        print("\nResults:")
        print(f"- Discovered: {result.get('discovered', 0)} products")
        print(f"- Success: {result.get('success', 0)} products")
        print(f"- Failed: {result.get('failed', 0)} products")
        
        if 'error' in result:
            print(f"- Error: {result['error']}")
        
        # Also test the discovery method directly
        print("\n" + "="*60)
        print("Testing _discover_product_urls directly...")
        print("="*60)
        
        urls = await scraper._discover_product_urls(category_url, max_pages=1)
        print(f"\nDirect discovery found {len(urls)} product URLs")
        
        if urls:
            print("\nFirst 5 URLs:")
            for i, url in enumerate(urls[:5], 1):
                print(f"{i}. {url}")
        
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_category_scraping())