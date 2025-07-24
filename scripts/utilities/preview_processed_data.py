#!/usr/bin/env python3
"""
Preview processed data before import
"""
import json
from pathlib import Path
from typing import Dict, Any
import pandas as pd

def preview_data():
    """Preview processed data"""
    
    # Load processed data
    data_file = Path("/Users/chongraktanaka/Documents/Project/ris data scrap/data/processed_import_data.json")
    
    if not data_file.exists():
        print("❌ Processed data file not found. Please run import_excel_data.py first.")
        return
    
    with open(data_file, 'r', encoding='utf-8') as f:
        products_data = json.load(f)
    
    print(f"📊 Data Preview: {len(products_data)} products")
    print("="*80)
    
    # Show sample products
    print("\n🔍 Sample Products:")
    for i, product in enumerate(products_data[:3]):
        print(f"\nProduct {i+1}:")
        print(f"  Name: {product['name']}")
        print(f"  Brand: {product['brand']}")
        print(f"  Category: {product['category']}")
        print(f"  SKU: {product['sku']}")
        print(f"  Current Price: ฿{product['current_price']}")
        print(f"  Original Price: ฿{product['original_price']}")
        print(f"  Discount: {product['discount_percentage']}%")
        print(f"  Retailer: {product['retailer_name']} ({product['retailer_code']})")
        print(f"  URL: {product['url']}")
        print(f"  Description: {product['description'][:100]}...")
    
    # Create DataFrame for analysis
    df = pd.DataFrame(products_data)
    
    print("\n📈 Data Statistics:")
    print(f"  Total Products: {len(df)}")
    print(f"  HP Products: {len(df[df['retailer_code'] == 'HP'])}")
    print(f"  TWD Products: {len(df[df['retailer_code'] == 'TWD'])}")
    print(f"  Products with Prices: {len(df[df['current_price'].notna()])}")
    print(f"  Products with Brands: {len(df[df['brand'].notna()])}")
    print(f"  Products with Descriptions: {len(df[df['description'] != ''])}")
    
    # Price analysis
    prices = df[df['current_price'].notna()]['current_price'].astype(float)
    if len(prices) > 0:
        print(f"\n💰 Price Analysis:")
        print(f"  Min Price: ฿{prices.min():,.2f}")
        print(f"  Max Price: ฿{prices.max():,.2f}")
        print(f"  Average Price: ฿{prices.mean():,.2f}")
        print(f"  Median Price: ฿{prices.median():,.2f}")
    
    # Brand distribution
    brand_counts = df['brand'].value_counts()
    print(f"\n🏷️  Top 10 Brands:")
    for brand, count in brand_counts.head(10).items():
        print(f"  {brand}: {count} products")
    
    # Category distribution
    category_counts = df['category'].value_counts()
    print(f"\n📂 Categories:")
    for category, count in category_counts.items():
        print(f"  {category}: {count} products")
    
    # Data quality check
    print(f"\n✅ Data Quality Check:")
    
    # Required fields check
    required_fields = ['sku', 'name', 'retailer_code', 'url']
    for field in required_fields:
        missing = df[field].isna().sum() + (df[field] == '').sum()
        print(f"  {field}: {len(df) - missing}/{len(df)} complete ({100*(len(df)-missing)/len(df):.1f}%)")
    
    # Optional fields check
    optional_fields = ['brand', 'category', 'current_price', 'description']
    for field in optional_fields:
        if field in df.columns:
            complete = df[field].notna().sum()
            if field == 'description':
                complete = (df[field] != '').sum()
            print(f"  {field}: {complete}/{len(df)} complete ({100*complete/len(df):.1f}%)")
    
    # Duplicate check
    duplicate_skus = df[df['sku'].duplicated()]
    if len(duplicate_skus) > 0:
        print(f"  ⚠️  Warning: {len(duplicate_skus)} duplicate SKUs found")
    else:
        print(f"  ✅ No duplicate SKUs")
    
    # URL validation
    valid_urls = df['url'].str.contains('http', na=False).sum()
    print(f"  URLs: {valid_urls}/{len(df)} valid ({100*valid_urls/len(df):.1f}%)")
    
    print("\n🎯 Ready for Import!")
    print("Run 'python supabase_import.py' to import to database")

if __name__ == "__main__":
    preview_data()