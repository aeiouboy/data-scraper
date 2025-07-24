#!/usr/bin/env python3
"""
Import script to transform Excel data into database-compatible format
"""
import pandas as pd
import numpy as np
from pathlib import Path
import re
from decimal import Decimal
from datetime import datetime
from typing import List, Dict, Any, Optional
import json
import hashlib
import uuid

# Import project models
import sys
sys.path.append('/Users/chongraktanaka/Documents/Project/ris data scrap')
from src.models.product import Product


class DataCleaner:
    """Clean and transform Excel data for database import"""
    
    def __init__(self):
        self.brand_mapping = {
            'samsung': 'Samsung',
            'lg': 'LG',
            'sharp': 'Sharp',
            'panasonic': 'Panasonic',
            'toshiba': 'Toshiba',
            'hitachi': 'Hitachi',
            'mitsubishi': 'Mitsubishi',
            'daikin': 'Daikin',
            'haier': 'Haier',
            'electrolux': 'Electrolux',
            'whirlpool': 'Whirlpool',
            'bosch': 'Bosch',
            'siemens': 'Siemens',
            'smeg': 'Smeg',
            'tefal': 'Tefal',
            'philips': 'Philips',
            'braun': 'Braun',
            'kenwood': 'Kenwood',
            'kitchenaid': 'KitchenAid',
            'beko': 'Beko',
            'aconatic': 'Aconatic',
            'nemox': 'Nemox',
            'sony': 'Sony',
            'canon': 'Canon',
            'nikon': 'Nikon',
            'fujifilm': 'Fujifilm'
        }
        
        self.category_mapping = {
            'ตู้เย็น': 'Refrigerator',
            'refrigerator': 'Refrigerator',
            'เครื่องซักผ้า': 'Washing Machine',
            'washing machine': 'Washing Machine',
            'เครื่องปรับอากาศ': 'Air Conditioner',
            'air conditioner': 'Air Conditioner',
            'หม้อ': 'Cookware',
            'pressure cooker': 'Cookware',
            'กาแฟ': 'Coffee Machine',
            'coffee': 'Coffee Machine',
            'ไอศกรีม': 'Ice Cream Maker',
            'ice cream': 'Ice Cream Maker',
            'microwave': 'Microwave',
            'oven': 'Oven',
            'mixer': 'Mixer',
            'blender': 'Blender',
            'kettle': 'Kettle',
            'toaster': 'Toaster'
        }
    
    def clean_price(self, price_str: str) -> Optional[Decimal]:
        """Clean price string and convert to Decimal"""
        if pd.isna(price_str) or not price_str:
            return None
            
        price_str = str(price_str).strip()
        
        # Handle "not found" indicators
        if 'ไม่พบ' in price_str.lower() or 'not found' in price_str.lower():
            return None
        
        # Handle price ranges (take the first price)
        if '-' in price_str:
            price_str = price_str.split('-')[0].strip()
        
        # Remove currency symbols and commas
        clean_price = re.sub(r'[฿,$]', '', price_str)
        clean_price = clean_price.replace(',', '').strip()
        
        # Extract numeric value
        numbers = re.findall(r'\d+\.?\d*', clean_price)
        if numbers:
            try:
                return Decimal(str(float(numbers[0])))
            except (ValueError, IndexError):
                return None
        
        return None
    
    def extract_brand(self, product_name: str) -> Optional[str]:
        """Extract brand from product name"""
        if pd.isna(product_name) or not product_name:
            return None
        
        name_lower = product_name.lower()
        
        for brand_key, brand_name in self.brand_mapping.items():
            if brand_key in name_lower:
                return brand_name
        
        return None
    
    def extract_category(self, product_name: str, url: str = None) -> Optional[str]:
        """Extract category from product name or URL"""
        if pd.isna(product_name) or not product_name:
            return None
        
        name_lower = product_name.lower()
        
        # Check URL for category hints
        if url:
            url_lower = url.lower()
            for category_key, category_name in self.category_mapping.items():
                if category_key in url_lower:
                    return category_name
        
        # Check product name
        for category_key, category_name in self.category_mapping.items():
            if category_key in name_lower:
                return category_name
        
        # Default categorization based on common patterns
        if any(keyword in name_lower for keyword in ['ตู้', 'refrigerator', 'fridge']):
            return 'Refrigerator'
        elif any(keyword in name_lower for keyword in ['ซักผ้า', 'washing', 'washer']):
            return 'Washing Machine'
        elif any(keyword in name_lower for keyword in ['ปรับอากาศ', 'air conditioner', 'ac']):
            return 'Air Conditioner'
        elif any(keyword in name_lower for keyword in ['หม้อ', 'cooker', 'pot']):
            return 'Cookware'
        elif any(keyword in name_lower for keyword in ['กาแฟ', 'coffee']):
            return 'Coffee Machine'
        
        return 'Other'
    
    def generate_sku(self, product_name: str, retailer_code: str) -> str:
        """Generate SKU for products without one"""
        # Create a hash of the product name
        name_hash = hashlib.md5(product_name.encode()).hexdigest()[:8]
        return f"{retailer_code}-{name_hash.upper()}"
    
    def calculate_discount_percentage(self, current_price: Decimal, original_price: Decimal) -> Optional[float]:
        """Calculate discount percentage"""
        if not current_price or not original_price or original_price <= current_price:
            return None
        
        discount = ((original_price - current_price) / original_price) * 100
        return round(float(discount), 2)
    
    def generate_product_hash(self, name: str, brand: str = None) -> str:
        """Generate hash for product matching"""
        # Normalize name for matching
        normalized_name = re.sub(r'[^\w\s]', '', name.lower())
        normalized_name = re.sub(r'\s+', ' ', normalized_name).strip()
        
        hash_input = f"{normalized_name}_{brand or 'unknown'}"
        return hashlib.md5(hash_input.encode()).hexdigest()
    
    def clean_hp_data(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        """Clean HP Excel data"""
        products = []
        
        for _, row in df.iterrows():
            # Extract basic fields
            name = row.get('ชื่อสินค้า', '')
            if pd.isna(name) or not name:
                continue
            name = str(name).strip()
                
            # Clean prices
            current_price = self.clean_price(row.get('ราคาส่วนลด', ''))
            original_price = self.clean_price(row.get('ราคาเดิม', ''))
            
            # Extract brand and category
            brand = self.extract_brand(name)
            category = self.extract_category(name, row.get('URL', ''))
            
            # Get or generate SKU
            sku = row.get('SKU', '').strip()
            if not sku:
                sku = self.generate_sku(name, 'HP')
            else:
                # Clean existing SKU
                sku = re.sub(r'SKU:\s*', '', sku)
            
            # Calculate discount
            discount_percentage = None
            if current_price and original_price:
                discount_percentage = self.calculate_discount_percentage(current_price, original_price)
            
            # Handle description field
            description = row.get('รายละเอียดสินค้า', '')
            if pd.isna(description):
                description = ''
            else:
                description = str(description)
            
            # Handle features
            features_raw = row.get('คุณสมบัติ', '')
            features = []
            if not pd.isna(features_raw) and features_raw:
                features = [str(features_raw)]
            
            # Handle specifications
            usage_instructions = row.get('วิธีการใช้งาน', '')
            if pd.isna(usage_instructions):
                usage_instructions = ''
            else:
                usage_instructions = str(usage_instructions)
            
            # Prepare product data
            product_data = {
                'sku': sku,
                'name': name,
                'brand': brand,
                'category': category,
                'unified_category': category,
                'current_price': current_price,
                'original_price': original_price,
                'discount_percentage': discount_percentage,
                'description': description,
                'features': features,
                'specifications': {'usage_instructions': usage_instructions},
                'availability': 'in_stock',
                'images': [],
                'url': row.get('URL', ''),
                'retailer_code': 'HP',
                'retailer_name': 'HomePro',
                'retailer_sku': sku,
                'product_hash': self.generate_product_hash(name, brand),
                'monitoring_tier': 'standard',
                'scraped_at': datetime.now()
            }
            
            products.append(product_data)
        
        return products
    
    def clean_twd_data(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        """Clean TWD Excel data"""
        products = []
        
        for _, row in df.iterrows():
            # Extract basic fields
            name = row.get('name', '')
            if pd.isna(name) or not name:
                continue
            name = str(name).strip()
            
            # Clean prices
            current_price = self.clean_price(row.get('price', ''))
            original_price = self.clean_price(row.get('original_price', ''))
            
            # Extract brand and category
            brand = self.extract_brand(name)
            category = self.extract_category(name, row.get('web-scraper-start-url', ''))
            
            # Generate SKU
            sku = self.generate_sku(name, 'TWD')
            
            # Calculate discount
            discount_percentage = None
            if current_price and original_price:
                discount_percentage = self.calculate_discount_percentage(current_price, original_price)
            
            # Prepare product data
            product_data = {
                'sku': sku,
                'name': name,
                'brand': brand,
                'category': category,
                'unified_category': category,
                'current_price': current_price,
                'original_price': original_price,
                'discount_percentage': discount_percentage,
                'description': '',
                'features': [],
                'specifications': {},
                'availability': 'in_stock',
                'images': [],
                'url': row.get('web-scraper-start-url', ''),
                'retailer_code': 'TWD',
                'retailer_name': 'Thai Watsadu',
                'retailer_sku': sku,
                'product_hash': self.generate_product_hash(name, brand),
                'monitoring_tier': 'standard',
                'scraped_at': datetime.now()
            }
            
            products.append(product_data)
        
        return products


def main():
    """Main function to process Excel files"""
    # File paths
    hp_file = Path("/Users/chongraktanaka/Documents/Project/ris data scrap/data/test_data/hp_data.xlsx")
    twd_file = Path("/Users/chongraktanaka/Documents/Project/ris data scrap/data/test_data/twd_data.xlsx")
    
    # Initialize cleaner
    cleaner = DataCleaner()
    
    # Process HP data
    hp_products = []
    if hp_file.exists():
        print("Processing HP data...")
        hp_df = pd.read_excel(hp_file)
        hp_products = cleaner.clean_hp_data(hp_df)
        print(f"Processed {len(hp_products)} HP products")
    
    # Process TWD data
    twd_products = []
    if twd_file.exists():
        print("Processing TWD data...")
        twd_df = pd.read_excel(twd_file)
        twd_products = cleaner.clean_twd_data(twd_df)
        print(f"Processed {len(twd_products)} TWD products")
    
    # Combine all products
    all_products = hp_products + twd_products
    
    # Generate summary report
    print("\n" + "="*80)
    print("IMPORT SUMMARY")
    print("="*80)
    
    print(f"Total products processed: {len(all_products)}")
    print(f"HP products: {len(hp_products)}")
    print(f"TWD products: {len(twd_products)}")
    
    # Brand distribution
    brands = {}
    categories = {}
    prices = []
    
    for product in all_products:
        brand = product.get('brand', 'Unknown')
        category = product.get('category', 'Unknown')
        price = product.get('current_price')
        
        brands[brand] = brands.get(brand, 0) + 1
        categories[category] = categories.get(category, 0) + 1
        
        if price:
            prices.append(float(price))
    
    print(f"\nBrand distribution:")
    for brand, count in sorted(brands.items(), key=lambda x: x[1], reverse=True)[:10]:
        print(f"  {brand}: {count}")
    
    print(f"\nCategory distribution:")
    for category, count in sorted(categories.items(), key=lambda x: x[1], reverse=True):
        print(f"  {category}: {count}")
    
    if prices:
        print(f"\nPrice statistics:")
        print(f"  Min: ฿{min(prices):,.2f}")
        print(f"  Max: ฿{max(prices):,.2f}")
        print(f"  Average: ฿{sum(prices)/len(prices):,.2f}")
        print(f"  Products with prices: {len(prices)}/{len(all_products)}")
    
    # Save processed data
    output_file = Path("/Users/chongraktanaka/Documents/Project/ris data scrap/data/processed_import_data.json")
    
    # Convert Decimal to float for JSON serialization
    json_products = []
    for product in all_products:
        json_product = product.copy()
        if json_product.get('current_price'):
            json_product['current_price'] = float(json_product['current_price'])
        if json_product.get('original_price'):
            json_product['original_price'] = float(json_product['original_price'])
        if json_product.get('scraped_at'):
            json_product['scraped_at'] = json_product['scraped_at'].isoformat()
        json_products.append(json_product)
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(json_products, f, indent=2, ensure_ascii=False)
    
    print(f"\nProcessed data saved to: {output_file}")
    
    # Validation check
    print("\n" + "="*80)
    print("DATA VALIDATION")
    print("="*80)
    
    validation_errors = []
    
    for i, product in enumerate(all_products):
        try:
            # Try to create a Product model instance
            Product(**product)
        except Exception as e:
            validation_errors.append(f"Product {i+1}: {str(e)}")
    
    if validation_errors:
        print(f"Validation errors found: {len(validation_errors)}")
        for error in validation_errors[:5]:  # Show first 5 errors
            print(f"  {error}")
        if len(validation_errors) > 5:
            print(f"  ... and {len(validation_errors) - 5} more")
    else:
        print("✅ All products pass validation")
    
    print(f"\nData is ready for import to Supabase database")
    print(f"Use the processed data at: {output_file}")


if __name__ == "__main__":
    main()