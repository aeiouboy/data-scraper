#!/usr/bin/env python3
"""
Analyze the Thai Watsadu scraping issue where only 1 product is found
This script identifies the root cause and suggests fixes
"""
import asyncio
import re
from typing import List, Dict, Any
from urllib.parse import urljoin

from src.services.firecrawl_client import FirecrawlClient
from src.core.logging_config import setup_logging

setup_logging()
import logging
logger = logging.getLogger(__name__)


async def analyze_url_extraction_issue():
    """
    Analyze why the Thai Watsadu scraper might only find 1 product
    """
    category_url = "https://www.thaiwatsadu.com/en/category/เครื่องปรับอากาศติดผนัง-630201"
    base_url = "https://www.thaiwatsadu.com"
    
    firecrawl = FirecrawlClient()
    
    print("\nThai Watsadu URL Extraction Analysis")
    print("="*60)
    
    # Fetch the category page
    print(f"\n1. Fetching category page: {category_url}")
    result = await firecrawl.scrape(category_url)
    
    if not result:
        print("❌ Failed to fetch category page")
        return
    
    print("✅ Successfully fetched category page")
    
    # Analyze different link extraction methods
    print("\n2. Analyzing link extraction methods:")
    
    # Method 1: linksOnPage (primary)
    links_on_page = result.get('linksOnPage', [])
    print(f"\n   Method 1 - linksOnPage: {len(links_on_page)} links")
    
    # Method 2: links (fallback)
    links_fallback = result.get('links', [])
    print(f"   Method 2 - links: {len(links_fallback)} links")
    
    # Method 3: Extract from markdown
    markdown = result.get('markdown', '')
    markdown_links = re.findall(r'\[([^\]]+)\]\(([^)]+)\)', markdown)
    print(f"   Method 3 - markdown extraction: {len(markdown_links)} links")
    
    # Method 4: Extract from HTML patterns
    html_links = re.findall(r'href=["\']([^"\']+)["\']', result.get('html', ''))
    print(f"   Method 4 - HTML extraction: {len(html_links)} links")
    
    # Analyze product URL patterns
    print("\n3. Product URL Analysis:")
    
    def extract_product_urls(links: List[Any]) -> List[str]:
        """Extract product URLs from a list of links"""
        product_urls = set()
        
        for link in links:
            url = ""
            if isinstance(link, dict):
                url = link.get('url', link.get('href', ''))
            elif isinstance(link, str):
                url = link
            elif isinstance(link, tuple) and len(link) >= 2:
                url = link[1]  # For markdown regex results
            
            # Check if it's a product URL
            if url and ('/product/' in url or '/th/product/' in url):
                # Make absolute URL
                if not url.startswith('http'):
                    url = urljoin(base_url, url)
                product_urls.add(url)
        
        return list(product_urls)
    
    # Extract products using each method
    products_method1 = extract_product_urls(links_on_page)
    products_method2 = extract_product_urls(links_fallback)
    products_method3 = extract_product_urls(markdown_links)
    products_method4 = extract_product_urls(html_links)
    
    print(f"\n   Products from linksOnPage: {len(products_method1)}")
    print(f"   Products from links: {len(products_method2)}")
    print(f"   Products from markdown: {len(products_method3)}")
    print(f"   Products from HTML: {len(products_method4)}")
    
    # Combine all unique products
    all_products = set()
    all_products.update(products_method1)
    all_products.update(products_method2)
    all_products.update(products_method3)
    all_products.update(products_method4)
    
    print(f"\n   Total unique products found: {len(all_products)}")
    
    # Show sample products
    if all_products:
        print("\n4. Sample Product URLs:")
        for i, url in enumerate(list(all_products)[:5], 1):
            print(f"   {i}. {url}")
    
    # Check for pagination
    print("\n5. Pagination Analysis:")
    
    # Look for page indicators
    page_patterns = [
        r'[?&]page=(\d+)',
        r'หน้า\s*(\d+)',
        r'Page\s*(\d+)',
        r'data-page=["\'](\d+)["\']',
        r'class=["\']page-(\d+)["\']'
    ]
    
    pages_found = set()
    for pattern in page_patterns:
        matches = re.findall(pattern, str(result), re.IGNORECASE)
        pages_found.update(matches)
    
    if pages_found:
        print(f"   Found page numbers: {sorted(pages_found)}")
        print(f"   Max page: {max(map(int, pages_found))}")
    else:
        print("   No pagination indicators found")
    
    # Check for "load more" or infinite scroll
    load_more_patterns = [
        'load more',
        'โหลดเพิ่ม',
        'infinite scroll',
        'lazy load'
    ]
    
    content_lower = (markdown + str(result.get('html', ''))).lower()
    for pattern in load_more_patterns:
        if pattern in content_lower:
            print(f"   ⚠️  Found '{pattern}' - might use dynamic loading")
    
    # Analyze potential issues
    print("\n6. Potential Issues:")
    
    issues = []
    
    if len(all_products) <= 1:
        issues.append("Only 1 or no products found - URL pattern matching might be incorrect")
    
    if len(products_method1) == 0 and len(links_on_page) > 0:
        issues.append("linksOnPage has links but no products extracted - check URL patterns")
    
    if pages_found and len(all_products) < 10:
        issues.append("Pagination exists but few products found - might need to fetch multiple pages")
    
    if not issues:
        issues.append("No obvious issues found - scraper should work correctly")
    
    for i, issue in enumerate(issues, 1):
        print(f"   {i}. {issue}")
    
    # Suggest fixes
    print("\n7. Suggested Fixes:")
    
    if len(all_products) > len(products_method1):
        print("   1. Update URL extraction to check multiple sources (links, markdown, HTML)")
    
    if pages_found:
        print("   2. Ensure pagination is handled correctly (fetch multiple pages)")
    
    print("   3. Add debug logging to track exactly which URLs are being discovered")
    print("   4. Verify that the scraper waits for the page to fully load")
    
    return {
        'total_products': len(all_products),
        'products_by_method': {
            'linksOnPage': len(products_method1),
            'links': len(products_method2),
            'markdown': len(products_method3),
            'html': len(products_method4)
        },
        'has_pagination': len(pages_found) > 0,
        'sample_urls': list(all_products)[:10]
    }


if __name__ == "__main__":
    results = asyncio.run(analyze_url_extraction_issue())