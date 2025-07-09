"""
Check which Boonthavorn URL patterns have products
"""
import requests
from bs4 import BeautifulSoup
import json
import time

def check_url_for_products(url):
    """Check if a URL contains product listings"""
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Look for product-related elements
            product_selectors = [
                'div[class*="product"]',
                'article[class*="product"]',
                'div[class*="Product"]',
                'a[href*="/product/"]',
                'a[href*="/p/"]',
                'div[data-product]',
                'div[class*="item"]',
                'div[class*="tile"]',
                'div[class*="card"]'
            ]
            
            results = {}
            for selector in product_selectors:
                elements = soup.select(selector)
                if elements:
                    results[selector] = len(elements)
            
            # Check for product URLs
            product_links = []
            all_links = soup.find_all('a', href=True)
            for link in all_links:
                href = link.get('href', '')
                if '/product/' in href or '/p/' in href:
                    product_links.append(href)
            
            return {
                'status': 'success',
                'product_elements': results,
                'product_links': len(product_links),
                'sample_links': product_links[:3]
            }
        else:
            return {'status': 'error', 'code': response.status_code}
    except Exception as e:
        return {'status': 'error', 'message': str(e)}

def test_boonthavorn_patterns():
    """Test different URL patterns"""
    print("Testing Boonthavorn URL Patterns for Products")
    print("=" * 80)
    
    # Load discovered URLs
    with open('boonthavorn_discovered.json', 'r', encoding='utf-8') as f:
        discovered = json.load(f)
    
    # Group by pattern
    by_pattern = {}
    for item in discovered:
        pattern = item['pattern']
        if pattern not in by_pattern:
            by_pattern[pattern] = []
        by_pattern[pattern].append(item)
    
    # Test one URL from each pattern
    results = {}
    
    for pattern, urls in by_pattern.items():
        print(f"\nTesting pattern: {pattern}")
        print("-" * 40)
        
        # Test the first URL from this pattern
        test_url = urls[0]['final_url']
        print(f"Testing: {test_url}")
        
        result = check_url_for_products(test_url)
        results[pattern] = {
            'url': test_url,
            'result': result
        }
        
        if result['status'] == 'success':
            if result['product_elements']:
                print(f"✓ Found product elements:")
                for selector, count in result['product_elements'].items():
                    print(f"  - {selector}: {count} elements")
            if result['product_links'] > 0:
                print(f"✓ Found {result['product_links']} product links")
                if result['sample_links']:
                    print("  Sample links:")
                    for link in result['sample_links']:
                        print(f"    - {link}")
            if not result['product_elements'] and result['product_links'] == 0:
                print("✗ No products found")
        else:
            print(f"✗ Error: {result}")
        
        time.sleep(0.5)  # Rate limiting
    
    # Find best pattern
    print("\n" + "=" * 80)
    print("Summary")
    print("=" * 80)
    
    best_pattern = None
    max_products = 0
    
    for pattern, data in results.items():
        if data['result']['status'] == 'success':
            total_elements = sum(data['result']['product_elements'].values())
            total_links = data['result']['product_links']
            total = total_elements + total_links
            
            print(f"{pattern}: {total} product indicators")
            
            if total > max_products:
                max_products = total
                best_pattern = pattern
    
    if best_pattern:
        print(f"\nBest pattern: {best_pattern} with {max_products} product indicators")
        
        # Get all URLs for the best pattern
        best_urls = [item['final_url'] for item in by_pattern[best_pattern]]
        print(f"\nURLs for best pattern ({len(best_urls)} total):")
        for url in best_urls[:10]:  # Show first 10
            print(f"  - {url}")
    
    return results, best_pattern

def check_thai_categories():
    """Check specific Thai categories"""
    print("\n" + "=" * 80)
    print("Checking Thai Category Pages")
    print("=" * 80)
    
    base_url = "https://www.boonthavorn.com"
    
    # Common Boonthavorn categories in Thai
    thai_categories = [
        "กระเบื้องปูพื้น",
        "กระเบื้องผนัง", 
        "สุขภัณฑ์",
        "ก๊อกน้ำ",
        "อ่างล้างหน้า",
        "ชักโครก",
        "อ่างอาบน้ำ",
        "ฝักบัว",
        "ประตู",
        "หน้าต่าง"
    ]
    
    working_categories = []
    
    for category in thai_categories:
        # Try different patterns
        patterns = ["/th/category/", "/category/", "/products/", "/c/"]
        
        for pattern in patterns:
            url = f"{base_url}{pattern}{category}"
            try:
                response = requests.head(url, timeout=5, allow_redirects=True)
                if response.status_code == 200:
                    working_categories.append({
                        'category': category,
                        'url': url,
                        'final_url': response.url,
                        'pattern': pattern
                    })
                    print(f"✓ Found: {category} at {pattern}")
                    break
                time.sleep(0.2)
            except:
                pass
    
    if working_categories:
        print(f"\nFound {len(working_categories)} working Thai categories")
        
        # Save for use
        with open('boonthavorn_thai_categories.json', 'w', encoding='utf-8') as f:
            json.dump(working_categories, f, ensure_ascii=False, indent=2)
        print("Saved to: boonthavorn_thai_categories.json")
    
    return working_categories

if __name__ == "__main__":
    # Test patterns for products
    results, best_pattern = test_boonthavorn_patterns()
    
    # Check Thai categories
    thai_categories = check_thai_categories()
    
    # Generate recommended URLs
    print("\n" + "=" * 80)
    print("Recommended Category URLs for Boonthavorn")
    print("=" * 80)
    
    if best_pattern:
        print(f"Using pattern: {best_pattern}")
        print("\ncategory_urls=[")
        
        # Use discovered URLs with best pattern
        with open('boonthavorn_discovered.json', 'r', encoding='utf-8') as f:
            discovered = json.load(f)
        
        seen = set()
        for item in discovered:
            if item['pattern'] == best_pattern and item['final_url'] not in seen:
                seen.add(item['final_url'])
                category_name = item['category']
                print(f'    "{item["final_url"]}",  # {category_name}')
        
        print("],")
    else:
        print("No optimal pattern found - website may use JavaScript rendering")