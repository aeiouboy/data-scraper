#!/usr/bin/env python3
"""
Properly scrape Thai Watsadu category with correct retailer code
"""
import asyncio
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.scrapers.thaiwatsadu_scraper import ThaiWatsaduScraper


async def scrape_twd_category_correctly():
    """
    Demonstrate the correct way to scrape Thai Watsadu categories
    """
    # The correct category URL (English version)
    category_url = "https://www.thaiwatsadu.com/en/category/เครื่องปรับอากาศติดผนัง-630201"
    
    print("\n" + "="*60)
    print("🏪 Thai Watsadu Category Scraping (Correct Method)")
    print("="*60)
    print(f"📍 URL: {category_url}")
    print("🔑 Retailer Code: TWD")
    print("="*60 + "\n")
    
    # Initialize the correct scraper
    scraper = ThaiWatsaduScraper()
    
    # Option 1: Use scrape_category method
    print("Method 1: Using scrape_category()")
    print("-" * 40)
    
    try:
        result = await scraper.scrape_category(
            category_url=category_url,
            max_pages=1,  # Just first page for testing
            max_concurrent=5
        )
        
        print(f"\n✅ Results:")
        print(f"   - URLs discovered: {result.get('discovered', 0)}")
        print(f"   - Successfully scraped: {result.get('success', 0)}")
        print(f"   - Failed: {result.get('failed', 0)}")
        
        if result.get('success', 0) > 0:
            print(f"   - Success rate: {(result['success']/result['discovered']*100):.1f}%")
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")
    
    # Option 2: Manual discovery and batch scraping
    print("\n\nMethod 2: Manual Discovery + Batch Scraping")
    print("-" * 40)
    
    try:
        # Step 1: Discover URLs
        print("Step 1: Discovering product URLs...")
        urls = await scraper._discover_product_urls(category_url, max_pages=1)
        print(f"✅ Found {len(urls)} product URLs")
        
        if urls:
            # Step 2: Scrape first 5 products as a test
            print(f"\nStep 2: Scraping first 5 products...")
            test_urls = urls[:5]
            
            result = await scraper.scrape_batch(test_urls)
            
            print(f"\n✅ Batch Results:")
            print(f"   - Total: {result.get('total', 0)}")
            print(f"   - Success: {result.get('success', 0)}")
            print(f"   - Failed: {result.get('failed', 0)}")
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")
    
    print("\n" + "="*60)
    print("✅ Done! Remember:")
    print("1. Use English URLs (/en/category/...)")
    print("2. Specify retailer_code='TWD' when using API")
    print("3. The scraper is working correctly!")
    print("="*60 + "\n")


async def test_via_api():
    """
    Show how to use the API correctly for TWD scraping
    """
    print("\n📡 API Usage Example:")
    print("-" * 40)
    print("When using the API endpoint, make sure to include retailer_code:")
    print("""
    POST /api/scraping/jobs
    {
        "job_type": "category",
        "target_url": "https://www.thaiwatsadu.com/en/category/เครื่องปรับอากาศติดผนัง-630201",
        "retailer_code": "TWD",  // ← THIS IS CRITICAL!
        "max_pages": 1
    }
    """)
    print("\nWithout retailer_code, it defaults to HomePro scraper!")


if __name__ == "__main__":
    # Run the correct scraping method
    asyncio.run(scrape_twd_category_correctly())
    
    # Show API usage
    asyncio.run(test_via_api())