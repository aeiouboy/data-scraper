#!/usr/bin/env python3
"""
Retry failed products from import log
"""
import asyncio
import json
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.append(str(project_root))

from src.services.supabase_service import SupabaseService
from src.models.product import Product
from decimal import Decimal
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def retry_failed_product(sku: str):
    """Retry a specific failed product"""
    
    # Load processed data
    data_file = project_root / "data" / "processed_import_data.json"
    
    if not data_file.exists():
        print(f"❌ Data file not found: {data_file}")
        return False
    
    with open(data_file, 'r') as f:
        all_data = json.load(f)
    
    # Find the failed product
    failed_product_data = None
    for item in all_data:
        if item['sku'] == sku:
            failed_product_data = item
            break
    
    if not failed_product_data:
        print(f"❌ Product {sku} not found in data")
        return False
    
    print(f"🔄 Retrying product: {sku}")
    print(f"   Name: {failed_product_data['name']}")
    print(f"   Retailer: {failed_product_data['retailer_code']}")
    
    # Convert to Product object
    try:
        product = Product(
            sku=failed_product_data['sku'],
            retailer_code=failed_product_data['retailer_code'],
            name=failed_product_data['name'],
            brand=failed_product_data.get('brand'),
            category=failed_product_data.get('category'),
            current_price=Decimal(str(failed_product_data['current_price'])) if failed_product_data.get('current_price') else None,
            original_price=Decimal(str(failed_product_data['original_price'])) if failed_product_data.get('original_price') else None,
            discount_percentage=failed_product_data.get('discount_percentage'),
            availability=failed_product_data.get('availability', 'unknown'),
            url=failed_product_data.get('url'),
            image_url=failed_product_data.get('image_url'),
            description=failed_product_data.get('description'),
            specifications=failed_product_data.get('specifications'),
            features=failed_product_data.get('features'),
            usage_instructions=failed_product_data.get('usage_instructions'),
            monitoring_tier=failed_product_data.get('monitoring_tier', 'standard'),
            matching_hash=failed_product_data.get('matching_hash'),
            scraped_at=datetime.fromisoformat(failed_product_data['scraped_at'].replace('Z', '+00:00'))
        )
    except Exception as e:
        print(f"❌ Error creating product object: {e}")
        return False
    
    # Retry import
    supabase = SupabaseService()
    try:
        result = await supabase.upsert_product(product)
        if result:
            print(f"✅ Successfully imported product: {sku}")
            return True
        else:
            print(f"❌ Failed to import product: {sku}")
            return False
    except Exception as e:
        print(f"❌ Error importing product {sku}: {e}")
        return False

async def main():
    """Retry all failed products"""
    
    failed_skus = ["1227651"]  # The one failed product
    
    print(f"🔄 Retrying {len(failed_skus)} failed products...")
    
    success_count = 0
    for sku in failed_skus:
        success = await retry_failed_product(sku)
        if success:
            success_count += 1
        print()  # Empty line
    
    print(f"📊 Retry Results:")
    print(f"   Attempted: {len(failed_skus)}")
    print(f"   Successful: {success_count}")
    print(f"   Failed: {len(failed_skus) - success_count}")
    
    if success_count == len(failed_skus):
        print("🎉 All failed products successfully retried!")
    else:
        print("⚠️  Some products still failed")

if __name__ == "__main__":
    asyncio.run(main())