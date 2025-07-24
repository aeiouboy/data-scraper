#!/usr/bin/env python3
"""
Targeted fix for remaining critical data quality issues
"""

import asyncio
import logging
from typing import List, Dict, Any
import json
import requests
from bs4 import BeautifulSoup
from src.scrapers.strategies.improved_native_strategy import ImprovedNativeStrategy
from src.services.supabase_service import SupabaseService
import time

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('targeted_fix_remaining.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class TargetedFixer:
    """Fix remaining critical data quality issues with targeted approach"""
    
    def __init__(self):
        self.supabase = SupabaseService()
        self.improved_strategy = ImprovedNativeStrategy()
    
    def fix_remaining_hp_prices(self, limit: int = 100) -> Dict[str, Any]:
        """Fix remaining HP products with missing prices"""
        logger.info(f"Fixing remaining HP products with missing prices (limit: {limit})...")
        
        # Get HP products with missing prices
        result = self.supabase.client.table('products')\
            .select('id, sku, name, brand, category, url, current_price, original_price')\
            .eq('retailer_code', 'HP')\
            .is_('current_price', 'null')\
            .limit(limit)\
            .execute()
        
        products = result.data
        logger.info(f"Found {len(products)} HP products with missing prices")
        
        fixed_count = 0
        failed_count = 0
        
        for product in products:
            try:
                logger.info(f"Processing HP product: {product['sku']}")
                
                # Fetch and extract
                response = requests.get(product['url'], timeout=30)
                if response.status_code != 200:
                    failed_count += 1
                    continue
                
                soup = BeautifulSoup(response.content, 'html.parser')
                price_result = self.improved_strategy.extract_improved_price(soup, product['url'])
                category_result = self.improved_strategy.extract_improved_category(soup, product['url'])
                
                # Prepare updates
                updates = {}
                if price_result.get('current_price'):
                    updates['current_price'] = price_result['current_price']
                if price_result.get('original_price'):
                    updates['original_price'] = price_result['original_price']
                if price_result.get('discount_percentage'):
                    updates['discount_percentage'] = price_result['discount_percentage']
                if category_result and product.get('category') in ['Other', 'General', None]:
                    updates['category'] = category_result
                
                # Apply updates
                if updates:
                    update_result = self.supabase.client.table('products')\
                        .update(updates)\
                        .eq('id', product['id'])\
                        .execute()
                    
                    if update_result.data:
                        fixed_count += 1
                        logger.info(f"✅ Fixed HP product {product['sku']} - Price: {price_result.get('current_price', 'N/A')}")
                    else:
                        failed_count += 1
                else:
                    failed_count += 1
                
                # Small delay to be respectful
                time.sleep(0.5)
                
            except Exception as e:
                logger.error(f"Error processing HP product {product['sku']}: {str(e)}")
                failed_count += 1
        
        return {
            'total_processed': len(products),
            'fixed': fixed_count,
            'failed': failed_count,
            'success_rate': fixed_count / len(products) * 100 if products else 0
        }
    
    def fix_remaining_brands(self, limit: int = 50) -> Dict[str, Any]:
        """Fix remaining products with missing brands"""
        logger.info(f"Fixing remaining products with missing brands (limit: {limit})...")
        
        # Get products with missing brands
        result = self.supabase.client.table('products')\
            .select('id, sku, name, brand, category, url, retailer_code')\
            .is_('brand', 'null')\
            .limit(limit)\
            .execute()
        
        products = result.data
        logger.info(f"Found {len(products)} products with missing brands")
        
        fixed_count = 0
        failed_count = 0
        
        for product in products:
            try:
                logger.info(f"Processing product: {product['sku']}")
                
                # Fetch and extract
                response = requests.get(product['url'], timeout=30)
                if response.status_code != 200:
                    failed_count += 1
                    continue
                
                soup = BeautifulSoup(response.content, 'html.parser')
                brand_result = self.improved_strategy.extract_improved_brand(soup, product['url'])
                
                # Apply brand update
                if brand_result:
                    update_result = self.supabase.client.table('products')\
                        .update({'brand': brand_result})\
                        .eq('id', product['id'])\
                        .execute()
                    
                    if update_result.data:
                        fixed_count += 1
                        logger.info(f"✅ Fixed brand for {product['sku']}: {brand_result}")
                    else:
                        failed_count += 1
                else:
                    failed_count += 1
                
                # Small delay to be respectful
                time.sleep(0.5)
                
            except Exception as e:
                logger.error(f"Error processing product {product['sku']}: {str(e)}")
                failed_count += 1
        
        return {
            'total_processed': len(products),
            'fixed': fixed_count,
            'failed': failed_count,
            'success_rate': fixed_count / len(products) * 100 if products else 0
        }
    
    def fix_generic_categories(self, limit: int = 50) -> Dict[str, Any]:
        """Fix products with generic categories"""
        logger.info(f"Fixing products with generic categories (limit: {limit})...")
        
        # Get products with generic categories
        result = self.supabase.client.table('products')\
            .select('id, sku, name, brand, category, url, retailer_code')\
            .in_('category', ['Other', 'General'])\
            .limit(limit)\
            .execute()
        
        products = result.data
        logger.info(f"Found {len(products)} products with generic categories")
        
        fixed_count = 0
        failed_count = 0
        
        for product in products:
            try:
                logger.info(f"Processing product: {product['sku']}")
                
                # Fetch and extract
                response = requests.get(product['url'], timeout=30)
                if response.status_code != 200:
                    failed_count += 1
                    continue
                
                soup = BeautifulSoup(response.content, 'html.parser')
                category_result = self.improved_strategy.extract_improved_category(soup, product['url'])
                
                # Apply category update
                if category_result:
                    update_result = self.supabase.client.table('products')\
                        .update({'category': category_result})\
                        .eq('id', product['id'])\
                        .execute()
                    
                    if update_result.data:
                        fixed_count += 1
                        logger.info(f"✅ Fixed category for {product['sku']}: {category_result}")
                    else:
                        failed_count += 1
                else:
                    failed_count += 1
                
                # Small delay to be respectful
                time.sleep(0.5)
                
            except Exception as e:
                logger.error(f"Error processing product {product['sku']}: {str(e)}")
                failed_count += 1
        
        return {
            'total_processed': len(products),
            'fixed': fixed_count,
            'failed': failed_count,
            'success_rate': fixed_count / len(products) * 100 if products else 0
        }

def main():
    """Main function to run targeted fixes"""
    fixer = TargetedFixer()
    
    print("🎯 TARGETED DATA QUALITY FIXES")
    print("=" * 50)
    
    # Fix HP prices
    print("\n💰 Fixing HP products with missing prices...")
    hp_results = fixer.fix_remaining_hp_prices(limit=100)
    print(f"  ✅ Fixed: {hp_results['fixed']}/{hp_results['total_processed']} ({hp_results['success_rate']:.1f}%)")
    
    # Fix missing brands
    print("\n🏷️ Fixing products with missing brands...")
    brand_results = fixer.fix_remaining_brands(limit=50)
    print(f"  ✅ Fixed: {brand_results['fixed']}/{brand_results['total_processed']} ({brand_results['success_rate']:.1f}%)")
    
    # Fix generic categories
    print("\n📂 Fixing products with generic categories...")
    category_results = fixer.fix_generic_categories(limit=50)
    print(f"  ✅ Fixed: {category_results['fixed']}/{category_results['total_processed']} ({category_results['success_rate']:.1f}%)")
    
    # Summary
    total_fixed = hp_results['fixed'] + brand_results['fixed'] + category_results['fixed']
    total_processed = hp_results['total_processed'] + brand_results['total_processed'] + category_results['total_processed']
    
    print(f"\n📊 OVERALL SUMMARY:")
    print(f"  Total products processed: {total_processed}")
    print(f"  Total fixes applied: {total_fixed}")
    print(f"  Overall success rate: {total_fixed/total_processed*100:.1f}%")
    
    # Save results
    results = {
        'hp_prices': hp_results,
        'brands': brand_results,
        'categories': category_results,
        'summary': {
            'total_processed': total_processed,
            'total_fixed': total_fixed,
            'success_rate': total_fixed/total_processed*100
        }
    }
    
    with open('targeted_fix_results.json', 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\n📁 Files created:")
    print(f"  - targeted_fix_results.json")
    print(f"  - targeted_fix_remaining.log")
    
    print(f"\n✅ Targeted fixes completed!")

if __name__ == "__main__":
    main()