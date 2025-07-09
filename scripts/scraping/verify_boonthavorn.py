"""
Verify Boonthavorn website and category URLs
"""
import requests
from bs4 import BeautifulSoup
import time
import json

def check_boonthavorn_main():
    """Check Boonthavorn main page"""
    print("Checking Boonthavorn Website")
    print("=" * 80)
    
    base_url = "https://www.boonthavorn.com"
    
    try:
        response = requests.get(base_url, timeout=10)
        print(f"Main page status: {response.status_code}")
        
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Find category links
            print("\nLooking for category links...")
            print("-" * 80)
            
            # Common patterns for category links
            category_patterns = [
                'a[href*="/category"]',
                'a[href*="/catalog"]',
                'a[href*="/c/"]',
                'a[href*="/products"]',
                'a[class*="category"]',
                'a[class*="menu"]'
            ]
            
            all_category_links = []
            
            for pattern in category_patterns:
                links = soup.select(pattern)
                for link in links:
                    href = link.get('href', '')
                    text = link.get_text(strip=True)
                    if href and not href.startswith('#') and len(text) > 2:
                        full_url = href if href.startswith('http') else f"{base_url}{href}"
                        all_category_links.append({
                            'url': full_url,
                            'text': text,
                            'pattern': pattern
                        })
            
            # Remove duplicates
            seen = set()
            unique_links = []
            for link in all_category_links:
                if link['url'] not in seen:
                    seen.add(link['url'])
                    unique_links.append(link)
            
            print(f"Found {len(unique_links)} unique category-like links")
            
            # Group by pattern
            by_pattern = {}
            for link in unique_links:
                pattern = link['pattern']
                if pattern not in by_pattern:
                    by_pattern[pattern] = []
                by_pattern[pattern].append(link)
            
            # Show samples by pattern
            for pattern, links in by_pattern.items():
                print(f"\nPattern: {pattern} ({len(links)} links)")
                for link in links[:3]:  # Show first 3
                    print(f"  - {link['text'][:50]}...")
                    print(f"    {link['url']}")
            
            # Save full HTML for inspection
            with open('boonthavorn_main.html', 'w', encoding='utf-8') as f:
                f.write(response.text)
            print("\nFull HTML saved to: boonthavorn_main.html")
            
        else:
            print(f"Error accessing main page: HTTP {response.status_code}")
            
    except Exception as e:
        print(f"Error: {str(e)}")

def check_configured_urls():
    """Check the URLs configured in retailers.py"""
    from src.config.retailers import RETAILER_CONFIGS, RetailerType
    
    print("\n" + "=" * 80)
    print("Checking Configured Boonthavorn URLs")
    print("=" * 80)
    
    boonthavorn_config = RETAILER_CONFIGS[RetailerType.BOONTHAVORN]
    
    print(f"Base URL: {boonthavorn_config.base_url}")
    print(f"Total configured categories: {len(boonthavorn_config.category_urls)}")
    print()
    
    working_urls = []
    failed_urls = []
    
    for url in boonthavorn_config.category_urls:
        try:
            print(f"Checking: {url}")
            response = requests.head(url, timeout=5, allow_redirects=True)
            
            if response.status_code == 200:
                # Get the page to check for products
                full_response = requests.get(url, timeout=10)
                if full_response.status_code == 200:
                    soup = BeautifulSoup(full_response.text, 'html.parser')
                    
                    # Look for product indicators
                    product_indicators = [
                        'div[class*="product"]',
                        'article[class*="product"]',
                        'a[href*="/product"]',
                        'div[class*="item"]',
                        'div[class*="Product"]'
                    ]
                    
                    product_count = 0
                    for indicator in product_indicators:
                        elements = soup.select(indicator)
                        if elements:
                            product_count = len(elements)
                            break
                    
                    working_urls.append({
                        'url': url,
                        'final_url': response.url,
                        'redirected': url != response.url,
                        'product_count': product_count
                    })
                    print(f"  ✓ Status: 200 OK, Products found: {product_count}")
                else:
                    failed_urls.append({'url': url, 'status': full_response.status_code})
                    print(f"  ✗ Status: {full_response.status_code}")
            else:
                failed_urls.append({'url': url, 'status': response.status_code})
                print(f"  ✗ Status: {response.status_code}")
                
            time.sleep(0.5)  # Rate limiting
            
        except Exception as e:
            failed_urls.append({'url': url, 'error': str(e)})
            print(f"  ✗ Error: {str(e)}")
    
    # Summary
    print("\n" + "=" * 80)
    print("Summary")
    print("=" * 80)
    print(f"✓ Working URLs: {len(working_urls)}/{len(boonthavorn_config.category_urls)}")
    print(f"✗ Failed URLs: {len(failed_urls)}/{len(boonthavorn_config.category_urls)}")
    
    if working_urls:
        print("\nWorking URLs:")
        for item in working_urls:
            print(f"  - {item['url'].split('/')[-1]}")
            if item['redirected']:
                print(f"    Redirected to: {item['final_url']}")
            print(f"    Products: {item['product_count']}")
    
    if failed_urls:
        print("\nFailed URLs:")
        for item in failed_urls:
            print(f"  - {item['url']}")
            if 'status' in item:
                print(f"    Status: {item['status']}")
            else:
                print(f"    Error: {item['error']}")
    
    return working_urls, failed_urls

