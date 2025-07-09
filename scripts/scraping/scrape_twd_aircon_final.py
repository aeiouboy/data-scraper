#!/usr/bin/env python3
"""Final improved scraper for Thai Watsadu air conditioner category"""

import os
import sys
import asyncio
import json
import re
from datetime import datetime
from urllib.parse import unquote, urljoin
from dotenv import load_dotenv

# Add the app directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Load environment variables
load_dotenv()

from src.services.firecrawl_client import FirecrawlClient

def parse_product_block(block_text: str):
    """Parse a single product block from markdown"""
    product = {}
    
    # Extract SKU (60XXXXXX pattern)
    sku_match = re.search(r'60\d{6}', block_text)
    if sku_match:
        product['sku'] = sku_match.group()
    
    # Extract product name (text between brand link and SKU)
    name_match = re.search(r'\] \[(.*?)\\\\', block_text)
    if name_match:
        product['name'] = name_match.group(1).strip()
    
    # Extract brand
    brand_match = re.search(r'\[([A-Z]+)\]\(https://www\.thaiwatsadu\.com/th/brand/', block_text)
    if brand_match:
        product['brand'] = brand_match.group(1)
    
    # Extract prices
    # Look for pattern: ฿\n\n฿XX,XXX\n\nYY,YYY
    price_pattern = r'฿\\\\\\\\฿([\d,]+)\\\\\\\\([\d,]+)'
    price_match = re.search(price_pattern, block_text)
    if price_match:
        product['original_price'] = f"฿{price_match.group(1)}"
        product['sale_price'] = f"฿{price_match.group(2)}"
    else:
        # Try simpler price pattern
        simple_price = re.search(r'฿([\d,]+)', block_text)
        if simple_price:
            product['price'] = f"฿{simple_price.group(1)}"
    
    # Extract product URL
    url_match = re.search(r'https://www\.thaiwatsadu\.com/th/product/[^\)]+', block_text)
    if url_match:
        product['url'] = url_match.group()
    
    # Extract discount percentage
    discount_match = re.search(r'-(\d+)%', block_text)
    if discount_match:
        product['discount_percentage'] = f"{discount_match.group(1)}%"
    
    # Check for badges/promotions
    if 'ลดเพิ่มทันที' in block_text:
        extra_discount = re.search(r'ลดเพิ่มทันที\\\\\\\\([\d,]+)', block_text)
        if extra_discount:
            product['extra_discount'] = f"฿{extra_discount.group(1)}"
    
    if 'ส่งด่วน' in block_text:
        product['fast_delivery'] = True
        
    return product

def extract_products_from_markdown(markdown: str):
    """Extract all products from markdown content"""
    products = []
    
    # Split by product image pattern (each product starts with an image)
    # Pattern: [![product_name](image_url)
    product_blocks = re.split(r'(?=\[\!\[)', markdown)
    
    for block in product_blocks:
        if '60' in block and 'BTU' in block:  # Likely a product block
            product = parse_product_block(block)
            if product.get('sku'):
                products.append(product)
    
    return products

async def scrape_category_page(url: str, page_num: int = 1):
    """Scrape a single category page with improved parsing"""
    print(f"\n📄 Scraping page {page_num}")
    
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
        
        # Extract total product count from page
        total_match = re.search(r'สินค้ารายการที่\d+ \- \d+จากทั้งหมด(\d+)รายการ', markdown)
        total_products = int(total_match.group(1)) if total_match else None
        
        print(f"📊 Found {len(products)} products on this page")
        if total_products:
            print(f"📈 Total products in category: {total_products}")
        
        return {
            'page': page_num,
            'url': url,
            'products': products,
            'total_products_in_category': total_products,
            'products_on_page': len(products),
            'page_title': metadata.get('title', ''),
            'scraped_at': datetime.now().isoformat()
        }
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return None

