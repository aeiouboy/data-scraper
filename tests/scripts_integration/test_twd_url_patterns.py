#!/usr/bin/env python3
"""
Test Thai Watsadu URL patterns to understand why only 1 product is found
"""
import re
from urllib.parse import urlparse

# Sample URLs from the debug output
test_urls = [
    "https://www.thaiwatsadu.com/en/category/เครื่องปรับอากาศติดผนัง-630201",
    "https://www.thaiwatsadu.com/en/product/%E0%B9%81%E0%B8%AD%E0%B8%A3%E0%B9%8C%E0%B8%95%E0%B8%B4%E0%B8%94%E0%B8%9C%E0%B8%99%E0%B8%B1%E0%B8%87-12,000-BTU-BEKO-BTFOG-120-G-%7C-BTFOG-121-G-60355295",
    "/en/product/air-conditioner-60355295",
    "/product/test-product-123",
    "/th/product/แอร์ติดผนัง-60355295",
    "https://www.thaiwatsadu.com/en/category/test-category",
    "https://www.thaiwatsadu.com/th/product/test-60123456"
]

print("Testing Thai Watsadu URL Pattern Detection")
print("=" * 60)

# Test the pattern used in _discover_product_urls
for url in test_urls:
    print(f"\nTesting: {url}")
    
    # Check if it matches product pattern
    is_product = '/th/product/' in url or '/product/' in url
    print(f"  - Matches product pattern: {is_product}")
    
    # Check specific patterns
    if '/product/' in url:
        print("    ✓ Contains '/product/'")
    if '/th/product/' in url:
        print("    ✓ Contains '/th/product/'")
    if '/en/product/' in url:
        print("    ✓ Contains '/en/product/'")
    
    # Check if it's a category
    if '/category/' in url:
        print("    ℹ️  This is a category URL")

# Now let's check what might be happening with the URL discovery
print("\n" + "="*60)
print("Checking URL discovery logic")
print("="*60)

# Simulate the discovery logic
discovered_urls = set()

# Simulate links that might be found on the page
simulated_links = [
    {"url": "https://www.thaiwatsadu.com/en/product/air-conditioner-1"},
    {"href": "/en/product/air-conditioner-2"},
    "https://www.thaiwatsadu.com/en/product/air-conditioner-3",
    {"url": "/product/air-conditioner-4"},
    {"url": "https://www.thaiwatsadu.com/en/category/other-category"},
    {"url": "https://www.thaiwatsadu.com/th/product/thai-product-5"}
]

print("\nSimulating link discovery:")
for link in simulated_links:
    if isinstance(link, dict):
        url = link.get('url', link.get('href', ''))
    else:
        url = str(link)
    
    print(f"\n  Link: {link}")
    print(f"  Extracted URL: {url}")
    
    # Thai Watsadu product URL patterns (from the scraper)
    if '/th/product/' in url or '/product/' in url:
        if not url.startswith('http'):
            url = f"https://www.thaiwatsadu.com{url}"
        discovered_urls.add(url)
        print(f"  ✓ Added to product URLs: {url}")
    else:
        print("  ✗ Not a product URL")

print(f"\nTotal discovered: {len(discovered_urls)} products")

# Check if there might be an issue with the URL format
print("\n" + "="*60)
print("Potential Issues")
print("="*60)

category_url = "https://www.thaiwatsadu.com/en/category/เครื่องปรับอากาศติดผนัง-630201"
print(f"\nCategory URL: {category_url}")

# Check URL encoding
from urllib.parse import quote, unquote
print(f"\nURL encoding check:")
print(f"  - Decoded: {unquote(category_url)}")
print(f"  - Path contains Thai: {'เครื่องปรับอากาศติดผนัง' in category_url}")

# Check if pagination might be an issue
print(f"\nPagination check:")
print(f"  - Base URL: {category_url}")
print(f"  - Page 2: {category_url}?page=2")

# Check if the issue might be with max_pages
print("\nIf max_pages=1 and only first link is processed, that could explain '1 product found'")
print("The scraper might be finding multiple URLs but only processing the first one.")