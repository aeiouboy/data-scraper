#!/usr/bin/env python3
"""Quick test to check retailer websites"""
import asyncio
from src.services.firecrawl_client import FirecrawlClient

async def test_main_pages():
    retailers = {
        'GlobalHouse': 'https://globalhouse.co.th',
        'DoHome': 'https://www.dohome.co.th',
        'Boonthavorn': 'https://www.boonthavorn.com',
        'MegaHome': 'https://www.megahome.co.th'
    }
    
    async with FirecrawlClient() as client:
        for name, url in retailers.items():
            print(f"\n{'='*60}")
            print(f"Testing {name}: {url}")
            print(f"{'='*60}")
            
            try:
                result = await client.scrape(url)
                if result:
                    title = result.get('metadata', {}).get('title', 'No title')
                    links = result.get('linksOnPage', result.get('links', []))
                    
                    print(f"✅ Success! Title: {title}")
                    print(f"   Total links: {len(links)}")
                    
                    # Look for product-like URLs
                    product_patterns = ['product', '/p/', 'item', 'detail', 'sku']
                    product_links = []
                    
                    for link in links:
                        if isinstance(link, dict):
                            link_url = link.get('url', link.get('href', ''))
                        else:
                            link_url = str(link)
                        
                        if any(pattern in link_url.lower() for pattern in product_patterns):
                            product_links.append(link_url)
                    
                    if product_links:
                        print(f"   Found {len(product_links)} product-like URLs:")
                        for pl in product_links[:3]:
                            print(f"     - {pl}")
                    else:
                        print("   ❌ No product URLs found")
                else:
                    print("❌ No response")
            except Exception as e:
                print(f"❌ Error: {str(e)}")
            
            await asyncio.sleep(2)

if __name__ == "__main__":
    asyncio.run(test_main_pages())