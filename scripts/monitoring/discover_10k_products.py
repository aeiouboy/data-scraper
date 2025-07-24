#!/usr/bin/env python3
"""
Discover 10K+ product URLs from HomePro for large-scale scraping test
"""
import asyncio
import logging
from src.scrapers.homepro_scraper import HomeProScraper

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def discover_large_product_set():
    """Discover ~10K product URLs from multiple categories"""
    
    print("🔍 Discovering 10K+ HomePro Products for Large-Scale Test")
    print("=" * 70)
    
    # Major HomePro categories that typically have many products
    categories = [
        ("APP", "https://www.homepro.co.th/c/APP"),  # Appliances - usually 1000+ products
        ("TOO", "https://www.homepro.co.th/c/TOO"),  # Tools - usually 2000+ products  
        ("ELT", "https://www.homepro.co.th/c/ELT"),  # Electrical - usually 1500+ products
        ("CON", "https://www.homepro.co.th/c/CON"),  # Construction - usually 2000+ products
        ("FUR", "https://www.homepro.co.th/c/FUR"),  # Furniture - usually 1500+ products
        ("BAT", "https://www.homepro.co.th/c/BAT"),  # Bathroom - usually 1000+ products
        ("KIT", "https://www.homepro.co.th/c/KIT"),  # Kitchen - usually 800+ products
        ("LIG", "https://www.homepro.co.th/c/LIG"),  # Lighting - usually 1200+ products
    ]
    
    all_urls = []
    
    try:
        async with HomeProScraper(use_native=True) as scraper:
            print("✅ HomePro scraper initialized with hybrid native strategy")
            
            for category_code, category_url in categories:
                print(f"\n📂 Discovering products from {category_code} category...")
                print(f"🔗 URL: {category_url}")
                
                try:
                    # Discover URLs from this category (max 25 pages to get ~1000-2000 URLs per category)
                    urls = await scraper.discover_product_urls(category_url, max_pages=25)
                    print(f"🔍 Found {len(urls)} products in {category_code}")
                    
                    all_urls.extend(urls)
                    print(f"📊 Total discovered so far: {len(all_urls)}")
                    
                    # Stop if we have enough URLs
                    if len(all_urls) >= 10000:
                        print(f"🎯 Target reached! Found {len(all_urls)} URLs")
                        break
                        
                except Exception as e:
                    print(f"❌ Error discovering from {category_code}: {str(e)}")
                    continue
            
            # Remove duplicates and limit to exactly 10K
            unique_urls = list(set(all_urls))
            final_urls = unique_urls[:10000]
            
            print(f"\n🎉 URL Discovery Complete!")
            print(f"📊 Statistics:")
            print(f"   - Total URLs found: {len(all_urls)}")
            print(f"   - Unique URLs: {len(unique_urls)}")
            print(f"   - Final set for testing: {len(final_urls)}")
            print(f"   - Categories processed: {len([c for c, _ in categories if len(all_urls) > 0])}")
            
            return final_urls
            
    except Exception as e:
        print(f"❌ Error during discovery: {str(e)}")
        import traceback
        traceback.print_exc()
        return []

if __name__ == "__main__":
    asyncio.run(discover_large_product_set())