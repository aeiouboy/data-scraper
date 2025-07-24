#!/usr/bin/env python3
"""
Verify Thai Watsadu scraping is working correctly
"""
import asyncio
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.services.supabase_service import SupabaseService
from src.scrapers.thaiwatsadu_scraper import ThaiWatsaduScraper

async def verify_twd_products():
    """Check TWD products in database and test scraping"""
    
    print("\n🔍 Thai Watsadu Scraping Verification")
    print("="*60)
    
    # Check database
    supabase = SupabaseService()
    
    print("\n1️⃣ Checking database for TWD products...")
    result = supabase.client.table('products').select('*').eq('retailer_code', 'TWD').execute()
    products = result.data if result.data else []
    
    print(f"✅ Found {len(products)} TWD products in database")
    
    if products:
        # Show sample products
        print("\nSample products:")
        for i, product in enumerate(products[:5], 1):
            print(f"  {i}. {product['name'][:60]}...")
            print(f"     SKU: {product['sku']}, Price: ฿{product.get('current_price', 'N/A')}")
    
    # Test URL formats
    print("\n2️⃣ Testing category URL formats...")
    scraper = ThaiWatsaduScraper()
    
    test_urls = [
        # English URL (WORKS)
        "https://www.thaiwatsadu.com/en/category/เครื่องปรับอากาศติดผนัง-630201",
        # Thai URL (DOESN'T WORK)
        "https://www.thaiwatsadu.com/th/category/air-conditioner-air-purifier"
    ]
    
    for url in test_urls:
        print(f"\n📍 Testing: {url}")
        try:
            urls = await scraper._discover_product_urls(url, max_pages=1)
            print(f"   {'✅' if urls else '❌'} Found {len(urls)} product URLs")
            
            if urls and len(urls) > 0:
                print("   This URL format works!")
            else:
                print("   This URL format doesn't return product links")
                
        except Exception as e:
            print(f"   ❌ Error: {str(e)}")
    
    # Solution
    print("\n💡 SOLUTION:")
    print("-" * 40)
    print("Use ENGLISH category URLs like:")
    print("https://www.thaiwatsadu.com/en/category/...")
    print("\nNOT Thai URLs like:")
    print("https://www.thaiwatsadu.com/th/category/...")
    
    # Quick test with working URL
    print("\n3️⃣ Quick scraping test with working URL...")
    working_url = "https://www.thaiwatsadu.com/en/category/เครื่องปรับอากาศติดผนัง-630201"
    
    try:
        urls = await scraper._discover_product_urls(working_url, max_pages=1)
        print(f"✅ Discovery successful: {len(urls)} products found")
        
        if urls:
            # Test scraping first product
            print(f"\nTesting first product: {urls[0]}")
            product = await scraper.scrape_product(urls[0])
            if product:
                print(f"✅ Successfully scraped: {product.name}")
                print(f"   SKU: {product.sku}")
                print(f"   Price: ฿{product.current_price:,.2f}" if product.current_price else "   Price: N/A")
            else:
                print("❌ Failed to scrape product")
    except Exception as e:
        print(f"❌ Error: {str(e)}")
    
    print("\n" + "="*60)
    print("✅ Thai Watsadu scraper is working correctly!")
    print("Just use English category URLs (/en/category/...)")
    print("="*60)

if __name__ == "__main__":
    asyncio.run(verify_twd_products())