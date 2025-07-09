#!/usr/bin/env python3
"""Analyze retailer website structures without using Firecrawl"""
import httpx
import asyncio
from bs4 import BeautifulSoup
import json
import re

async def analyze_retailer(name, base_url, test_urls):
    """Analyze a retailer's website structure"""
    print(f"\n{'='*60}")
    print(f"Analyzing {name}")
    print(f"{'='*60}")
    
    async with httpx.AsyncClient(follow_redirects=True) as client:
        for url in test_urls:
            print(f"\nTesting: {url}")
            try:
                response = await client.get(url, timeout=10.0)
                print(f"Status: {response.status_code}")
                
                if response.status_code == 200:
                    soup = BeautifulSoup(response.text, 'html.parser')
                    
                    # Check for common e-commerce patterns
                    patterns = {
                        'Product links': [
                            'a[href*="product"]',
                            'a[href*="/p/"]',
                            'a[href*="item"]',
                            'a[href*="detail"]',
                            'a[class*="product"]',
                            'div[class*="product-item"]',
                            'div[class*="product-card"]'
                        ],
                        'Price elements': [
                            '[class*="price"]',
                            '[data-price]',
                            'span:contains("฿")',
                            'span:contains("THB")',
                            '.price',
                            '.product-price'
                        ],
                        'Product data': [
                            '[data-product]',
                            '[data-sku]',
                            '[data-product-id]',
                            'script[type="application/ld+json"]'
                        ],
                        'Next.js/React': [
                            'script[src*="_next"]',
                            'div[id="__next"]',
                            'script[src*="react"]'
                        ]
                    }
                    
                    found_patterns = {}
                    for pattern_type, selectors in patterns.items():
                        for selector in selectors:
                            try:
                                if ':contains' in selector:
                                    # Handle text search
                                    elements = soup.find_all(text=re.compile(selector.split('"')[1]))
                                else:
                                    elements = soup.select(selector)
                                if elements:
                                    if pattern_type not in found_patterns:
                                        found_patterns[pattern_type] = []
                                    found_patterns[pattern_type].append(f"{selector}: {len(elements)} found")
                            except:
                                pass
                    
                    if found_patterns:
                        print("Found patterns:")
                        for pattern_type, findings in found_patterns.items():
                            print(f"  {pattern_type}:")
                            for finding in findings[:3]:  # Limit output
                                print(f"    - {finding}")
                    
                    # Check for API endpoints in scripts
                    scripts = soup.find_all('script')
                    api_patterns = []
                    for script in scripts:
                        if script.string:
                            # Look for API endpoints
                            api_matches = re.findall(r'["\']([^"\']*api[^"\']*)["\']', script.string)
                            api_patterns.extend([m for m in api_matches if 'product' in m.lower() or 'search' in m.lower()][:3])
                    
                    if api_patterns:
                        print("  Potential API endpoints:")
                        for api in set(api_patterns):
                            print(f"    - {api}")
                            
                else:
                    print(f"Failed with status: {response.status_code}")
                    
            except Exception as e:
                print(f"Error: {str(e)}")

async def main():
    retailers = {
        'GlobalHouse': {
            'base': 'https://globalhouse.co.th',
            'urls': [
                'https://globalhouse.co.th',
                'https://globalhouse.co.th/product/category/5511001',
                'https://globalhouse.co.th/electrical'
            ]
        },
        'DoHome': {
            'base': 'https://www.dohome.co.th',
            'urls': [
                'https://www.dohome.co.th',
                'https://www.dohome.co.th/th/electrical',
                'https://www.dohome.co.th/en/search?q=air'
            ]
        },
        'Boonthavorn': {
            'base': 'https://www.boonthavorn.com',
            'urls': [
                'https://www.boonthavorn.com',
                'https://www.boonthavorn.com/boonthavorn-wall-floor',
                'https://www.boonthavorn.com/th/ceramic-floor-tiles'
            ]
        },
        'MegaHome': {
            'base': 'https://www.megahome.co.th',
            'urls': [
                'https://www.megahome.co.th',
                'https://www.megahome.co.th/th/flooring',
                'https://www.megahome.co.th/en/search?q=floor'
            ]
        }
    }
    
    for name, config in retailers.items():
        await analyze_retailer(name, config['base'], config['urls'])
        await asyncio.sleep(2)  # Be respectful with requests

if __name__ == "__main__":
    asyncio.run(main())