#!/usr/bin/env python3
"""
Test complete TWD scraping flow and verify results
"""
import asyncio
from src.scrapers.thaiwatsadu_scraper import ThaiWatsaduScraper
from src.services.supabase_service import SupabaseService

async def test_complete_flow():
    """Test the complete scraping flow"""
    
    scraper = ThaiWatsaduScraper()
    supabase = SupabaseService()
    
    print("\n=== Testing Thai Watsadu Complete Scraping Flow ===\n")
    
    # 1. Check initial count
    print("1. Initial TWD product count:")
    initial_response = supabase.client.table('products').select('id', count='exact').eq('retailer_code', 'TWD').execute()
    initial_count = initial_response.count
    print(f"   Products in database: {initial_count}")
    
    # 2. Test category scraping with small limit
    category_url = "https://www.thaiwatsadu.com/th/category/air-conditioner-air-purifier"
    print(f"\n2. Testing category scraping:")
    print(f"   Category: {category_url}")
    print(f"   Limiting to 1 page, max 5 products\n")
    
    # Run scraper
    result = await scraper.scrape_category(category_url, max_pages=1)
    
    # 3. Display scraper results
    print("\n3. Scraper Results:")
    print(f"   Discovered URLs: {result.get('discovered', 0)}")
    print(f"   Successfully scraped: {result.get('success', 0)}")
    print(f"   Failed: {result.get('failed', 0)}")
    print(f"   Error: {result.get('error', 'None')}")
    
    # 4. Check final count
    print("\n4. Final TWD product count:")
    final_response = supabase.client.table('products').select('id', count='exact').eq('retailer_code', 'TWD').execute()
    final_count = final_response.count
    print(f"   Products in database: {final_count}")
    print(f"   New products added: {final_count - initial_count}")
    
    # 5. Show recent products
    print("\n5. Recent TWD products (last 5):")
    recent = supabase.client.table('products').select('*').eq('retailer_code', 'TWD').order('scraped_at', desc=True).limit(5).execute()
    
    for i, product in enumerate(recent.data, 1):
        print(f"   {i}. {product['name'][:50]}...")
        print(f"      SKU: {product['sku']} | Price: {product.get('current_price', 'No price')}")
    
    # 6. Verify discrepancy
    print("\n6. Analysis:")
    if result.get('discovered', 0) > result.get('success', 0):
        print(f"   ⚠️  Discrepancy found:")
        print(f"      - Discovered: {result.get('discovered', 0)} URLs")
        print(f"      - Successfully scraped: {result.get('success', 0)}")
        print(f"      - This means {result.get('discovered', 0) - result.get('success', 0)} products failed to scrape or save")
    else:
        print(f"   ✅ All discovered products were successfully scraped and saved")
    
    return result

if __name__ == "__main__":
    asyncio.run(test_complete_flow())