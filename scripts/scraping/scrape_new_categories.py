#!/usr/bin/env python3
"""
Scrape specific new HomePro categories
"""
import asyncio
import sys
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).parent))

from src.scrapers.homepro_scraper import HomeProScraper

async def scrape_categories():
    print("🛒 SCRAPING NEW HOMEPRO CATEGORIES")
    print("=" * 50)
    
    # Select a few high-impact categories to scrape
    categories = [
        "https://www.homepro.co.th/c/ELE",    # Electronics
        "https://www.homepro.co.th/c/TOO",    # Tools  
        "https://www.homepro.co.th/c/APP",    # Appliances
        "https://www.homepro.co.th/c/FUR",    # Furniture
        "https://www.homepro.co.th/c/KIT",    # Kitchen
    ]
    
    scraper = HomeProScraper()
    
    for i, category_url in enumerate(categories, 1):
        category_code = category_url.split('/c/')[-1]
        print(f"\n🔄 [{i}/{len(categories)}] Scraping category: {category_code}")
        print(f"   URL: {category_url}")
        
        try:
            # Scrape the category (limit to reasonable number for testing)
            results = await scraper.scrape_category(category_url, max_pages=5)
            
            if results:
                success_count = len([r for r in results if r.get('success', False)])
                total_count = len(results)
                success_rate = (success_count / total_count * 100) if total_count > 0 else 0
                
                print(f"   ✅ Scraped {success_count}/{total_count} products ({success_rate:.1f}% success)")
                
                # Show sample of categories extracted
                categories_found = set()
                for result in results:
                    if result.get('success') and result.get('data', {}).get('category'):
                        categories_found.add(result['data']['category'])
                
                if categories_found:
                    print(f"   📋 Sample categories found:")
                    for cat in list(categories_found)[:5]:
                        print(f"      • {cat}")
                else:
                    print(f"   ⚠️ No categories extracted")
            else:
                print(f"   ❌ No results returned")
                
        except Exception as e:
            print(f"   ❌ Error scraping {category_code}: {str(e)[:60]}...")
        
        # Brief pause between categories
        await asyncio.sleep(2)
    
    print(f"\n🎉 Category scraping completed!")
    print(f"💡 Check the database for updated product counts.")

if __name__ == "__main__":
    asyncio.run(scrape_categories())