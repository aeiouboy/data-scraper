#!/usr/bin/env python3
"""
Test Thai Watsadu scraper with direct category URL
"""
import asyncio
from src.scrapers.thaiwatsadu_scraper import ThaiWatsaduScraper
from src.services.supabase_service import SupabaseService
from src.services.firecrawl_client import FirecrawlClient

async def test_direct_category():
    """Test scraping with the exact category URL that has products"""
    
    print("\n=== Testing Thai Watsadu Direct Category ===\n")
    
    # Use the English category URL that we know has products
    category_url = "https://www.thaiwatsadu.com/en/category/เครื่องปรับอากาศติดผนัง-630201"
    
    # First, let's manually check what Firecrawl returns
    print("1. Manual Firecrawl test:")
    firecrawl = FirecrawlClient()
    result = await firecrawl.scrape(category_url)
    
    if result:
        links = result.get('linksOnPage', [])
        print(f"   Total links found: {len(links)}")
        
        # Count product links
        product_count = 0
        sample_urls = []
        
        for link in links:
            url = link.get('url', '') if isinstance(link, dict) else str(link)
            if any(pattern in url for pattern in ['/product/', '/th/product/', '/en/product/']):
                product_count += 1
                if len(sample_urls) < 5:
                    sample_urls.append(url)
        
        print(f"   Product links found: {product_count}")
        print(f"\n   Sample product URLs:")
        for i, url in enumerate(sample_urls, 1):
            print(f"   {i}. {url[:100]}...")
    
    # Now test with the actual scraper
    print("\n2. Testing with Thai Watsadu scraper:")
    scraper = ThaiWatsaduScraper()
    
    # Test discovery only
    print("\n   Testing URL discovery:")
    product_urls = await scraper._discover_product_urls(category_url, max_pages=1)
    print(f"   URLs discovered by scraper: {len(product_urls)}")
    
    if product_urls:
        print(f"\n   First 3 URLs discovered:")
        for i, url in enumerate(product_urls[:3], 1):
            print(f"   {i}. {url}")
    
    # Run full category scrape with just 1 page
    print("\n3. Running full category scrape (1 page only):")
    result = await scraper.scrape_category(category_url, max_pages=1)
    
    print("\n📊 Scraping Results:")
    print(f"   Discovered: {result.get('discovered', 0)} URLs")
    print(f"   Successfully scraped: {result.get('success', 0)}")
    print(f"   Failed: {result.get('failed', 0)}")
    
    return result

if __name__ == "__main__":
    asyncio.run(test_direct_category())