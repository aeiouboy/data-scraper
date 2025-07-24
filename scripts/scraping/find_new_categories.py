#!/usr/bin/env python3
"""
Find new HomePro categories to scrape
"""
import asyncio
import aiohttp
from bs4 import BeautifulSoup
import re

async def find_categories():
    print("🔍 FINDING NEW HOMEPRO CATEGORIES TO SCRAPE")
    print("=" * 60)
    
    # Popular HomePro category codes to try
    potential_categories = [
        # Home & Living
        "FUR", "DEC", "KIT", "BAT", "LIG", "GDN", "OUT",
        
        # Electronics & Appliances  
        "ELE", "APP", "AIR", "FAN", "TV", "AUD", "PC",
        
        # Tools & Hardware
        "TOO", "HAR", "PLU", "PIP", "ELE", "SAF", "LAD",
        
        # Construction & Building
        "CON", "CEM", "PAI", "TIL", "FLO", "ROO", "WIN",
        
        # Auto & Outdoor
        "AUT", "BIK", "SPO", "CAM", "PET", "TOY",
        
        # Previously tested
        "BED", "CLO",  # Already done
        
        # New ones to try
        "MED", "HEA", "BEA", "OFF", "STO", "CLE", "WAS"
    ]
    
    print(f"🎯 Testing {len(potential_categories)} potential category codes...")
    
    valid_categories = []
    
    async with aiohttp.ClientSession() as session:
        for category_code in potential_categories:
            url = f"https://www.homepro.co.th/c/{category_code}"
            
            try:
                async with session.get(url, timeout=10) as response:
                    if response.status == 200:
                        text = await response.text()
                        soup = BeautifulSoup(text, 'html.parser')
                        
                        # Check if it's a valid category page
                        products = soup.find_all('div', class_=re.compile(r'product|item'))
                        title_elem = soup.find('title')
                        title = title_elem.text if title_elem else ""
                        
                        if products and len(products) > 5:  # Valid category with products
                            # Extract category name from title or breadcrumb
                            category_name = title.split(' | ')[0] if ' | ' in title else title
                            product_count = len(products)
                            
                            valid_categories.append({
                                'code': category_code,
                                'url': url,
                                'name': category_name[:50],
                                'estimated_products': product_count
                            })
                            
                            print(f"   ✅ {category_code}: {category_name[:40]}... (~{product_count} products)")
                        else:
                            print(f"   ❌ {category_code}: No products found")
                            
            except Exception as e:
                print(f"   ⚠️ {category_code}: Error - {str(e)[:30]}...")
                
            # Small delay to be respectful
            await asyncio.sleep(0.5)
    
    print(f"\n📊 SUMMARY:")
    print(f"   ✅ Valid categories found: {len(valid_categories)}")
    
    if valid_categories:
        print(f"\n🎯 RECOMMENDED CATEGORIES TO SCRAPE:")
        for cat in valid_categories[:10]:  # Show top 10
            print(f"   • {cat['code']}: {cat['name']} (~{cat['estimated_products']} products)")
            print(f"     URL: {cat['url']}")
    
    return valid_categories

if __name__ == "__main__":
    asyncio.run(find_categories())