#!/usr/bin/env python3
"""
Focused batch fix for most critical data quality issues
"""

import json
import logging
import requests
from bs4 import BeautifulSoup
from src.scrapers.strategies.improved_native_strategy import ImprovedNativeStrategy
from src.services.supabase_service import SupabaseService
import time

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class FocusedBatchFixer:
    """Fix most critical data quality issues in focused batches"""
    
    def __init__(self):
        self.supabase = SupabaseService()
        self.improved_strategy = ImprovedNativeStrategy()
        self.stats = {
            'processed': 0,
            'successful': 0,
            'failed': 0,
            'price_fixes': 0,
            'brand_fixes': 0
        }
    
    def fix_hp_critical_batch(self, limit: int = 50) -> dict:
        """Fix critical HP products with missing data"""
        logger.info(f"Fixing HP critical issues (limit: {limit})...")
        
        # Get HP products with missing prices OR brands
        result = self.supabase.client.table('products')\
            .select('id, sku, name, brand, category, url, current_price, original_price')\
            .eq('retailer_code', 'HP')\
            .or_('current_price.is.null,brand.is.null')\
            .limit(limit)\
            .execute()
        
        products = result.data
        logger.info(f"Found {len(products)} HP products to fix")
        
        for product in products:
            try:
                logger.info(f"Processing HP: {product['sku']}")
                
                response = requests.get(product['url'], timeout=30)
                if response.status_code != 200:
                    self.stats['failed'] += 1
                    continue
                
                soup = BeautifulSoup(response.content, 'html.parser')
                
                updates = {}
                
                # Fix price if missing
                if not product.get('current_price'):
                    price_result = self.improved_strategy.extract_improved_price(soup, product['url'])
                    if price_result.get('current_price'):
                        updates['current_price'] = price_result['current_price']
                        self.stats['price_fixes'] += 1
                    if price_result.get('original_price'):
                        updates['original_price'] = price_result['original_price']
                
                # Fix brand if missing
                if not product.get('brand'):
                    brand_result = self.improved_strategy.extract_improved_brand(soup, product['url'])
                    if brand_result:
                        updates['brand'] = brand_result
                        self.stats['brand_fixes'] += 1
                
                # Apply updates
                if updates:
                    update_result = self.supabase.client.table('products')\
                        .update(updates)\
                        .eq('id', product['id'])\
                        .execute()
                    
                    if update_result.data:
                        self.stats['successful'] += 1
                        logger.info(f"✅ Fixed HP {product['sku']}: {list(updates.keys())}")
                    else:
                        self.stats['failed'] += 1
                else:
                    self.stats['failed'] += 1
                
                self.stats['processed'] += 1
                time.sleep(1)  # Be respectful
                
            except Exception as e:
                logger.error(f"Error processing HP {product['sku']}: {str(e)}")
                self.stats['failed'] += 1
        
        return self.stats.copy()
    
    def fix_twd_brands_batch(self, limit: int = 30) -> dict:
        """Fix TWD products with missing brands"""
        logger.info(f"Fixing TWD brand issues (limit: {limit})...")
        
        result = self.supabase.client.table('products')\
            .select('id, sku, name, brand, category, url')\
            .eq('retailer_code', 'TWD')\
            .is_('brand', 'null')\
            .limit(limit)\
            .execute()
        
        products = result.data
        logger.info(f"Found {len(products)} TWD products with missing brands")
        
        for product in products:
            try:
                logger.info(f"Processing TWD: {product['sku']}")
                
                response = requests.get(product['url'], timeout=30)
                if response.status_code != 200:
                    self.stats['failed'] += 1
                    continue
                
                soup = BeautifulSoup(response.content, 'html.parser')
                brand_result = self.improved_strategy.extract_improved_brand(soup, product['url'])
                
                if brand_result:
                    update_result = self.supabase.client.table('products')\
                        .update({'brand': brand_result})\
                        .eq('id', product['id'])\
                        .execute()
                    
                    if update_result.data:
                        self.stats['successful'] += 1
                        self.stats['brand_fixes'] += 1
                        logger.info(f"✅ Fixed TWD brand {product['sku']}: {brand_result}")
                    else:
                        self.stats['failed'] += 1
                else:
                    self.stats['failed'] += 1
                
                self.stats['processed'] += 1
                time.sleep(1)
                
            except Exception as e:
                logger.error(f"Error processing TWD {product['sku']}: {str(e)}")
                self.stats['failed'] += 1
        
        return self.stats.copy()

def main():
    """Run focused batch fixes"""
    fixer = FocusedBatchFixer()
    
    print("🎯 FOCUSED BATCH DATA QUALITY FIX")
    print("=" * 45)
    
    # Phase 1: Fix critical HP issues
    print("\n🏪 Phase 1: HP Critical Issues (50 products)")
    hp_results = fixer.fix_hp_critical_batch(limit=50)
    print(f"  Processed: {hp_results['processed']}")
    print(f"  ✅ Successful: {hp_results['successful']}")
    print(f"  💰 Price fixes: {hp_results['price_fixes']}")
    print(f"  🏷️ Brand fixes: {hp_results['brand_fixes']}")
    
    # Phase 2: Fix TWD brands
    print("\n🏪 Phase 2: TWD Brand Issues (30 products)")
    twd_results = fixer.fix_twd_brands_batch(limit=30)
    print(f"  Processed: {twd_results['processed'] - hp_results['processed']}")
    print(f"  ✅ Additional successful: {twd_results['successful'] - hp_results['successful']}")
    print(f"  🏷️ Additional brand fixes: {twd_results['brand_fixes'] - hp_results['brand_fixes']}")
    
    # Save results
    final_results = {
        'phase_1_hp': hp_results,
        'phase_2_twd': twd_results,
        'total_processed': twd_results['processed'],
        'total_successful': twd_results['successful'],
        'total_price_fixes': twd_results['price_fixes'],
        'total_brand_fixes': twd_results['brand_fixes'],
        'success_rate': (twd_results['successful'] / twd_results['processed'] * 100) if twd_results['processed'] > 0 else 0
    }
    
    with open('focused_batch_fix_results.json', 'w') as f:
        json.dump(final_results, f, indent=2)
    
    print(f"\n📊 BATCH FIX SUMMARY:")
    print(f"  Total processed: {final_results['total_processed']}")
    print(f"  ✅ Total successful: {final_results['total_successful']}")
    print(f"  💰 Price fixes: {final_results['total_price_fixes']}")
    print(f"  🏷️ Brand fixes: {final_results['total_brand_fixes']}")
    print(f"  📈 Success rate: {final_results['success_rate']:.1f}%")
    
    print(f"\n📁 Results saved: focused_batch_fix_results.json")
    print(f"✅ Focused batch fix completed!")

if __name__ == "__main__":
    main()