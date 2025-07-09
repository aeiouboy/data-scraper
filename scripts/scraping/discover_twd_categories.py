"""
Script to discover all Thai Watsadu categories
"""
import requests
from bs4 import BeautifulSoup
import json
import time
from urllib.parse import urljoin, unquote

def discover_categories():
    """Discover all Thai Watsadu categories"""
    base_url = "https://www.thaiwatsadu.com"
    discovered_categories = {}
    
    # Try common category IDs (1-1000)
    print("Discovering Thai Watsadu categories...")
    print("=" * 60)
    
    valid_categories = []
    
    # First, let's check the main page for category links
    try:
        response = requests.get(f"{base_url}/th", timeout=10)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Find all links that match category pattern
            category_links = soup.find_all('a', href=lambda x: x and '/th/category/' in x)
            
            for link in category_links:
                href = link.get('href')
                text = link.get_text(strip=True)
                if href:
                    full_url = urljoin(base_url, href)
                    if full_url not in discovered_categories:
                        discovered_categories[full_url] = text
                        print(f"Found: {text} -> {href}")
    
    except Exception as e:
        print(f"Error fetching main page: {e}")
    
    # Try to discover categories by ID pattern (checking common IDs)
    category_ids = [
        # Known categories
        51, 52, 53, 54, 55, 56, 57, 58, 59, 510, 511, 512, 513, 514, 515, 516,
        # Extended search
        60, 61, 62, 63, 64, 65, 66, 67, 68, 69, 610, 611, 612, 613, 614, 615,
        # Special categories
        6010, 6110, 719900,
        # Additional IDs to check
        *range(1, 100),  # Check 1-99
        *range(100, 200, 10),  # Check 100, 110, 120...
        *range(1000, 2000, 100),  # Check 1000, 1100, 1200...
    ]
    
    print("\nChecking category IDs...")
    print("-" * 60)
    
    for cat_id in set(category_ids):
        try:
            # Try different URL patterns
            urls_to_try = [
                f"{base_url}/th/category/{cat_id}",
                f"{base_url}/th/category/category-{cat_id}",
            ]
            
            for url in urls_to_try:
                response = requests.head(url, timeout=5, allow_redirects=True)
                if response.status_code == 200:
                    # If found, get the page to extract category name
                    full_response = requests.get(url, timeout=10)
                    if full_response.status_code == 200:
                        soup = BeautifulSoup(full_response.text, 'html.parser')
                        
                        # Try to find category name
                        title = soup.find('h1') or soup.find('title')
                        if title:
                            category_name = title.get_text(strip=True)
                            valid_categories.append({
                                'id': cat_id,
                                'url': url,
                                'name': category_name
                            })
                            print(f"✓ Category {cat_id}: {category_name}")
                            break
                
                time.sleep(0.5)  # Rate limiting
                
        except Exception as e:
            continue
    
    # Save results
    results = {
        'discovered_from_homepage': discovered_categories,
        'discovered_by_id': valid_categories,
        'total_found': len(discovered_categories) + len(valid_categories)
    }
    
    with open('twd_categories.json', 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    
    print(f"\nTotal categories found: {results['total_found']}")
    print("Results saved to twd_categories.json")
    
    # Generate category URLs for config
    print("\nCategory URLs for configuration:")
    print("-" * 60)
    
    all_categories = []
    
    # From homepage
    for url, name in discovered_categories.items():
        all_categories.append(f'            "{url}",  # {name}')
    
    # From ID discovery
    for cat in valid_categories:
        all_categories.append(f'            "{cat["url"]}",  # {cat["name"]}')
    
    print("category_urls=[")
    for cat in all_categories:
        print(cat)
    print("        ],")

if __name__ == "__main__":
    discover_categories()