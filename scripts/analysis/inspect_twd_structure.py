"""
Inspect Thai Watsadu HTML structure to find correct selectors
"""
import requests
from bs4 import BeautifulSoup
import json

def inspect_page_structure():
    """Inspect Thai Watsadu page structure"""
    test_url = "https://www.thaiwatsadu.com/th/category/เหล็ก-51"
    
    print("Inspecting Thai Watsadu page structure...")
    print("=" * 80)
    print(f"URL: {test_url}")
    print()
    
    try:
        response = requests.get(test_url, timeout=10)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Find all links
            all_links = soup.find_all('a', href=True)
            product_links = []
            
            print("Looking for product URL patterns...")
            print("-" * 80)
            
            # Check different URL patterns
            patterns = ['/product/', '/p/', '/item/', '/th/p/', '/th/product/']
            
            for link in all_links:
                href = link.get('href', '')
                for pattern in patterns:
                    if pattern in href:
                        product_links.append({
                            'href': href,
                            'text': link.text.strip()[:50],
                            'pattern': pattern
                        })
                        break
            
            if product_links:
                print(f"Found {len(product_links)} product links")
                print("\nSample product URLs:")
                for i, link in enumerate(product_links[:5]):
                    print(f"{i+1}. Pattern: {link['pattern']}")
                    print(f"   URL: {link['href']}")
                    print(f"   Text: {link['text']}...")
                    print()
            
            # Check for product containers
            print("\nChecking for product containers...")
            print("-" * 80)
            
            # Common e-commerce container patterns
            container_selectors = [
                ('div.product-item', 'Product item divs'),
                ('div[class*="product-card"]', 'Product card divs'),
                ('article.product', 'Product articles'),
                ('li.product-item', 'Product list items'),
                ('div[class*="ProductCard"]', 'ProductCard divs'),
                ('div[class*="product-box"]', 'Product box divs'),
                ('div[class*="item-box"]', 'Item box divs'),
                ('div[data-product-id]', 'Divs with product ID'),
                ('a[class*="product-link"]', 'Product links'),
                ('div.item', 'Item divs'),
            ]
            
            for selector, description in container_selectors:
                elements = soup.select(selector)
                if elements:
                    print(f"✓ Found {len(elements)} elements matching: {selector} ({description})")
                    
                    # Show sample structure
                    if elements:
                        sample = elements[0]
                        print(f"  Sample structure:")
                        # Get classes
                        classes = sample.get('class', [])
                        print(f"  Classes: {' '.join(classes)}")
                        # Check for product data
                        if sample.get('data-product-id'):
                            print(f"  Product ID: {sample.get('data-product-id')}")
            
            # Save full HTML for manual inspection
            with open('twd_sample_page.html', 'w', encoding='utf-8') as f:
                f.write(response.text)
            print("\nFull HTML saved to: twd_sample_page.html")
            
            # Look for JavaScript rendered content indicators
            print("\nChecking for JavaScript rendering...")
            print("-" * 80)
            
            # Check for common JS frameworks
            js_indicators = [
                ('script[src*="react"]', 'React'),
                ('script[src*="vue"]', 'Vue'),
                ('script[src*="angular"]', 'Angular'),
                ('div[id="app"]', 'Vue/React app container'),
                ('div[id="root"]', 'React root container'),
                ('script[type="application/json"]', 'JSON data scripts'),
            ]
            
            for selector, framework in js_indicators:
                elements = soup.select(selector)
                if elements:
                    print(f"✓ Found {framework}: {len(elements)} elements")
            
        else:
            print(f"Error: HTTP {response.status_code}")
            
    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    inspect_page_structure()