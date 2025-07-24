#!/usr/bin/env python3
"""
Fix HomePro scraping issues - correct price and brand extraction
Based on the example: https://www.homepro.co.th/p/1294085
Expected: Original price = 9990, Sale price = 8690, Discount = 1300
"""
import asyncio
import aiohttp
from bs4 import BeautifulSoup
import re
from typing import Dict, Any, Optional

async def analyze_homepro_page():
    """Analyze the HomePro page structure to identify correct selectors"""
    
    url = "https://www.homepro.co.th/p/1294085"
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
        'Accept-Language': 'th-TH,th;q=0.9,en-US;q=0.8,en;q=0.7',
        'Accept-Encoding': 'gzip, deflate, br',
        'Connection': 'keep-alive',
    }
    
    print(f"🔍 Analyzing HomePro page: {url}")
    print("=" * 60)
    
    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=headers) as response:
            if response.status != 200:
                print(f"❌ Failed to fetch page: HTTP {response.status}")
                return
            
            content = await response.text()
            soup = BeautifulSoup(content, 'html.parser')
            
            print("📋 PAGE ANALYSIS RESULTS:")
            print("-" * 40)
            
            # 1. Product Name Analysis
            print("1. PRODUCT NAME:")
            name_candidates = [
                ('h1', soup.find('h1')),
                ('title tag', soup.find('title')),
                ('.product-title', soup.select_one('.product-title')),
                ('[data-testid*="title"]', soup.select_one('[data-testid*="title"]')),
                ('.pdp-title', soup.select_one('.pdp-title')),
                ('h1[class*="title"]', soup.select_one('h1[class*="title"]')),
            ]
            
            for selector, element in name_candidates:
                if element:
                    text = element.get_text(strip=True)
                    print(f"   {selector}: {text[:80]}...")
            
            # 2. Price Analysis
            print("\n2. PRICE ANALYSIS:")
            print("   Looking for price patterns...")
            
            # Search for all elements containing price-like text
            price_patterns = [
                r'฿\s*([0-9,]+)',
                r'([0-9,]+)\s*บาท',
                r'([0-9,]+)\s*฿',
                r'price["\']:\s*["\']?([0-9,]+)',
                r'"price":\s*([0-9,]+)',
            ]
            
            all_text = soup.get_text()
            found_prices = []
            
            for pattern in price_patterns:
                matches = re.findall(pattern, all_text)
                for match in matches:
                    try:
                        price_num = float(match.replace(',', ''))
                        if 1000 <= price_num <= 100000:  # Reasonable price range
                            found_prices.append((pattern, price_num))
                    except ValueError:
                        continue
            
            print(f"   Found {len(found_prices)} potential prices:")
            for pattern, price in found_prices[:10]:  # Show first 10
                print(f"   - ฿{price:,.0f} (pattern: {pattern[:30]}...)")
            
            # 3. Specific Element Analysis
            print("\n3. SPECIFIC ELEMENTS:")
            
            # Check for common e-commerce selectors
            selectors_to_check = [
                '.price',
                '.current-price', 
                '.sale-price',
                '.original-price',
                '.regular-price',
                '.product-price',
                '[data-testid*="price"]',
                '[class*="price"]',
                '.price-current',
                '.price-wrapper',
                '.price-box',
                '.price-info',
            ]
            
            for selector in selectors_to_check:
                elements = soup.select(selector)
                if elements:
                    print(f"   {selector}: {len(elements)} elements found")
                    for i, elem in enumerate(elements[:3]):  # Show first 3
                        text = elem.get_text(strip=True)
                        if text:
                            print(f"     [{i+1}] {text[:50]}")
            
            # 4. Script Tag Analysis (for JSON data)
            print("\n4. SCRIPT TAG ANALYSIS:")
            scripts = soup.find_all('script')
            
            for i, script in enumerate(scripts):
                if script.string and ('price' in script.string.lower() or 'product' in script.string.lower()):
                    content = script.string[:200]
                    print(f"   Script {i+1}: {content}...")
                    
                    # Look for JSON with price data
                    json_patterns = [
                        r'"price":\s*([0-9,]+)',
                        r'"currentPrice":\s*([0-9,]+)',
                        r'"salePrice":\s*([0-9,]+)',
                        r'"regularPrice":\s*([0-9,]+)',
                        r'"originalPrice":\s*([0-9,]+)',
                    ]
                    
                    for pattern in json_patterns:
                        matches = re.findall(pattern, script.string)
                        if matches:
                            print(f"     Found JSON price: {pattern} -> {matches}")
            
            # 5. Brand Analysis
            print("\n5. BRAND ANALYSIS:")
            brand_candidates = [
                ('.brand', soup.select_one('.brand')),
                ('.brand-name', soup.select_one('.brand-name')),
                ('.manufacturer', soup.select_one('.manufacturer')),
                ('[data-brand]', soup.select_one('[data-brand]')),
                ('[class*="brand"]', soup.select_one('[class*="brand"]')),
            ]
            
            for selector, element in brand_candidates:
                if element:
                    text = element.get_text(strip=True)
                    print(f"   {selector}: {text}")
            
            # 6. Meta tag analysis
            print("\n6. META TAG ANALYSIS:")
            meta_tags = soup.find_all('meta')
            for meta in meta_tags:
                if meta.get('property') or meta.get('name'):
                    prop = meta.get('property') or meta.get('name')
                    content = meta.get('content', '')
                    if 'price' in prop.lower() or 'product' in prop.lower():
                        print(f"   {prop}: {content}")

