#!/usr/bin/env python3
"""
Debug why TWD scraper finds 0 URLs when analysis shows 48
"""
import asyncio
from src.scrapers.thaiwatsadu_scraper import ThaiWatsaduScraper
from src.services.firecrawl_client import FirecrawlClient

async def debug_url_discovery():
    """Debug the URL discovery process step by step"""
    
    print("\n=== Debugging TWD URL Discovery ===\n")
    
    # Test URLs
    test_urls = [
        "https://www.thaiwatsadu.com/th/category/air-conditioner-air-purifier",  # Original Thai path
        "https://www.thaiwatsadu.com/en/category/เครื่องปรับอากาศติดผนัง-630201"  # English path that works
    ]
    
    scraper = ThaiWatsaduScraper()
    firecrawl = FirecrawlClient()
    
    for test_url in test_urls:
        print(f"\nTesting URL: {test_url}")
        print("-" * 80)
        
        # Get raw Firecrawl result
        print("1. Raw Firecrawl result:")
        result = await firecrawl.scrape(test_url)
        
        if result:
            # Check what's in the result
            print(f"   - Has 'linksOnPage': {'linksOnPage' in result}")
            print(f"   - Has 'links': {'links' in result}")
            
            links = result.get('linksOnPage', result.get('links', []))
            print(f"   - Total links: {len(links)}")
            
            # Check link format
            if links:
                first_link = links[0]
                print(f"   - First link type: {type(first_link)}")
                if isinstance(first_link, dict):
                    print(f"   - First link keys: {list(first_link.keys())}")
                    print(f"   - Sample: {first_link}")
            
            # Count product URLs manually
            product_count = 0
            for link in links:
                url = ""
                if isinstance(link, dict):
                    url = link.get('url', link.get('href', ''))
                else:
                    url = str(link)
                
                # Check all patterns
                if '/product/' in url or '/th/product/' in url or '/en/product/' in url:
                    product_count += 1
                    if product_count <= 3:
                        print(f"   - Product URL {product_count}: {url[:80]}...")
            
            print(f"\n   Total product URLs found: {product_count}")
        else:
            print("   ❌ Failed to get Firecrawl result")
        
        # Test scraper's discovery method
        print("\n2. Scraper's _discover_product_urls method:")
        try:
            urls = await scraper._discover_product_urls(test_url, max_pages=1)
            print(f"   - URLs discovered: {len(urls)}")
            if urls:
                print(f"   - First URL: {urls[0]}")
        except Exception as e:
            print(f"   - Error: {str(e)}")
        
        print("\n" + "="*80)

if __name__ == "__main__":
    asyncio.run(debug_url_discovery())