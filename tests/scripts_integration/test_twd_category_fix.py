#!/usr/bin/env python3
"""
Test script to verify the Thai Watsadu category scraping fix
"""
import asyncio
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.scrapers.thaiwatsadu_scraper import ThaiWatsaduScraper
from src.scrapers.thaiwatsadu_scraper_improved import ImprovedThaiWatsaduScraper


async def compare_scrapers():
    """Compare original vs improved scraper"""
    category_url = "https://www.thaiwatsadu.com/en/category/เครื่องปรับอากาศติดผนัง-630201"
    
    print("\n" + "="*60)
    print("Thai Watsadu Category Scraping Comparison")
    print("="*60)
    print(f"Testing URL: {category_url}\n")
    
    # Test original scraper
    print("1. Testing ORIGINAL scraper...")
    print("-" * 40)
    original_scraper = ThaiWatsaduScraper()
    
    # Just test URL discovery
    try:
        original_urls = await original_scraper._discover_product_urls(category_url, max_pages=1)
        print(f"✅ Original scraper discovered: {len(original_urls)} URLs")
        if original_urls:
            print(f"   Sample URLs:")
            for url in original_urls[:3]:
                print(f"   - {url}")
    except Exception as e:
        print(f"❌ Original scraper error: {str(e)}")
    
    print("\n2. Testing IMPROVED scraper...")
    print("-" * 40)
    improved_scraper = ImprovedThaiWatsaduScraper()
    
    try:
        # Test with just 1 page and scraping first 3 products
        result = await improved_scraper.scrape_category(category_url, max_pages=1)
        
        print(f"\n📊 Results Summary:")
        print(f"   - URLs discovered: {result['discovered']}")
        print(f"   - Successfully scraped: {result['success']}")
        print(f"   - Failed: {result['failed']}")
        print(f"   - Success rate: {(result['success']/result['discovered']*100):.1f}%" if result['discovered'] > 0 else "N/A")
        
        if result['successful_products']:
            print(f"\n✅ Successfully scraped products:")
            for i, product in enumerate(result['successful_products'][:5], 1):
                print(f"   {i}. {product['name'][:60]}...")
                print(f"      SKU: {product['sku']}")
        
        if result['errors']:
            print(f"\n⚠️  Errors encountered: {len(result['errors'])}")
            error_summary = {}
            for error in result['errors']:
                error_type = error['error'].split(':')[0]
                error_summary[error_type] = error_summary.get(error_type, 0) + 1
            
            for error_type, count in error_summary.items():
                print(f"   - {error_type}: {count} occurrences")
                
    except Exception as e:
        print(f"❌ Improved scraper error: {str(e)}")
    
    print("\n" + "="*60)
    print("✅ Comparison complete!")
    print("="*60)


async def quick_test():
    """Quick test of the fix"""
    category_url = "https://www.thaiwatsadu.com/en/category/เครื่องปรับอากาศติดผนัง-630201"
    
    print("\n🔧 Quick Fix Test")
    print("="*40)
    
    scraper = ImprovedThaiWatsaduScraper()
    
    # Test URL discovery
    urls = await scraper._discover_product_urls_improved(category_url, max_pages=1)
    print(f"✅ Discovered {len(urls)} product URLs")
    
    if urls:
        # Test scraping first 3 products
        print(f"\n📦 Testing individual product scraping...")
        
        from src.scrapers.thaiwatsadu_scraper import ThaiWatsaduScraper
        original_scraper = ThaiWatsaduScraper()
        
        success = 0
        for i, url in enumerate(urls[:3], 1):
            print(f"\n[{i}/3] {url}")
            try:
                product = await original_scraper.scrape_product(url)
                if product:
                    print(f"   ✅ Success: {product.name[:50]}...")
                    success += 1
                else:
                    print(f"   ❌ Failed: No product data")
            except Exception as e:
                print(f"   ❌ Error: {str(e)}")
            
            await asyncio.sleep(2)  # Rate limit
        
        print(f"\n📊 Result: {success}/3 products scraped successfully")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description='Test Thai Watsadu category scraping fix')
    parser.add_argument('--quick', action='store_true', help='Run quick test only')
    args = parser.parse_args()
    
    if args.quick:
        asyncio.run(quick_test())
    else:
        asyncio.run(compare_scrapers())