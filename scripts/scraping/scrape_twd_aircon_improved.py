#!/usr/bin/env python3
"""Improved scraper for Thai Watsadu wall-mounted air conditioner category"""

import os
import sys
import asyncio
import json
import re
from datetime import datetime
from urllib.parse import unquote
from dotenv import load_dotenv

# Add the app directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Load environment variables
load_dotenv()

from src.services.firecrawl_client import FirecrawlClient

def extract_products_from_markdown(markdown: str):
    """Extract product information from markdown content"""
    products = []
    
    # Save raw markdown for inspection
    with open('twd_aircon_raw_markdown.txt', 'w', encoding='utf-8') as f:
        f.write(markdown)
    print("📝 Saved raw markdown to twd_aircon_raw_markdown.txt for inspection")
    
    # Split into lines
    lines = markdown.split('\n')
    
    # Track current product being built
    current_product = {}
    
    for i, line in enumerate(lines):
        line = line.strip()
        
        # Skip empty lines
        if not line:
            continue
            
        # Look for product code pattern (60XXXXXX)
        sku_match = re.search(r'60\d{6}', line)
        if sku_match:
            # If we have a previous product, save it
            if current_product.get('sku'):
                products.append(current_product)
                
            # Start new product
            current_product = {
                'sku': sku_match.group(),
                'raw_line': line
            }
            
        # Look for price patterns
        price_match = re.search(r'฿[\d,]+', line)
        if price_match and current_product:
            if 'price' not in current_product:
                current_product['price'] = price_match.group()
            elif 'sale_price' not in current_product:
                current_product['sale_price'] = price_match.group()
                
        # Look for product names (usually after SKU, before price)
        # Names are typically longer lines without special patterns
        if (current_product.get('sku') and 
            'name' not in current_product and 
            len(line) > 20 and 
            not line.startswith('[') and 
            not line.startswith('!') and
            '฿' not in line and
            'รหัส' not in line):
            current_product['name'] = line
            
    # Don't forget the last product
    if current_product.get('sku'):
        products.append(current_product)
        
    return products

async def scrape_category_with_analysis(url: str, page_num: int = 1):
    """Scrape and analyze a category page"""
    print(f"\n📄 Scraping page {page_num}: {url}")
    
    client = FirecrawlClient()
    
    try:
        # Scrape the page
        result = await client.scrape(url)
        
        if not result:
            print(f"❌ Failed to scrape page {page_num}")
            return None
            
        print(f"✅ Successfully scraped page {page_num}")
        
        # Extract products
        markdown = result.get('markdown', '')
        products = extract_products_from_markdown(markdown)
        
        # Extract metadata
        metadata = result.get('metadata', {})
        
        # Extract links
        links = result.get('links', [])
        product_links = []
        for link in links:
            if '/product/' in link or re.search(r'/\d{8}', link):
                product_links.append(link)
        
        print(f"📊 Found {len(products)} products")
        print(f"🔗 Found {len(product_links)} product links")
        
        return {
            'page': page_num,
            'url': url,
            'products': products,
            'product_links': product_links[:10],  # Limit to first 10 for review
            'metadata': metadata,
            'total_products': len(products),
            'markdown_length': len(markdown),
            'scraped_at': datetime.now().isoformat()
        }
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return None

async def main():
    """Main function"""
    # The category URL
    category_url = "https://www.thaiwatsadu.com/en/category/%E0%B9%80%E0%B8%84%E0%B8%A3%E0%B8%B7%E0%B9%88%E0%B8%AD%E0%B8%87%E0%B8%9B%E0%B8%A3%E0%B8%B1%E0%B8%9A%E0%B8%AD%E0%B8%B2%E0%B8%81%E0%B8%B2%E0%B8%A8%E0%B8%95%E0%B8%B4%E0%B8%94%E0%B8%9C%E0%B8%99%E0%B8%B1%E0%B8%87-630201?page=1"
    
    print("🏷️  Category: Wall-mounted Air Conditioners")
    print("🔍 Analyzing page structure...")
    
    # Scrape just the first page for analysis
    result = await scrape_category_with_analysis(category_url, 1)
    
    if result:
        # Save results
        output_file = f"twd_aircon_improved_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        
        print(f"\n✅ Analysis completed!")
        print(f"📁 Results saved to: {output_file}")
        
        # Show sample products
        if result['products']:
            print(f"\n🛍️  Sample products:")
            for i, product in enumerate(result['products'][:5], 1):
                print(f"\n  {i}. SKU: {product.get('sku', 'N/A')}")
                print(f"     Name: {product.get('name', 'N/A')}")
                print(f"     Price: {product.get('price', 'N/A')}")
                if product.get('sale_price'):
                    print(f"     Sale: {product.get('sale_price')}")
                    
        # Show sample links
        if result['product_links']:
            print(f"\n🔗 Sample product links:")
            for i, link in enumerate(result['product_links'][:3], 1):
                print(f"  {i}. {link}")

if __name__ == "__main__":
    asyncio.run(main())