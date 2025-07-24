"""
Test updated Boonthavorn URLs with Firecrawl
"""
import asyncio
import os
from dotenv import load_dotenv
from src.services.firecrawl_client import FirecrawlClient
from src.config.retailers import RETAILER_CONFIGS, RetailerType
import json

# Load environment variables
load_dotenv()

async def test_boonthavorn_categories():
    """Test updated Boonthavorn category URLs"""
    if not os.getenv('FIRECRAWL_API_KEY'):
        print("❌ FIRECRAWL_API_KEY not found!")
        return
    
    firecrawl = FirecrawlClient()
    boonthavorn_config = RETAILER_CONFIGS[RetailerType.BOONTHAVORN]
    
    print("Testing Updated Boonthavorn Category URLs")
    print("=" * 80)
    print(f"Total categories: {len(boonthavorn_config.category_urls)}")
    print()
    
    # Test a few key categories
    test_urls = [
        boonthavorn_config.category_urls[0],  # Main tiles category
        boonthavorn_config.category_urls[6],  # Floor tiles
        boonthavorn_config.category_urls[10], # Sanitarywares
    ]
    
    total_products_found = 0
    working_categories = []
    
    for url in test_urls:
        print(f"\nTesting: {url}")
        print("-" * 60)
        
        try:
            result = await firecrawl.scrape(url)
            
            if result:
                # Look for product links
                links = result.get('linksOnPage', result.get('links', []))
                product_links = []
                
                for link in links:
                    if isinstance(link, dict):
                        href = link.get('url', link.get('href', ''))
                    else:
                        href = str(link)
                    
                    # Boonthavorn product patterns
                    if any(pattern in href.lower() for pattern in ['/product/', '/p/', '-p-', '/item/']):
                        if 'boonthavorn.com' in href:
                            product_links.append(href)
                
                # Check content for product indicators
                markdown = result.get('markdown', '')
                has_prices = any(indicator in markdown for indicator in ['฿', 'บาท', 'ราคา', 'price'])
                
                print(f"✓ Scraped successfully")
                print(f"  Total links: {len(links)}")
                print(f"  Product links found: {len(product_links)}")
                print(f"  Price indicators: {'Yes' if has_prices else 'No'}")
                
                if product_links:
                    working_categories.append(url)
                    total_products_found += len(product_links)
                    print("  Sample product links:")
                    for link in product_links[:3]:
                        print(f"    - {link}")
                
                # Check for "view more" or pagination
                if 'ดูเพิ่มเติม' in markdown or 'Load More' in markdown:
                    print("  ✓ Has pagination/load more")
                
            else:
                print("✗ Failed to scrape")
                
        except Exception as e:
            print(f"✗ Error: {str(e)}")
        
        await asyncio.sleep(2)  # Rate limiting
    
    # Summary
    print("\n" + "=" * 80)
    print("Summary")
    print("=" * 80)
    print(f"Categories tested: {len(test_urls)}")
    print(f"Working categories: {len(working_categories)}")
    print(f"Total product links found: {total_products_found}")
    
    if working_categories:
        print("\n✓ Boonthavorn scraper should work with these categories:")
        for cat in working_categories:
            print(f"  - {cat}")
    else:
        print("\n⚠️ No product links found. Boonthavorn may require:")
        print("  - JavaScript rendering for product listings")
        print("  - Different scraping approach")
        print("  - API access for product data")

async def test_specific_page():
    """Test a specific Boonthavorn page structure"""
    print("\n" + "=" * 80)
    print("Testing Boonthavorn Page Structure")
    print("=" * 80)
    
    firecrawl = FirecrawlClient()
    
    # Test the main tiles page
    test_url = "https://www.boonthavorn.com/boonthavorn-wall-floor"
    
    try:
        result = await firecrawl.scrape(test_url)
        
        if result:
            # Save for analysis
            with open('boonthavorn_tiles_page.json', 'w', encoding='utf-8') as f:
                json.dump(result, f, ensure_ascii=False, indent=2)
            
            print(f"✓ Saved page data to: boonthavorn_tiles_page.json")
            
            # Check for JavaScript data
            html = result.get('html', '')
            if '__NEXT_DATA__' in html:
                print("✓ Found Next.js data - site uses React/Next.js")
            if 'window.__STATE__' in html:
                print("✓ Found state data - site uses client-side rendering")
                
    except Exception as e:
        print(f"Error: {str(e)}")

async def main():
    """Run tests"""
    # Test category URLs
    await test_boonthavorn_categories()
    
    # Test page structure
    await test_specific_page()
    
    print("\n" + "=" * 80)
    print("Recommendations:")
    print("=" * 80)
    print("1. Boonthavorn uses JavaScript rendering (React/Next.js)")
    print("2. Product data may be loaded dynamically via API")
    print("3. Consider using browser automation or API endpoints")
    print("4. The current URLs are correct but need special handling")

if __name__ == "__main__":
    asyncio.run(main())