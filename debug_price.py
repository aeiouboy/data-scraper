#!/usr/bin/env python3
"""Debug price extraction for a specific product"""
import asyncio
import re
from app.services.firecrawl_client import FirecrawlClient

async def debug_price():
    client = FirecrawlClient()
    
    # Scrape the product page
    result = await client.scrape("https://www.homepro.co.th/p/1083389")
    
    if result:
        markdown = result.get("markdown", "")
        
        # Find all price patterns
        print("=== All prices found in markdown ===")
        
        # Pattern 1: ฿ followed by numbers
        baht_prices = re.findall(r'฿\s*([\d,]+)', markdown)
        print(f"\nBaht prices (฿): {baht_prices[:10]}")
        
        # Pattern 2: Numbers followed by บาท
        baht_suffix = re.findall(r'([\d,]+)\s*บาท', markdown)
        print(f"\nPrices with บาท suffix: {baht_suffix[:10]}")
        
        # Pattern 3: Specific price patterns around "ราคา" (price)
        price_context = re.findall(r'ราคา[^0-9]*([\d,]+)', markdown)
        print(f"\nPrices near 'ราคา': {price_context[:5]}")
        
        # Look for sale/discount patterns
        sale_patterns = re.findall(r'(?:ลด|sale|โปร|พิเศษ)[^0-9]*([\d,]+)', markdown, re.IGNORECASE)
        print(f"\nSale/discount prices: {sale_patterns[:5]}")
        
        # Find specific section with มีคนซื้อไปแล้ว
        if 'มีคนซื้อไปแล้ว' in markdown:
            # Extract text around this phrase
            idx = markdown.find('มีคนซื้อไปแล้ว')
            context = markdown[max(0, idx-500):idx+500]
            print(f"\n=== Context around 'มีคนซื้อไปแล้ว' ===")
            print(context)
        
        # Look for the actual price display area
        if '995' in markdown:
            idx = markdown.find('995')
            context = markdown[max(0, idx-200):idx+200]
            print(f"\n=== Context around '995' ===")
            print(context)

if __name__ == "__main__":
    asyncio.run(debug_price())