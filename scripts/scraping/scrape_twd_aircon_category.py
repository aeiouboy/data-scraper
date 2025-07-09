#!/usr/bin/env python3
"""Scrape Thai Watsadu wall-mounted air conditioner category"""

import os
import sys
import asyncio
import json
from datetime import datetime
from urllib.parse import unquote
from dotenv import load_dotenv

# Add the app directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Load environment variables
load_dotenv()

from src.services.firecrawl_client import FirecrawlClient

async def scrape_category_page(url: str, page_num: int = 1):
    """Scrape a single category page"""
    print(f"\n📄 Scraping page {page_num}: {url}")
    
    client = FirecrawlClient()
    
    try:
        # Scrape the page
        result = await client.scrape(url)
        
        if not result:
            print(f"❌ Failed to scrape page {page_num}")
            return None
            
        print(f"✅ Successfully scraped page {page_num}")
        
        # Extract product information from markdown
        products = []
        markdown = result.get('markdown', '')
        
        # Look for product patterns in the markdown
        # Thai Watsadu typically shows products in a grid with:
        # - Product image
        # - Product name
        # - Price
        # - SKU/Product code
        
        # Split by common product separators
        lines = markdown.split('\n')
        current_product = {}
        
        for line in lines:
            line = line.strip()
            
            # Look for price patterns (฿ followed by numbers)
            if '฿' in line and any(char.isdigit() for char in line):
                if current_product.get('name'):
                    current_product['price'] = line
                    
            # Look for product codes (typically starts with numbers)
            elif line and line[0].isdigit() and len(line) > 5:
                if current_product.get('name') and current_product.get('price'):
                    current_product['sku'] = line
                    products.append(current_product)
                    current_product = {}
                    
            # Look for product names (usually longer text without special chars)
            elif len(line) > 20 and '฿' not in line and not line.startswith('[') and not line.startswith('!'):
                current_product['name'] = line
                
        # Also extract links to individual product pages
        links = result.get('links', [])
        product_links = [link for link in links if '/product/' in link]
        
        print(f"📊 Found {len(products)} products from content parsing")
        print(f"🔗 Found {len(product_links)} product links")
        
        return {
            'page': page_num,
            'url': url,
            'products': products,
            'product_links': product_links,
            'total_products_found': len(products),
            'raw_markdown_length': len(markdown),
            'scraped_at': datetime.now().isoformat()
        }
        
    except Exception as e:
        print(f"❌ Error scraping page {page_num}: {str(e)}")
        return None

async def scrape_all_pages(base_url: str, max_pages: int = 5):
    """Scrape multiple pages of the category"""
    all_results = []
    
    # Extract base URL without page parameter
    if '?page=' in base_url:
        base_url = base_url.split('?page=')[0]
    
    print(f"🎯 Starting to scrape category: {base_url}")
    print(f"📑 Will scrape up to {max_pages} pages")
    
    for page in range(1, max_pages + 1):
        url = f"{base_url}?page={page}"
        result = await scrape_category_page(url, page)
        
        if result:
            all_results.append(result)
            
            # If no products found, might be end of pagination
            if result['total_products_found'] == 0:
                print(f"📍 No products found on page {page}, stopping pagination")
                break
                
        # Add delay between pages to be respectful
        if page < max_pages:
            print(f"⏳ Waiting 2 seconds before next page...")
            await asyncio.sleep(2)
    
    return all_results

async def main():
    """Main function"""
    # The category URL - Wall-mounted air conditioners
    category_url = "https://www.thaiwatsadu.com/en/category/%E0%B9%80%E0%B8%84%E0%B8%A3%E0%B8%B7%E0%B9%88%E0%B8%AD%E0%B8%87%E0%B8%9B%E0%B8%A3%E0%B8%B1%E0%B8%9A%E0%B8%AD%E0%B8%B2%E0%B8%81%E0%B8%B2%E0%B8%A8%E0%B8%95%E0%B8%B4%E0%B8%94%E0%B8%9C%E0%B8%99%E0%B8%B1%E0%B8%87-630201?page=1"
    
    # Decode the category name
    category_name = unquote("เครื่องปรับอากาศติดผนัง")
    print(f"🏷️  Category: {category_name} (Wall-mounted air conditioners)")
    
    # Scrape the category
    results = await scrape_all_pages(category_url, max_pages=3)
    
    if results:
        # Save results to file
        output_file = f"twd_aircon_category_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        
        print(f"\n✅ Scraping completed!")
        print(f"📁 Results saved to: {output_file}")
        
        # Summary
        total_products = sum(r['total_products_found'] for r in results)
        total_links = sum(len(r['product_links']) for r in results)
        
        print(f"\n📊 Summary:")
        print(f"  - Pages scraped: {len(results)}")
        print(f"  - Total products found: {total_products}")
        print(f"  - Total product links: {total_links}")
        
        # Show sample of first few products
        if results and results[0]['products']:
            print(f"\n🛍️  Sample products from page 1:")
            for i, product in enumerate(results[0]['products'][:5], 1):
                print(f"  {i}. {product.get('name', 'N/A')[:60]}...")
                print(f"     Price: {product.get('price', 'N/A')}")
                print(f"     SKU: {product.get('sku', 'N/A')}")
                
    else:
        print("❌ No results obtained")

if __name__ == "__main__":
    asyncio.run(main())