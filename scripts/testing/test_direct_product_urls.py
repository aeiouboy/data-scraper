#!/usr/bin/env python3
"""Test direct product URLs for each retailer"""
import asyncio
from src.services.firecrawl_client import FirecrawlClient
import re

# Test URLs for each retailer (found from their websites)
retailer_test_urls = {
    'GlobalHouse': [
        'https://globalhouse.co.th/product/5511001',  # Try numeric ID
        'https://globalhouse.co.th/p/5511001',
        'https://globalhouse.co.th/th/product/5511001',
        'https://globalhouse.co.th/products/electrical/air-conditioner',
    ],
    'DoHome': [
        'https://www.dohome.co.th/th/products/12345',
        'https://www.dohome.co.th/en/products/12345',
        'https://www.dohome.co.th/th/p/12345',
        'https://www.dohome.co.th/product/electrical/item-12345',
    ],
    'Boonthavorn': [
        'https://www.boonthavorn.com/th/products/12345',
        'https://www.boonthavorn.com/en/products/12345',
        'https://www.boonthavorn.com/product/tiles/item-12345',
        'https://www.boonthavorn.com/p/12345',
    ],
    'MegaHome': [
        'https://www.megahome.co.th/th/products/12345',
        'https://www.megahome.co.th/en/products/12345',
        'https://www.megahome.co.th/p/12345',
        'https://www.megahome.co.th/product/flooring/item-12345',
    ]
}

async def test_urls():
    async with FirecrawlClient() as client:
        for retailer, urls in retailer_test_urls.items():
            print(f"\n{'='*60}")
            print(f"Testing {retailer}")
            print(f"{'='*60}")
            
            for url in urls:
                print(f"\nTesting: {url}")
                try:
                    result = await client.scrape(url)
                    if result:
                        status_code = result.get('statusCode', 'N/A')
                        title = result.get('metadata', {}).get('title', 'No title')[:80]
                        markdown = result.get('markdown', '')
                        
                        print(f"  Status: {status_code}")
                        print(f"  Title: {title}")
                        
                        # Look for product indicators
                        product_indicators = [
                            r'ราคา|price',
                            r'สินค้า|product',
                            r'รหัส|sku|code',
                            r'หมวดหมู่|category',
                            r'add.?to.?cart|หยิบใส่',
                        ]
                        
                        found_indicators = []
                        for indicator in product_indicators:
                            if re.search(indicator, markdown, re.IGNORECASE):
                                found_indicators.append(indicator)
                        
                        if found_indicators:
                            print(f"  ✅ Found product indicators: {', '.join(found_indicators)}")
                        else:
                            print(f"  ❌ No product indicators found")
                            
                        # Check for actual links in content
                        links = result.get('linksOnPage', result.get('links', []))
                        if links:
                            print(f"  Links found: {len(links)}")
                            # Find product-like links
                            product_links = []
                            for link in links[:10]:
                                if isinstance(link, dict):
                                    url = link.get('url', link.get('href', ''))
                                else:
                                    url = str(link)
                                if any(pattern in url.lower() for pattern in ['product', '/p/', 'item', 'detail']):
                                    product_links.append(url)
                            if product_links:
                                print(f"  Product links: {product_links[:3]}")
                    else:
                        print(f"  ❌ No response")
                        
                except Exception as e:
                    print(f"  ❌ Error: {str(e)}")
                    
                await asyncio.sleep(2)  # Rate limiting

if __name__ == "__main__":
    asyncio.run(test_urls())