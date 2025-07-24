#!/usr/bin/env python3
"""Test MegaHome website structure directly"""
import httpx
import asyncio
from bs4 import BeautifulSoup
import re

async def test_megahome():
    """Test MegaHome product URLs"""
    base_url = 'https://www.megahome.co.th'
    
    async with httpx.AsyncClient(follow_redirects=True) as client:
        # Test main page
        print("Testing MegaHome main page...")
        response = await client.get(base_url)
        
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Find all links with /p/ pattern
            product_links = []
            all_links = soup.find_all('a', href=True)
            
            for link in all_links:
                href = link['href']
                if '/p/' in href:
                    full_url = href if href.startswith('http') else base_url + href
                    product_links.append(full_url)
            
            print(f"\nFound {len(product_links)} product links with /p/ pattern")
            
            # Show unique patterns
            unique_patterns = set()
            for url in product_links:
                # Extract pattern
                match = re.search(r'/p/(\d+)', url)
                if match:
                    unique_patterns.add(f"/p/{len(match.group(1))}-digit-id")
            
            print("\nURL patterns found:")
            for pattern in unique_patterns:
                print(f"  - {pattern}")
            
            # Show some sample URLs
            print(f"\nSample product URLs:")
            for url in product_links[:5]:
                print(f"  - {url}")
            
            # Test a few product URLs
            print(f"\nTesting first 3 product URLs:")
            for i, url in enumerate(product_links[:3]):
                print(f"\n{i+1}. {url}")
                try:
                    prod_response = await client.get(url, timeout=10.0)
                    if prod_response.status_code == 200:
                        prod_soup = BeautifulSoup(prod_response.text, 'html.parser')
                        
                        # Look for product information
                        title = prod_soup.find('h1')
                        price = prod_soup.find(class_=re.compile('price', re.I))
                        sku = prod_soup.find(text=re.compile(r'SKU|รหัส', re.I))
                        
                        print(f"   Title: {title.text.strip() if title else 'Not found'}")
                        print(f"   Price element: {'Found' if price else 'Not found'}")
                        print(f"   SKU element: {'Found' if sku else 'Not found'}")
                        
                        # Check for structured data
                        json_ld = prod_soup.find('script', type='application/ld+json')
                        if json_ld:
                            print("   ✅ Has structured data (JSON-LD)")
                    else:
                        print(f"   ❌ Status: {prod_response.status_code}")
                except Exception as e:
                    print(f"   ❌ Error: {str(e)}")
                
                await asyncio.sleep(1)  # Rate limiting
                
            # Check category pages
            print("\n\nTesting category pages:")
            category_urls = [
                '/c/FLO',  # Flooring
                '/c/TOO',  # Tools
                '/flooring'
            ]
            
            for cat_url in category_urls:
                full_cat_url = base_url + cat_url
                print(f"\nTesting: {full_cat_url}")
                try:
                    cat_response = await client.get(full_cat_url, timeout=10.0)
                    print(f"   Status: {cat_response.status_code}")
                    if cat_response.status_code == 200:
                        cat_soup = BeautifulSoup(cat_response.text, 'html.parser')
                        cat_products = cat_soup.find_all('a', href=re.compile(r'/p/\d+'))
                        print(f"   Products found: {len(cat_products)}")
                except Exception as e:
                    print(f"   Error: {str(e)}")
                    
        else:
            print(f"Failed to access MegaHome: {response.status_code}")

if __name__ == "__main__":
    asyncio.run(test_megahome())