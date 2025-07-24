#!/usr/bin/env python3
"""
Debug specific TWD product price extraction
"""

import requests
from bs4 import BeautifulSoup
import json
import re
from src.services.supabase_service import SupabaseService
from src.scrapers.strategies.improved_native_strategy import ImprovedNativeStrategy

def debug_twd_product():
    """Debug specific TWD product: TWD-82666F68"""
    
    sku = "TWD-82666F68"
    url = "https://www.thaiwatsadu.com/en/product/%E0%B8%A5%E0%B8%B3%E0%B9%82%E0%B8%9E%E0%B8%87%E0%B8%9A%E0%B8%A5%E0%B8%B9%E0%B8%97%E0%B8%B9%E0%B8%98-8--4-%E0%B8%99%E0%B8%B4%E0%B9%89%E0%B8%A7-ZAGIO-%E0%B8%A3%E0%B8%B8%E0%B9%88%E0%B8%99-ZG-8557-%E0%B8%81%E0%B8%B3%E0%B8%A5%E0%B8%B1%E0%B8%87-24--3-%E0%B8%A7%E0%B8%B1%E0%B8%95%E0%B8%95%E0%B9%8C-%E0%B8%AA%E0%B8%B5%E0%B8%94%E0%B8%B3-60288535"
    
    print(f"🔍 DEBUGGING TWD PRODUCT: {sku}")
    print(f"🔗 URL: {url}")
    print("=" * 80)
    
    # Get current database data
    supabase = SupabaseService()
    result = supabase.client.table('products').select('*').eq('sku', sku).execute()
    
    if result.data:
        current_product = result.data[0]
        print(f"\n📊 CURRENT DATABASE DATA:")
        print(f"  SKU: {current_product.get('sku')}")
        print(f"  Name: {current_product.get('name')}")
        print(f"  Brand: {current_product.get('brand')}")
        print(f"  Category: {current_product.get('category')}")
        print(f"  Current Price: {current_product.get('current_price')}")
        print(f"  Original Price: {current_product.get('original_price')}")
        print(f"  URL: {current_product.get('url')}")
    else:
        print(f"❌ Product {sku} not found in database")
        return
    
    # Fetch the webpage
    print(f"\n🌐 FETCHING WEBPAGE...")
    try:
        response = requests.get(url, timeout=30)
        print(f"  Status: {response.status_code}")
        
        if response.status_code != 200:
            print(f"❌ Failed to fetch webpage")
            return
            
        soup = BeautifulSoup(response.content, 'html.parser')
        print(f"  Content length: {len(response.content)} bytes")
        
    except Exception as e:
        print(f"❌ Error fetching webpage: {str(e)}")
        return
    
    # Test improved price extraction
    print(f"\n💰 TESTING IMPROVED PRICE EXTRACTION...")
    improved_strategy = ImprovedNativeStrategy()
    
    try:
        price_result = improved_strategy.extract_improved_price(soup, url)
        print(f"  Improved extraction result: {price_result}")
    except Exception as e:
        print(f"  ❌ Improved extraction error: {str(e)}")
        price_result = {}
    
    # Manual price extraction methods
    print(f"\n🔧 MANUAL PRICE EXTRACTION METHODS:")
    
    # Method 1: JSON-LD structured data
    print(f"\n  Method 1: JSON-LD Structured Data")
    json_scripts = soup.find_all('script', type='application/ld+json')
    for i, script in enumerate(json_scripts):
        try:
            data = json.loads(script.string)
            print(f"    Script {i+1}: {str(data)[:200]}...")
            
            if isinstance(data, dict):
                if 'offers' in data:
                    print(f"    Found offers: {data['offers']}")
                if 'price' in data:
                    print(f"    Found price: {data['price']}")
            elif isinstance(data, list):
                for item in data:
                    if isinstance(item, dict) and ('offers' in item or 'price' in item):
                        print(f"    Found price data: {item}")
        except:
            continue
    
    # Method 2: Price CSS selectors
    print(f"\n  Method 2: CSS Selectors")
    price_selectors = [
        '.price',
        '.sale-price',
        '.current-price',
        '.product-price',
        '[data-price]',
        '.price-current',
        '.special-price',
        '.final-price'
    ]
    
    for selector in price_selectors:
        elements = soup.select(selector)
        if elements:
            for elem in elements[:3]:  # Limit to first 3
                text = elem.get_text(strip=True)
                if text:
                    print(f"    {selector}: {text}")
    
    # Method 3: Text pattern matching
    print(f"\n  Method 3: Text Pattern Matching")
    price_patterns = [
        r'฿[\d,]+\.?\d*',
        r'THB[\d,]+\.?\d*',
        r'[\d,]+\.?\d*\s*฿',
        r'[\d,]+\.?\d*\s*บาท',
        r'Price[:\s]*[\d,]+\.?\d*',
        r'ราคา[:\s]*[\d,]+\.?\d*'
    ]
    
    page_text = soup.get_text()
    for pattern in price_patterns:
        matches = re.findall(pattern, page_text)
        if matches:
            print(f"    Pattern {pattern}: {matches[:5]}")  # First 5 matches
    
    # Method 4: Meta tags
    print(f"\n  Method 4: Meta Tags")
    meta_tags = soup.find_all('meta')
    for meta in meta_tags:
        if meta.get('property') and 'price' in meta.get('property', '').lower():
            print(f"    {meta.get('property')}: {meta.get('content')}")
        if meta.get('name') and 'price' in meta.get('name', '').lower():
            print(f"    {meta.get('name')}: {meta.get('content')}")
    
    # Method 5: Data attributes
    print(f"\n  Method 5: Data Attributes")
    elements_with_data = soup.find_all(attrs={"data-price": True})
    for elem in elements_with_data:
        print(f"    data-price: {elem.get('data-price')}")
    
    # Method 6: Specific TWD selectors
    print(f"\n  Method 6: TWD-Specific Selectors")
    twd_selectors = [
        '.product-info-price',
        '.product-price-value',
        '.price-box',
        '.regular-price',
        '.special-price .price',
        '[class*="price"]',
        '[id*="price"]'
    ]
    
    for selector in twd_selectors:
        elements = soup.select(selector)
        if elements:
            for elem in elements[:3]:
                text = elem.get_text(strip=True)
                if text:
                    print(f"    {selector}: {text}")
    
    # Attempt to fix the product
    print(f"\n🔧 ATTEMPTING TO FIX PRODUCT...")
    
    best_price = None
    best_original_price = None
    
    # Try to extract correct prices
    if price_result.get('current_price'):
        best_price = price_result['current_price']
    if price_result.get('original_price'):
        best_original_price = price_result['original_price']
    
    # Manual fallback extraction if improved method failed
    if not best_price:
        # Look for common price patterns in page text
        price_matches = re.findall(r'฿([\d,]+\.?\d*)', page_text)
        if price_matches:
            # Take the most likely price (usually the first clean number)
            try:
                best_price = float(price_matches[0].replace(',', ''))
                print(f"  Manual extraction found price: ฿{best_price}")
            except:
                pass
    
    # Apply fix if we found a price
    if best_price:
        updates = {'current_price': best_price}
        if best_original_price:
            updates['original_price'] = best_original_price
        
        print(f"\n✅ APPLYING FIX:")
        print(f"  Current price: ฿{best_price}")
        if best_original_price:
            print(f"  Original price: ฿{best_original_price}")
        
        try:
            update_result = supabase.client.table('products')\
                .update(updates)\
                .eq('sku', sku)\
                .execute()
            
            if update_result.data:
                print(f"  ✅ Successfully updated product {sku}")
                
                # Verify the update
                verify_result = supabase.client.table('products').select('current_price, original_price').eq('sku', sku).execute()
                if verify_result.data:
                    verified = verify_result.data[0]
                    print(f"  ✅ Verified - Current price: {verified.get('current_price')}")
                    if verified.get('original_price'):
                        print(f"  ✅ Verified - Original price: {verified.get('original_price')}")
            else:
                print(f"  ❌ Failed to update product")
                
        except Exception as e:
            print(f"  ❌ Error updating product: {str(e)}")
    else:
        print(f"\n❌ Could not extract valid price from webpage")
    
    print(f"\n🏁 DEBUG COMPLETE")

if __name__ == "__main__":
    debug_twd_product()