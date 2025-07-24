#!/usr/bin/env python3
"""
Debug URL discovery to see what's happening
"""
import asyncio
import logging
from src.scrapers.homepro_scraper import HomeProScraper

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

async def debug_url_discovery():
    """Debug URL discovery issues"""
    
    print("🔍 Debugging URL Discovery")
    print("=" * 40)
    
    try:
        async with HomeProScraper(use_native=True) as scraper:
            print("✅ HomePro scraper initialized")
            
            # Test URL discovery on a simple category
            test_url = "https://www.homepro.co.th/c/LIG"
            print(f"\n🔗 Testing URL discovery: {test_url}")
            
            urls = await scraper.discover_product_urls(test_url, max_pages=1)
            
            print(f"📊 Results:")
            print(f"   - URLs discovered: {len(urls)}")
            
            if urls:
                print(f"   - Sample URLs:")
                for i, url in enumerate(urls[:5]):
                    print(f"     {i+1}. {url}")
                if len(urls) > 5:
                    print(f"     ... and {len(urls) - 5} more")
            else:
                print("   ❌ No URLs discovered")
                
            return urls
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return []

if __name__ == "__main__":
    asyncio.run(debug_url_discovery())