def discover_actual_categories():
    """Try to discover actual Boonthavorn categories"""
    print("\n" + "=" * 80)
    print("Discovering Actual Boonthavorn Categories")
    print("=" * 80)
    
    base_url = "https://www.boonthavorn.com"
    
    # Common e-commerce URL patterns
    test_patterns = [
        "/th/category",
        "/en/category",
        "/category",
        "/products",
        "/catalog",
        "/c",
        "/collections",
        "/shop"
    ]
    
    # Common Boonthavorn categories
    category_names = [
        "ceramic-tile", "กระเบื้อง", "tile",
        "sanitary-ware", "สุขภัณฑ์", "bathroom",
        "kitchen", "ครัว", "ห้องครัว",
        "flooring", "พื้น", "floor",
        "doors-windows", "ประตู", "หน้าต่าง",
        "lighting", "ไฟ", "โคมไฟ",
        "paint", "สี", "สีทาบ้าน"
    ]
    
    discovered_urls = []
    
    print("Testing URL patterns...")
    for pattern in test_patterns:
        for category in category_names[:5]:  # Test first 5 categories
            test_url = f"{base_url}{pattern}/{category}"
            try:
                response = requests.head(test_url, timeout=3, allow_redirects=True)
                if response.status_code == 200:
                    discovered_urls.append({
                        'url': test_url,
                        'final_url': response.url,
                        'pattern': pattern,
                        'category': category
                    })
                    print(f"✓ Found: {test_url}")
                    if response.url != test_url:
                        print(f"  Redirected to: {response.url}")
                time.sleep(0.2)
            except:
                pass
    
    if discovered_urls:
        print(f"\nDiscovered {len(discovered_urls)} working URLs")
        
        # Save discoveries
        with open('boonthavorn_discovered.json', 'w', encoding='utf-8') as f:
            json.dump(discovered_urls, f, ensure_ascii=False, indent=2)
        print("Saved to: boonthavorn_discovered.json")
    else:
        print("\nNo URLs discovered with common patterns")

def inspect_page_structure():
    """Inspect a Boonthavorn page to understand structure"""
    print("\n" + "=" * 80)
    print("Inspecting Boonthavorn Page Structure")
    print("=" * 80)
    
    # Try the main page
    url = "https://www.boonthavorn.com"
    
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Check for navigation menu
            print("\nLooking for navigation menu...")
            nav_selectors = [
                'nav', 'div[class*="nav"]', 'ul[class*="menu"]',
                'div[class*="menu"]', 'header'
            ]
            
            for selector in nav_selectors:
                elements = soup.select(selector)
                if elements:
                    print(f"Found {len(elements)} {selector} elements")
                    # Look for links within
                    links = elements[0].find_all('a', href=True)
                    if links:
                        print(f"  Contains {len(links)} links")
                        for link in links[:5]:
                            href = link.get('href', '')
                            text = link.get_text(strip=True)[:30]
                            if text and not href.startswith('#'):
                                print(f"    - {text}: {href}")
            
            # Check for JavaScript frameworks
            print("\nChecking for JavaScript rendering...")
            js_indicators = [
                ('script[src*="react"]', 'React'),
                ('script[src*="vue"]', 'Vue'),
                ('script[src*="angular"]', 'Angular'),
                ('div[id="app"]', 'Vue/React app'),
                ('div[id="root"]', 'React root'),
                ('script[src*="next"]', 'Next.js')
            ]
            
            for selector, framework in js_indicators:
                if soup.select(selector):
                    print(f"✓ Found {framework}")
            
            # Look for API endpoints in scripts
            scripts = soup.find_all('script')
            for script in scripts:
                if script.string and 'api' in script.string.lower():
                    print("\nFound script with API references")
                    # Extract potential API endpoints
                    import re
                    api_patterns = re.findall(r'["\'](/api/[^"\']+)["\']', script.string)
                    for api in api_patterns[:3]:
                        print(f"  - {api}")
                    
    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    # Check main page
    check_boonthavorn_main()
    
    # Check configured URLs
    working, failed = check_configured_urls()
    
    # Try to discover actual categories
    discover_actual_categories()
    
    # Inspect page structure
    inspect_page_structure()