async def scrape_all_pages(base_url: str, max_pages: int = 5):
    """Scrape multiple pages of the category"""
    all_results = []
    all_products = []
    
    # Clean base URL
    if '?page=' in base_url:
        base_url = base_url.split('?page=')[0]
    
    print(f"🎯 Starting to scrape Thai Watsadu Air Conditioner category")
    print(f"📑 Will scrape up to {max_pages} pages")
    
    for page in range(1, max_pages + 1):
        url = f"{base_url}?page={page}"
        result = await scrape_category_page(url, page)
        
        if result:
            all_results.append(result)
            all_products.extend(result['products'])
            
            # Check if we've reached the last page
            if result['products_on_page'] == 0:
                print(f"📍 No products found on page {page}, stopping")
                break
                
            # Check if we've scraped all products
            total = result.get('total_products_in_category')
            if total and len(all_products) >= total:
                print(f"✅ Scraped all {total} products")
                break
                
        # Delay between pages
        if page < max_pages and result and result['products_on_page'] > 0:
            print(f"⏳ Waiting 2 seconds...")
            await asyncio.sleep(2)
    
    return all_results, all_products

async def main():
    """Main function"""
    # Category URL
    category_url = "https://www.thaiwatsadu.com/en/category/%E0%B9%80%E0%B8%84%E0%B8%A3%E0%B8%B7%E0%B9%88%E0%B8%AD%E0%B8%87%E0%B8%9B%E0%B8%A3%E0%B8%B1%E0%B8%9A%E0%B8%AD%E0%B8%B2%E0%B8%81%E0%B8%B2%E0%B8%A8%E0%B8%95%E0%B8%B4%E0%B8%94%E0%B8%9C%E0%B8%99%E0%B8%B1%E0%B8%87-630201?page=1"
    
    print("🏷️  Category: Wall-mounted Air Conditioners")
    print("🌐 Site: Thai Watsadu\n")
    
    # Scrape category
    results, all_products = await scrape_all_pages(category_url, max_pages=5)
    
    if all_products:
        # Save detailed results
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # Save all products
        products_file = f"twd_aircon_products_{timestamp}.json"
        with open(products_file, 'w', encoding='utf-8') as f:
            json.dump({
                'category': 'Wall-mounted Air Conditioners',
                'total_products': len(all_products),
                'scraped_at': datetime.now().isoformat(),
                'products': all_products
            }, f, ensure_ascii=False, indent=2)
        
        # Save page-by-page results
        pages_file = f"twd_aircon_pages_{timestamp}.json"
        with open(pages_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        
        print(f"\n✅ Scraping completed!")
        print(f"📁 Products saved to: {products_file}")
        print(f"📁 Page details saved to: {pages_file}")
        
        # Summary
        print(f"\n📊 Summary:")
        print(f"  - Pages scraped: {len(results)}")
        print(f"  - Total products: {len(all_products)}")
        
        # Brand distribution
        brands = {}
        for product in all_products:
            brand = product.get('brand', 'Unknown')
            brands[brand] = brands.get(brand, 0) + 1
        
        print(f"\n🏭 Brands found:")
        for brand, count in sorted(brands.items(), key=lambda x: x[1], reverse=True):
            print(f"  - {brand}: {count} products")
        
        # Price range
        prices = []
        for product in all_products:
            if product.get('sale_price'):
                price_str = product['sale_price'].replace('฿', '').replace(',', '')
                try:
                    prices.append(int(price_str))
                except:
                    pass
        
        if prices:
            print(f"\n💰 Price range:")
            print(f"  - Lowest: ฿{min(prices):,}")
            print(f"  - Highest: ฿{max(prices):,}")
            print(f"  - Average: ฿{sum(prices)//len(prices):,}")
        
        # Sample products
        print(f"\n🛍️  Sample products:")
        for i, product in enumerate(all_products[:5], 1):
            print(f"\n  {i}. {product.get('name', 'N/A')}")
            print(f"     Brand: {product.get('brand', 'N/A')}")
            print(f"     SKU: {product.get('sku', 'N/A')}")
            if product.get('original_price') and product.get('sale_price'):
                print(f"     Price: {product['original_price']} → {product['sale_price']} ({product.get('discount_percentage', '')})")
            else:
                print(f"     Price: {product.get('price', 'N/A')}")
            if product.get('extra_discount'):
                print(f"     Extra discount: {product['extra_discount']}")
            if product.get('fast_delivery'):
                print(f"     ⚡ Fast delivery available")
                
    else:
        print("❌ No products found")

if __name__ == "__main__":
    asyncio.run(main())