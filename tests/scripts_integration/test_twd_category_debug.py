#!/usr/bin/env python3
"""
Simple debug script for Thai Watsadu category scraping issue
"""
import asyncio
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def debug_twd_category():
    """Debug why only 1 product is found"""
    from src.scrapers.thaiwatsadu_scraper import ThaiWatsaduScraper
    from src.services.firecrawl_client import FirecrawlClient
    
    category_url = "https://www.thaiwatsadu.com/en/category/เครื่องปรับอากาศติดผนัง-630201"
    
    print("\n🔍 Thai Watsadu Category Debug")
    print("="*60)
    print(f"URL: {category_url}\n")
    
    # Step 1: Check Firecrawl response
    print("Step 1: Checking Firecrawl response...")
    firecrawl = FirecrawlClient()
    
    try:
        result = await firecrawl.scrape(category_url)
        if result:
            # Check different link formats
            links = result.get('linksOnPage', result.get('links', []))
            print(f"✅ Total links found: {len(links)}")
            
            # Count product links
            product_links = []
            for link in links:
                url = link if isinstance(link, str) else link.get('url', link.get('href', ''))
                if '/product/' in url:
                    product_links.append(url)
            
            print(f"✅ Product links found: {len(product_links)}")
            if product_links:
                print("\nFirst 5 product URLs:")
                for i, url in enumerate(product_links[:5], 1):
                    print(f"  {i}. {url}")
        else:
            print("❌ No result from Firecrawl")
    except Exception as e:
        print(f"❌ Firecrawl error: {str(e)}")
    
    # Step 2: Test the scraper's URL discovery
    print("\n\nStep 2: Testing scraper's URL discovery...")
    scraper = ThaiWatsaduScraper()
    
    try:
        urls = await scraper._discover_product_urls(category_url, max_pages=1)
        print(f"✅ Scraper discovered: {len(urls)} URLs")
        
        if urls:
            print("\nFirst 5 discovered URLs:")
            for i, url in enumerate(urls[:5], 1):
                print(f"  {i}. {url}")
    except Exception as e:
        print(f"❌ Discovery error: {str(e)}")
    
    # Step 3: Test category scraping
    print("\n\nStep 3: Testing category scraping...")
    try:
        result = await scraper.scrape_category(category_url, max_pages=1)
        print(f"\nCategory scraping result:")
        print(f"  - Discovered: {result.get('discovered', 0)}")
        print(f"  - Success: {result.get('success', 0)}")
        print(f"  - Failed: {result.get('failed', 0)}")
        
        if result.get('error'):
            print(f"  - Error: {result['error']}")
    except Exception as e:
        print(f"❌ Category scraping error: {str(e)}")
    
    print("\n" + "="*60)

if __name__ == "__main__":
    asyncio.run(debug_twd_category())