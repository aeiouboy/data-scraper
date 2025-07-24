#!/usr/bin/env python3
"""
Test HomePro pagination structure to understand URL format
"""
import asyncio
import aiohttp
from bs4 import BeautifulSoup

async def test_homepro_pagination():
    """Test different pagination URL formats for HomePro"""
    
    print("🔍 Testing HomePro Pagination Structure")
    print("=" * 50)
    
    base_url = "https://www.homepro.co.th/c/LIG"
    
    # Test different pagination formats
    test_urls = [
        f"{base_url}",                    # Page 1 (base)
        f"{base_url}?page=2",            # Format 1: ?page=2
        f"{base_url}?p=2",               # Format 2: ?p=2  
        f"{base_url}/page/2",            # Format 3: /page/2
        f"{base_url}?offset=50",         # Format 4: ?offset=50
        f"{base_url}?start=50",          # Format 5: ?start=50
    ]
    
    async with aiohttp.ClientSession() as session:
        for i, url in enumerate(test_urls):
            try:
                print(f"\n📄 Testing URL {i+1}: {url}")
                
                async with session.get(url, timeout=10) as response:
                    if response.status == 200:
                        content = await response.text()
                        soup = BeautifulSoup(content, 'html.parser')
                        
                        # Count product links
                        product_links = soup.find_all('a', href=lambda x: x and '/p/' in x)
                        unique_links = list(set([link.get('href') for link in product_links if link.get('href')]))
                        
                        print(f"   ✅ Status: {response.status}")
                        print(f"   📦 Products found: {len(unique_links)}")
                        
                        # Check for pagination indicators
                        pagination_found = False
                        pagination_elements = soup.find_all(['a', 'button'], string=lambda x: x and ('next' in x.lower() or 'ถัดไป' in x.lower() or '2' in x))
                        if pagination_elements:
                            pagination_found = True
                            print(f"   🔢 Pagination elements found: {len(pagination_elements)}")
                        
                        # Look for specific pagination patterns
                        page_links = soup.find_all('a', href=lambda x: x and ('page=' in x or 'p=' in x))
                        if page_links:
                            print(f"   🔗 Page links found: {[link.get('href') for link in page_links[:3]]}")
                        
                        # Check if content differs from page 1
                        if i > 0:
                            print(f"   📊 Content length: {len(content)} chars")
                            
                    else:
                        print(f"   ❌ Status: {response.status}")
                        
            except Exception as e:
                print(f"   ❌ Error: {str(e)}")
    
    print(f"\n💡 Recommendation:")
    print("   Check the working pagination format and update the native strategy accordingly")

if __name__ == "__main__":
    asyncio.run(test_homepro_pagination())