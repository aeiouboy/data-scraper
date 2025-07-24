#!/usr/bin/env python3
"""
Investigate TWD products with category URLs to understand the issue
"""

import requests
from bs4 import BeautifulSoup
from src.services.supabase_service import SupabaseService
import json

def investigate_twd_category_products():
    """Investigate a few TWD products with category URLs"""
    
    supabase = SupabaseService()
    
    print("🔍 INVESTIGATING TWD CATEGORY URL PRODUCTS")
    print("=" * 60)
    
    # Get 3 sample products with category URLs
    result = supabase.client.table('products')\
        .select('id, sku, name, brand, category, url, current_price, original_price')\
        .eq('retailer_code', 'TWD')\
        .like('url', '%/category/%')\
        .limit(3)\
        .execute()
    
    products = result.data
    
    investigation_results = []
    
    for product in products:
        print(f"\n📦 PRODUCT: {product['sku']}")
        print(f"  Name: {product['name']}")
        print(f"  Category: {product['category']}")
        print(f"  Current Price: ฿{product['current_price']}")
        print(f"  Original Price: ฿{product['original_price']}")
        print(f"  URL: {product['url']}")
        
        # Test the URL
        print(f"\n🌐 TESTING URL...")
        try:
            response = requests.get(product['url'], timeout=15)
            print(f"  Status: {response.status_code}")
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'html.parser')
                title = soup.find('title')
                if title:
                    print(f"  Page Title: {title.get_text()[:100]}...")
                
                # Look for product listings on category page
                product_links = soup.find_all('a', href=True)
                product_urls = []
                
                for link in product_links:
                    href = link.get('href', '')
                    if '/product/' in href:
                        if href.startswith('/'):
                            href = f"https://www.thaiwatsadu.com{href}"
                        product_urls.append(href)
                
                print(f"  Product URLs found on category page: {len(product_urls)}")
                if product_urls:
                    print(f"  Sample URLs: {product_urls[:3]}")
                
                # Try to find this specific product
                page_text = soup.get_text().lower()
                product_name_parts = product['name'].lower().split()[:3]
                
                potential_matches = []
                for word in product_name_parts:
                    if len(word) > 3 and word in page_text:
                        potential_matches.append(word)
                
                print(f"  Product name parts found on page: {potential_matches}")
                
            else:
                print(f"  ❌ URL not accessible")
                
        except Exception as e:
            print(f"  ❌ Error accessing URL: {str(e)}")
        
        # Try searching for this product manually
        print(f"\n🔍 SEARCHING FOR PRODUCT...")
        try:
            search_terms = ' '.join(product['name'].split()[:4])
            search_url = f"https://www.thaiwatsadu.com/en/search?q={search_terms}"
            
            response = requests.get(search_url, timeout=15)
            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # Look for search results
                search_results = soup.find_all('a', href=True)
                found_products = []
                
                for link in search_results:
                    href = link.get('href', '')
                    if '/product/' in href:
                        link_text = link.get_text(strip=True)
                        if any(word.lower() in link_text.lower() for word in product['name'].split()[:3] if len(word) > 3):
                            if href.startswith('/'):
                                href = f"https://www.thaiwatsadu.com{href}"
                            found_products.append({
                                'url': href,
                                'text': link_text[:100]
                            })
                
                print(f"  Search results found: {len(found_products)}")
                if found_products:
                    print(f"  Best match: {found_products[0]['url']}")
                    print(f"  Text: {found_products[0]['text']}")
                else:
                    print(f"  ❌ No matching products found in search")
            
        except Exception as e:
            print(f"  ❌ Search error: {str(e)}")
        
        investigation_results.append({
            'product': product,
            'url_accessible': response.status_code == 200 if 'response' in locals() else False,
            'search_found_matches': len(found_products) if 'found_products' in locals() else 0
        })
    
    # Summary
    print(f"\n📊 INVESTIGATION SUMMARY:")
    accessible_urls = sum(1 for r in investigation_results if r['url_accessible'])
    products_found_in_search = sum(1 for r in investigation_results if r['search_found_matches'] > 0)
    
    print(f"  Products investigated: {len(investigation_results)}")
    print(f"  Category URLs accessible: {accessible_urls}")
    print(f"  Products found via search: {products_found_in_search}")
    
    # Save results
    with open('twd_category_investigation_results.json', 'w') as f:
        json.dump(investigation_results, f, indent=2)
    
    print(f"\n📁 Results saved: twd_category_investigation_results.json")
    
    # Recommendation
    print(f"\n💡 RECOMMENDATIONS:")
    if products_found_in_search > 0:
        print(f"  ✅ Some products can be found via search - implement search-based URL correction")
    else:
        print(f"  ⚠️ Products not found via search - may need to be removed from database")
    
    if accessible_urls > 0:
        print(f"  📋 Category URLs are accessible - products may be listed on category pages")
    else:
        print(f"  ❌ Category URLs not accessible - products may be outdated")

if __name__ == "__main__":
    investigate_twd_category_products()