def create_improved_selectors():
    """Create improved selectors based on analysis"""
    
    print("\n" + "=" * 60)
    print("🔧 IMPROVED SELECTOR RECOMMENDATIONS:")
    print("=" * 60)
    
    improved_selectors = {
        'name': [
            'h1',  # Most common
            '.product-title',
            '[data-testid*="title"]',
            '.pdp-title',
            'title',  # Fallback
        ],
        'current_price': [
            '[data-testid*="price"]',
            '.sale-price',
            '.current-price', 
            '.price-current',
            '.final-price',
            '.price:not(.original-price)',
        ],
        'original_price': [
            '.original-price',
            '.regular-price', 
            '.list-price',
            '.was-price',
            '.price-before',
        ],
        'brand': [
            '[data-brand]',
            '.brand-name',
            '.brand', 
            '.manufacturer',
            '[class*="brand"]',
        ],
        'availability': [
            '.stock-status',
            '.availability',
            '[data-testid*="stock"]',
            '.inventory-status',
        ]
    }
    
    for field, selectors in improved_selectors.items():
        print(f"\n{field.upper()}:")
        for selector in selectors:
            print(f"   - {selector}")
    
    return improved_selectors

async def test_extraction():
    """Test the extraction with improved logic"""
    
    print("\n" + "=" * 60)
    print("🧪 TESTING IMPROVED EXTRACTION:")
    print("=" * 60)
    
    # Expected values for validation
    expected = {
        'original_price': 9990,
        'sale_price': 8690,
        'discount': 1300,
        'name_contains': ['ทีวี', 'LED', '55', 'นิ้ว'],
    }
    
    print("Expected values:")
    print(f"   Original price: ฿{expected['original_price']:,}")
    print(f"   Sale price: ฿{expected['sale_price']:,}")
    print(f"   Discount: ฿{expected['discount']:,}")
    print(f"   Name should contain: {expected['name_contains']}")
    
    print("\n⚠️  Current extraction shows:")
    print("   Price: ฿None")
    print("   Brand: LED (incorrect)")
    print("   Name: ทีวีแอลอีดี 55 นิ้ว NANO (4K, LED, GOOGLE TV) 55NUD9900N")
    
    print("\n🎯 Issues to fix:")
    print("   1. Price extraction selectors not working")
    print("   2. Brand extraction getting wrong data") 
    print("   3. Missing original price vs sale price logic")
    print("   4. No discount calculation")
    
async def main():
    """Main function to analyze and provide fixes"""
    try:
        await analyze_homepro_page()
        create_improved_selectors()
        await test_extraction()
        
        print("\n" + "=" * 60)
        print("✅ ANALYSIS COMPLETE!")
        print("📋 Next steps:")
        print("   1. Update native_strategy.py _extract_product_data() method")
        print("   2. Add original price vs sale price detection")
        print("   3. Implement discount calculation")
        print("   4. Test with the specific URL")
        print("=" * 60)
        
    except Exception as e:
        print(f"❌ Analysis failed: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())