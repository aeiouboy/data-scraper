"""
Test Boonthavorn with Firecrawl API
"""
import asyncio
import os
from dotenv import load_dotenv
from src.services.firecrawl_client import FirecrawlClient
import json

# Load environment variables
load_dotenv()

async def test_boonthavorn_category():
    """Test Boonthavorn category with Firecrawl"""
    if not os.getenv('FIRECRAWL_API_KEY'):
        print("❌ FIRECRAWL_API_KEY not found!")
        return
    
    firecrawl = FirecrawlClient()
    
    # Test URLs
    test_urls = [
        "https://www.boonthavorn.com/th/category/ceramic-tile",
        "https://www.boonthavorn.com/th/category/กระเบื้องปูพื้น",
        "https://www.boonthavorn.com"
    ]
    
    print("Testing Boonthavorn with Firecrawl API")
    print("=" * 80)
    
    for url in test_urls:
        print(f"\nTesting: {url}")
        print("-" * 60)
        
        try:
            # Use Firecrawl to scrape
            result = await firecrawl.scrape(url)
            
            if result:
                # Check for product links
                links = result.get('linksOnPage', result.get('links', []))
                product_links = []
                
                for link in links:
                    if isinstance(link, dict):
                        href = link.get('url', link.get('href', ''))
                    else:
                        href = str(link)
                    
                    # Check for product patterns
                    if any(pattern in href for pattern in ['/product/', '/p/', '/item/']):
                        product_links.append(href)
                
                print(f"✓ Scraped successfully")
                print(f"  Total links found: {len(links)}")
                print(f"  Product links found: {len(product_links)}")
                
                if product_links:
                    print("  Sample product links:")
                    for link in product_links[:5]:
                        print(f"    - {link}")
                
                # Check markdown content for product info
                markdown = result.get('markdown', '')
                if 'ราคา' in markdown or 'บาท' in markdown or '฿' in markdown:
                    print("  ✓ Found price indicators in content")
                
                # Save result for inspection
                filename = f"boonthavorn_{url.split('/')[-1]}_firecrawl.json"
                with open(filename, 'w', encoding='utf-8') as f:
                    json.dump(result, f, ensure_ascii=False, indent=2)
                print(f"  Saved full result to: {filename}")
                
            else:
                print("✗ Failed to scrape")
                
        except Exception as e:
            print(f"✗ Error: {str(e)}")
        
        # Rate limiting
        await asyncio.sleep(2)

async def discover_boonthavorn_structure():
    """Try to discover Boonthavorn's actual structure"""
    print("\n" + "=" * 80)
    print("Discovering Boonthavorn Structure")
    print("=" * 80)
    
    firecrawl = FirecrawlClient()
    
    # Start from main page
    main_url = "https://www.boonthavorn.com"
    
    try:
        result = await firecrawl.scrape(main_url)
        
        if result:
            # Look for category links
            links = result.get('linksOnPage', result.get('links', []))
            category_links = []
            
            category_patterns = [
                '/category/', '/catalog/', '/products/', 
                '/collections/', '/c/', '/shop/'
            ]
            
            for link in links:
                if isinstance(link, dict):
                    href = link.get('url', link.get('href', ''))
                else:
                    href = str(link)
                
                # Check if it's a category link
                if any(pattern in href for pattern in category_patterns):
                    if 'boonthavorn.com' in href:
                        category_links.append(href)
            
            # Remove duplicates
            category_links = list(set(category_links))
            
            print(f"Found {len(category_links)} category links")
            
            if category_links:
                print("\nCategory URLs found:")
                for link in sorted(category_links)[:20]:  # Show first 20
                    print(f"  - {link}")
                
                # Save for later use
                with open('boonthavorn_categories_firecrawl.json', 'w', encoding='utf-8') as f:
                    json.dump(category_links, f, ensure_ascii=False, indent=2)
                print(f"\nSaved all {len(category_links)} category links to: boonthavorn_categories_firecrawl.json")
                
                return category_links
            
    except Exception as e:
        print(f"Error: {str(e)}")
    
    return []

async def main():
    """Run tests"""
    # Test specific categories
    await test_boonthavorn_category()
    
    # Discover structure
    category_links = await discover_boonthavorn_structure()
    
    if category_links:
        print("\n" + "=" * 80)
        print("Recommended Updates for retailers.py")
        print("=" * 80)
        print("\ncategory_urls=[")
        
        # Group by language/type
        th_links = [l for l in category_links if '/th/' in l]
        en_links = [l for l in category_links if '/en/' in l]
        other_links = [l for l in category_links if '/th/' not in l and '/en/' not in l]
        
        # Prioritize Thai links
        all_sorted = th_links[:10] + other_links[:5] + en_links[:5]
        
        for link in all_sorted[:15]:  # Limit to 15 categories
            category_name = link.split('/')[-1].replace('-', ' ').title()
            print(f'    "{link}",  # {category_name}')
        
        print("],")

if __name__ == "__main__":
    asyncio.run(main())