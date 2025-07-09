#!/usr/bin/env python3
"""Thai Watsadu scraper with proper price extraction"""

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

def parse_product_from_markdown(product_block: str):
    """Parse a single product from markdown block with proper price extraction"""
    product = {}
    
    # Extract SKU
    sku_match = re.search(r'60\d{6}', product_block)
    if sku_match:
        product['sku'] = sku_match.group()
    
    # Extract brand
    brand_match = re.search(r'\[([A-Z]+)\]', product_block)
    if brand_match:
        product['brand'] = brand_match.group(1)
    
    # Extract product name from URL or link text
    name_match = re.search(r'\[(.*?)\\\\\n\\\\nรหัสสินค้า', product_block)
    if name_match:
        name = name_match.group(1).strip()
        # Clean up the name
        name = re.sub(r'\s+', ' ', name)
        product['name'] = name
    
    # Extract URL
    url_match = re.search(r'https://www\.thaiwatsadu\.com/th/product/[^\)]+', product_block)
    if url_match:
        product['url'] = url_match.group()
        # Try to extract name from URL if not found above
        if not product.get('name'):
            url_name = url_match.group().split('/')[-1].split('-60')[0]
            url_name = unquote(url_name).replace('-', ' ')
            product['name'] = url_name
    
    # Extract prices - looking for pattern: ฿\n\n฿XX,XXX\n\nYY,YYY
    # The first price (฿XX,XXX) is the original price
    # The second number (YY,YYY) is the sale price
    price_section = re.search(r'฿\\\\\\\\฿([\d,]+)\\\\\\\\([\d,]+)', product_block)
    if price_section:
        product['original_price'] = f"฿{price_section.group(1)}"
        product['sale_price'] = f"฿{price_section.group(2)}"
        
        # Calculate discount percentage
        try:
            original = int(price_section.group(1).replace(',', ''))
            sale = int(price_section.group(2).replace(',', ''))
            discount_pct = round((original - sale) / original * 100)
            product['discount_percentage'] = f"{discount_pct}%"
        except:
            pass
    
    # Extract additional discount if any
    extra_discount_match = re.search(r'ลดเพิ่มทันที\\\\\\\\([\d,]+)', product_block)
    if extra_discount_match:
        product['extra_discount'] = f"฿{extra_discount_match.group(1)}"
        
        # Calculate final price if we have sale price and extra discount
        if product.get('sale_price'):
            try:
                sale_price = int(product['sale_price'].replace('฿', '').replace(',', ''))
                extra = int(extra_discount_match.group(1).replace(',', ''))
                final_price = sale_price - extra
                product['final_price'] = f"฿{final_price:,}"
            except:
                pass
    
    # Check for fast delivery
    if 'ส่งด่วน' in product_block and 'ภายในวัน' in product_block:
        product['same_day_delivery'] = True
    
    # Extract discount badge percentage (sometimes shown separately)
    discount_badge = re.search(r'-(\d+)%', product_block)
    if discount_badge and not product.get('discount_percentage'):
        product['discount_percentage'] = f"{discount_badge.group(1)}%"
    
    return product

async def scrape_category_page(url: str, page_num: int):
    """Scrape a single category page"""
    print(f"\n📄 Scraping page {page_num}")
    
    client = FirecrawlClient()
    
    try:
        result = await client.scrape(url)
        
        if not result:
            return None
            
        print(f"✅ Page {page_num} scraped successfully")
        
        markdown = result.get('markdown', '')
        
        # Split by product pattern - each product starts with an image link
        product_blocks = re.split(r'(?=\[\!\[)', markdown)
        
        products = []
        for block in product_blocks:
            if '60' in block and ('BTU' in block or 'แอร์' in block):
                product = parse_product_from_markdown(block)
                if product.get('sku'):
                    products.append(product)
        
        # Extract total count
        total_match = re.search(r'จากทั้งหมด(\d+)รายการ', markdown)
        total_products = int(total_match.group(1)) if total_match else None
        
        print(f"📊 Found {len(products)} products on page {page_num}")
        
        return {
            'page': page_num,
            'products': products,
            'total_in_category': total_products
        }
        
    except Exception as e:
        print(f"❌ Error on page {page_num}: {str(e)}")
        return None

async def main():
    """Main scraping function"""
    base_url = "https://www.thaiwatsadu.com/en/category/%E0%B9%80%E0%B8%84%E0%B8%A3%E0%B8%B7%E0%B9%88%E0%B8%AD%E0%B8%87%E0%B8%9B%E0%B8%A3%E0%B8%B1%E0%B8%9A%E0%B8%AD%E0%B8%B2%E0%B8%81%E0%B8%B2%E0%B8%A8%E0%B8%95%E0%B8%B4%E0%B8%94%E0%B8%9C%E0%B8%99%E0%B8%B1%E0%B8%87-630201"
    
    print("🏷️  Thai Watsadu - Wall-mounted Air Conditioners")
    print("💰 Extracting both original and sale prices\n")
    
    all_products = []
    
    # Scrape first 3 pages
    for page in range(1, 4):
        url = f"{base_url}?page={page}"
        result = await scrape_category_page(url, page)
        
        if result and result['products']:
            all_products.extend(result['products'])
            
            # Show first product from each page as example
            if result['products']:
                sample = result['products'][0]
                print(f"\n📦 Sample from page {page}:")
                print(f"   Name: {sample.get('name', 'N/A')}")
                print(f"   Brand: {sample.get('brand', 'N/A')}")
                print(f"   SKU: {sample.get('sku', 'N/A')}")
                if sample.get('original_price') and sample.get('sale_price'):
                    print(f"   Price: {sample['original_price']} → {sample['sale_price']} ({sample.get('discount_percentage', 'N/A')})")
                    if sample.get('extra_discount'):
                        print(f"   Extra: -{sample['extra_discount']} = {sample.get('final_price', 'N/A')}")
                else:
                    print(f"   Price: {sample.get('price', 'N/A')}")
        
        if page < 3:
            print("\n⏳ Waiting 2 seconds...")
            await asyncio.sleep(2)
    
    # Save results
    if all_products:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_file = f"twd_aircon_with_prices_{timestamp}.json"
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump({
                'category': 'Wall-mounted Air Conditioners',
                'site': 'Thai Watsadu',
                'total_products': len(all_products),
                'scraped_at': datetime.now().isoformat(),
                'products': all_products
            }, f, ensure_ascii=False, indent=2)
        
        print(f"\n✅ Scraping completed!")
        print(f"📁 Saved to: {output_file}")
        print(f"📊 Total products: {len(all_products)}")
        
        # Price analysis
        prices_original = []
        prices_sale = []
        prices_final = []
        
        for p in all_products:
            if p.get('original_price'):
                try:
                    prices_original.append(int(p['original_price'].replace('฿', '').replace(',', '')))
                except:
                    pass
            if p.get('sale_price'):
                try:
                    prices_sale.append(int(p['sale_price'].replace('฿', '').replace(',', '')))
                except:
                    pass
            if p.get('final_price'):
                try:
                    prices_final.append(int(p['final_price'].replace('฿', '').replace(',', '')))
                except:
                    pass
        
        print(f"\n💰 Price Analysis:")
        if prices_original:
            print(f"   Original prices: ฿{min(prices_original):,} - ฿{max(prices_original):,}")
        if prices_sale:
            print(f"   Sale prices: ฿{min(prices_sale):,} - ฿{max(prices_sale):,}")
        if prices_final:
            print(f"   Final prices (with extra discount): ฿{min(prices_final):,} - ฿{max(prices_final):,}")

if __name__ == "__main__":
    asyncio.run(main())