#!/usr/bin/env python3
"""Debug price extraction for HomePro product"""

import asyncio
import sys
import os
import logging
import re
from bs4 import BeautifulSoup

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.scrapers.strategies.native_strategy import NativeStrategy

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def debug_price_extraction():
    """Debug price extraction for specific product"""
    
    test_url = "https://www.homepro.co.th/p/1097133"
    
    try:
        config = {
            'name': 'HomePro',
            'code': 'HP',
            'base_url': 'https://www.homepro.co.th',
            'rate_limit_delay': 2.0,
            'max_concurrent': 3,
            'timeout': 30,
            'retry_attempts': 2
        }
        
        strategy = NativeStrategy(config)
        result = await strategy.scrape_url(test_url)
        
        if result.success and result.data:
            # Get the raw HTML
            html_content = result.data.get('content', '')
            if not html_content:
                print("No HTML content found")
                return
            
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Find all price patterns
            print("🔍 All price patterns found in HTML:")
            price_matches = re.findall(r'฿\s*([0-9,]+)', html_content)
            unique_prices = sorted(list(set([float(p.replace(',', '')) for p in price_matches if p.replace(',', '').isdigit()])))
            
            print(f"   Found prices: {unique_prices}")
            
            # Look for specific price elements
            print("\n🔍 Checking specific price selectors:")
            
            selectors_to_check = [
                '.price',
                '.product-price',
                '[class*="price"]',
                '[data-price]',
                '.regular-price',
                '.sale-price',
                '.original-price',
                '.current-price'
            ]
            
            for selector in selectors_to_check:
                elements = soup.select(selector)
                if elements:
                    print(f"   {selector}: Found {len(elements)} elements")
                    for i, elem in enumerate(elements[:3]):  # Show first 3
                        text = elem.get_text(strip=True)
                        print(f"      Element {i+1}: '{text}'")
                else:
                    print(f"   {selector}: No elements found")
            
            # Search for common price display patterns
            print("\n🔍 Looking for price display patterns:")
            
            # Look for crossed-out prices (original price)
            crossed_out = soup.find_all(['span', 'div', 'del', 's'], style=re.compile(r'text-decoration.*line-through|text-decoration.*strikethrough', re.I))
            if crossed_out:
                print(f"   Found {len(crossed_out)} crossed-out elements:")
                for elem in crossed_out:
                    text = elem.get_text(strip=True)
                    print(f"      Crossed out: '{text}'")
            
            # Look for elements with price-like classes
            price_like_classes = soup.find_all(['span', 'div'], class_=re.compile(r'price|cost|amount', re.I))
            if price_like_classes:
                print(f"   Found {len(price_like_classes)} price-like class elements:")
                for i, elem in enumerate(price_like_classes[:5]):
                    text = elem.get_text(strip=True)
                    classes = ' '.join(elem.get('class', []))
                    print(f"      Element {i+1} ({classes}): '{text}'")
            
            # Show what our current extraction found
            print(f"\n📊 Current extraction results:")
            print(f"   Original Price: {result.data.get('original_price', 'Not found')}")
            print(f"   Current Price: {result.data.get('current_price', 'Not found')}")
            print(f"   Discount: {result.data.get('discount_percentage', 'Not found')}%")
            
        else:
            print(f"❌ Failed to scrape: {result.error}")
            
    except Exception as e:
        logger.error(f"Error: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        await strategy.close()

if __name__ == "__main__":
    asyncio.run(debug_price_extraction())