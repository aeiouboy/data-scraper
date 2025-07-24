#!/usr/bin/env python3
"""
Quick test script for HomePro scraper
"""
import asyncio
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent))

from src.core.scraper import HomeProScraper
from src.services.supabase_service import SupabaseService


async def test_basic_functionality():
    """Test basic scraper functionality"""
    print("🧪 HomePro Scraper Test Suite")
    print("=" * 50)
    
    # Test 1: Database Connection
    print("\n1️⃣ Testing Supabase connection...")
    try:
        service = SupabaseService()
        stats = await service.get_product_stats()
        print("✅ Supabase connected successfully")
    except Exception as e:
        print(f"❌ Supabase error: {str(e)}")
        return
    
    # Test 2: Scraper Initialization
    print("\n2️⃣ Initializing scraper...")
    try:
        scraper = HomeProScraper()
        print("✅ Scraper initialized")
    except Exception as e:
        print(f"❌ Scraper initialization error: {str(e)}")
        return
    
    # Test 3: URL Discovery (lightweight test)
    print("\n3️⃣ Testing URL discovery...")
    test_category = "https://www.homepro.co.th/c/tools"
    try:
        urls = await scraper.discover_product_urls(test_category, max_pages=1)
        if urls:
            print(f"✅ Discovered {len(urls)} product URLs")
            print(f"   Sample: {urls[0] if urls else 'None'}")
        else:
            print("⚠️  No URLs discovered (category might be empty)")
    except Exception as e:
        print(f"❌ Discovery error: {str(e)}")
    
    # Test 4: Single Product Scrape
    print("\n4️⃣ Testing single product scrape...")
    # Use a sample product URL - replace with actual HomePro product
    test_product = "https://www.homepro.co.th/p/1001234567"
    try:
        print(f"   Scraping: {test_product}")
        result = await scraper.scrape_single_product(test_product)
        if result:
            print(f"✅ Successfully scraped: {result.get('name', 'Unknown')}")
            print(f"   SKU: {result.get('sku')}")
            print(f"   Price: ฿{result.get('current_price', 'N/A')}")
        else:
            print("⚠️  No data returned (product might not exist)")
    except Exception as e:
        print(f"❌ Scraping error: {str(e)}")
    
    # Test 5: Statistics
    print("\n5️⃣ Testing statistics...")
    try:
        stats = await scraper.get_scraping_stats()
        if stats['products']:
            print("✅ Statistics retrieved:")
            print(f"   Total products: {stats['products'].get('total_products', 0)}")
        else:
            print("ℹ️  No statistics available yet")
    except Exception as e:
        print(f"❌ Statistics error: {str(e)}")
    
    print("\n" + "=" * 50)
    print("🏁 Test suite completed!")


if __name__ == "__main__":
    print("Starting tests...")
    asyncio.run(test_basic_functionality())