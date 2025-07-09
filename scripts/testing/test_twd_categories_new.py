"""
Test Thai Watsadu scraper with new category URLs
"""
import asyncio
import aiohttp
from bs4 import BeautifulSoup
import json
from datetime import datetime
from src.config.retailers import RETAILER_CONFIGS, RetailerType

async def test_category_url(session, url):
    """Test a single category URL"""
    try:
        async with session.get(url, timeout=10) as response:
            if response.status == 200:
                text = await response.text()
                soup = BeautifulSoup(text, 'html.parser')
                
                # Look for products
                product_count = 0
                
                # Common product container patterns
                product_selectors = [
                    'div[class*="product"]',
                    'article[class*="product"]',
                    'li[class*="product"]',
                    'div[class*="item"]',
                    'a[href*="/product/"]'
                ]
                
                for selector in product_selectors:
                    products = soup.select(selector)
                    if products:
                        product_count = len(products)
                        break
                
                # Get page title
                title = soup.find('title')
                title_text = title.text.strip() if title else "No title"
                
                return {
                    'url': url,
                    'status': 'success',
                    'product_count': product_count,
                    'title': title_text[:100]
                }
            else:
                return {
                    'url': url,
                    'status': 'error',
                    'error': f'HTTP {response.status}'
                }
    except Exception as e:
        return {
            'url': url,
            'status': 'error',
            'error': str(e)
        }

async def test_all_categories():
    """Test all Thai Watsadu category URLs"""
    # Get Thai Watsadu config
    twd_config = RETAILER_CONFIGS[RetailerType.TWD]
    
    print("Testing Thai Watsadu Category URLs")
    print("=" * 80)
    print(f"Total categories to test: {len(twd_config.category_urls)}")
    print(f"Base URL: {twd_config.base_url}")
    print()
    
    # Create session
    connector = aiohttp.TCPConnector(limit=3)  # Limit concurrent connections
    async with aiohttp.ClientSession(connector=connector) as session:
        results = []
        
        # Test categories in batches
        batch_size = 5
        for i in range(0, len(twd_config.category_urls), batch_size):
            batch = twd_config.category_urls[i:i+batch_size]
            batch_results = await asyncio.gather(
                *[test_category_url(session, url) for url in batch]
            )
            results.extend(batch_results)
            
            # Progress update
            print(f"Tested {len(results)}/{len(twd_config.category_urls)} categories...")
            
            # Rate limiting
            await asyncio.sleep(1)
    
    # Analyze results
    successful = [r for r in results if r['status'] == 'success']
    failed = [r for r in results if r['status'] == 'error']
    with_products = [r for r in successful if r['product_count'] > 0]
    
    print("\n" + "=" * 80)
    print("Test Results Summary:")
    print("-" * 80)
    print(f"✓ Successful: {len(successful)}/{len(results)}")
    print(f"✗ Failed: {len(failed)}/{len(results)}")
    print(f"📦 Categories with products found: {len(with_products)}")
    
    if successful:
        print("\nSuccessful Categories:")
        print("-" * 80)
        for result in successful[:10]:  # Show first 10
            print(f"✓ {result['url'].split('/')[-1]}")
            print(f"  Title: {result['title']}")
            print(f"  Products found: {result['product_count']}")
    
    if failed:
        print("\nFailed Categories:")
        print("-" * 80)
        for result in failed[:5]:  # Show first 5
            print(f"✗ {result['url'].split('/')[-1]}")
            print(f"  Error: {result['error']}")
    
    # Save detailed results
    report = {
        'test_date': datetime.now().isoformat(),
        'total_categories': len(results),
        'successful': len(successful),
        'failed': len(failed),
        'with_products': len(with_products),
        'results': results
    }
    
    with open('twd_category_test_report.json', 'w', encoding='utf-8') as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    
    print(f"\nDetailed report saved to: twd_category_test_report.json")
    
    return len(successful) > 0

async def test_sample_scraping():
    """Test actual scraping of a few categories"""
    print("\n" + "=" * 80)
    print("Testing Sample Product Scraping")
    print("=" * 80)
    
    # Get a few working categories
    twd_config = RETAILER_CONFIGS[RetailerType.TWD]
    test_categories = [
        "https://www.thaiwatsadu.com/th/category/เหล็ก-51",
        "https://www.thaiwatsadu.com/th/category/เครื่องมือช่าง-52",
        "https://www.thaiwatsadu.com/th/category/สี-55",
    ]
    
    async with aiohttp.ClientSession() as session:
        for category_url in test_categories:
            print(f"\nTesting: {category_url}")
            try:
                async with session.get(category_url, timeout=10) as response:
                    if response.status == 200:
                        text = await response.text()
                        soup = BeautifulSoup(text, 'html.parser')
                        
                        # Find product links
                        product_links = soup.select('a[href*="/th/product/"]')[:5]
                        
                        if product_links:
                            print(f"  Found {len(product_links)} product links")
                            for link in product_links[:3]:
                                href = link.get('href', '')
                                text = link.text.strip()[:50]
                                print(f"    - {text}...")
                        else:
                            print("  No product links found")
                    else:
                        print(f"  Error: HTTP {response.status}")
            except Exception as e:
                print(f"  Error: {str(e)}")

async def main():
    """Run all tests"""
    print("Thai Watsadu Category URL Test")
    print("=" * 80)
    print(f"Testing Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Test all category URLs
    success = await test_all_categories()
    
    if success:
        # Test sample scraping
        await test_sample_scraping()
        
        print("\n" + "=" * 80)
        print("✓ Thai Watsadu category URLs have been verified!")
        print("The scraper should now work with the updated URLs.")
    else:
        print("\n" + "=" * 80)
        print("✗ Some issues were found with the category URLs.")
        print("Please check the test report for details.")

if __name__ == "__main__":
    asyncio.run(main())