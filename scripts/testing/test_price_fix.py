#!/usr/bin/env python3
"""
Test the fixed HomePro price extraction
"""
import asyncio
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.scrapers.homepro_scraper import HomeProScraper

async def test_price_extraction():
    """Test the fixed price extraction on the specific URL"""
    
    test_url = "https://www.homepro.co.th/p/1294085"
    expected = {
        'original_price': 9990,
        'current_price': 8690,
        'discount': 1300,
        'name_should_contain': ['ทีวี', 'LED', '55', 'นิ้ว']
    }
    
    print(f"🧪 Testing fixed price extraction for: {test_url}")
    print("=" * 70)
    print(f"Expected results:")
    print(f"   Original price: ฿{expected['original_price']:,}")
    print(f"   Current price: ฿{expected['current_price']:,}")
    print(f"   Discount: ฿{expected['discount']:,}")
    print(f"   Name should contain: {expected['name_should_contain']}")
    print()
    
    try:
        # Create scraper with native strategy
        async with HomeProScraper(use_native=True) as scraper:
            print("🔍 Scraping product with fixed extraction logic...")
            
            # Scrape the product
            result = await scraper.scrape_single_product(test_url)
            
            if result:
                print("✅ Successfully scraped product!")
                print("📊 EXTRACTED DATA:")
                print("-" * 50)
                print(f"   Name: {result.get('name', 'N/A')}")
                print(f"   SKU: {result.get('sku', 'N/A')}")
                print(f"   Brand: {result.get('brand', 'N/A')}")
                print(f"   Current Price: ฿{result.get('current_price', 'N/A'):,}" if result.get('current_price') else "   Current Price: N/A")
                print(f"   Original Price: ฿{result.get('original_price', 'N/A'):,}" if result.get('original_price') else "   Original Price: N/A")
                print(f"   Discount %: {result.get('discount_percentage', 'N/A')}%" if result.get('discount_percentage') else "   Discount %: N/A")
                print(f"   Availability: {result.get('availability', 'N/A')}")
                print(f"   Strategy Used: {result.get('scrape_strategy', 'N/A')}")
                print()
                
                # Validate results
                print("🎯 VALIDATION RESULTS:")
                print("-" * 50)
                
                current_price = result.get('current_price')
                original_price = result.get('original_price')
                name = result.get('name', '')
                brand = result.get('brand', '')
                
                # Price validation
                if current_price == expected['current_price']:
                    print(f"   ✅ Current price correct: ฿{current_price:,}")
                else:
                    print(f"   ❌ Current price incorrect: ฿{current_price:,} (expected ฿{expected['current_price']:,})")
                
                if original_price == expected['original_price']:
                    print(f"   ✅ Original price correct: ฿{original_price:,}")
                else:
                    print(f"   ❌ Original price incorrect: ฿{original_price:,} (expected ฿{expected['original_price']:,})")
                
                # Discount validation
                if current_price and original_price:
                    actual_discount = original_price - current_price
                    if actual_discount == expected['discount']:
                        print(f"   ✅ Discount correct: ฿{actual_discount:,}")
                    else:
                        print(f"   ❌ Discount incorrect: ฿{actual_discount:,} (expected ฿{expected['discount']:,})")
                
                # Name validation
                name_valid = all(term in name for term in expected['name_should_contain'])
                if name_valid:
                    print(f"   ✅ Product name contains expected terms")
                else:
                    missing_terms = [term for term in expected['name_should_contain'] if term not in name]
                    print(f"   ❌ Product name missing terms: {missing_terms}")
                
                # Brand validation
                if brand and brand != 'LED':
                    print(f"   ✅ Brand extraction improved: '{brand}' (no longer 'LED')")
                else:
                    print(f"   ❌ Brand still incorrect: '{brand}'")
                
                print()
                if all([
                    current_price == expected['current_price'],
                    original_price == expected['original_price'],
                    name_valid,
                    brand and brand != 'LED'
                ]):
                    print("🎉 ALL TESTS PASSED! Price extraction fix is working correctly.")
                else:
                    print("⚠️  Some tests failed. Further fixes may be needed.")
                    
            else:
                print("❌ Failed to scrape product")
                return False
                
    except Exception as e:
        print(f"❌ Test failed with error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False
    
    return True

if __name__ == "__main__":
    success = asyncio.run(test_price_extraction())
    sys.exit(0 if success else 1)