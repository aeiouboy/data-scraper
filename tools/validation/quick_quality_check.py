#!/usr/bin/env python3
"""
Quick data quality validation check
"""

import json
from src.services.supabase_service import SupabaseService

def main():
    """Quick quality check"""
    supabase = SupabaseService()
    
    print("🔍 QUICK DATA QUALITY CHECK")
    print("=" * 40)
    
    # Get total products
    total_result = supabase.client.table('products').select('id', count='exact').execute()
    total = total_result.count
    
    # Missing brands
    brands_result = supabase.client.table('products').select('id', count='exact').is_('brand', 'null').execute()
    missing_brands = brands_result.count
    
    # Missing prices  
    prices_result = supabase.client.table('products').select('id', count='exact').is_('current_price', 'null').execute()
    missing_prices = prices_result.count
    
    # Generic categories
    categories_result = supabase.client.table('products').select('id', count='exact').in_('category', ['Other', 'General']).execute()
    generic_categories = categories_result.count
    
    # Calculate percentages
    brand_completeness = ((total - missing_brands) / total * 100) if total > 0 else 0
    price_completeness = ((total - missing_prices) / total * 100) if total > 0 else 0
    category_specificity = ((total - generic_categories) / total * 100) if total > 0 else 0
    
    print(f"\n📊 CURRENT METRICS:")
    print(f"  Total products: {total:,}")
    print(f"  Missing brands: {missing_brands} ({brand_completeness:.1f}% complete)")
    print(f"  Missing prices: {missing_prices} ({price_completeness:.1f}% complete)")
    print(f"  Generic categories: {generic_categories} ({category_specificity:.1f}% specific)")
    
    # Get HP specific stats
    hp_total = supabase.client.table('products').select('id', count='exact').eq('retailer_code', 'HP').execute().count
    hp_missing_brands = supabase.client.table('products').select('id', count='exact').eq('retailer_code', 'HP').is_('brand', 'null').execute().count
    hp_missing_prices = supabase.client.table('products').select('id', count='exact').eq('retailer_code', 'HP').is_('current_price', 'null').execute().count
    
    print(f"\n🏪 HP SPECIFIC:")
    print(f"  Total HP products: {hp_total}")
    print(f"  Missing brands: {hp_missing_brands}")
    print(f"  Missing prices: {hp_missing_prices}")
    
    # Get TWD specific stats
    twd_total = supabase.client.table('products').select('id', count='exact').eq('retailer_code', 'TWD').execute().count
    twd_missing_brands = supabase.client.table('products').select('id', count='exact').eq('retailer_code', 'TWD').is_('brand', 'null').execute().count
    twd_missing_prices = supabase.client.table('products').select('id', count='exact').eq('retailer_code', 'TWD').is_('current_price', 'null').execute().count
    
    print(f"\n🏪 TWD SPECIFIC:")
    print(f"  Total TWD products: {twd_total}")
    print(f"  Missing brands: {twd_missing_brands}")
    print(f"  Missing prices: {twd_missing_prices}")
    
    # Summary
    results = {
        'total_products': total,
        'missing_brands': missing_brands,
        'missing_prices': missing_prices,
        'generic_categories': generic_categories,
        'quality_metrics': {
            'brand_completeness': round(brand_completeness, 1),
            'price_completeness': round(price_completeness, 1),
            'category_specificity': round(category_specificity, 1)
        },
        'hp_stats': {
            'total': hp_total,
            'missing_brands': hp_missing_brands,
            'missing_prices': hp_missing_prices
        },
        'twd_stats': {
            'total': twd_total,
            'missing_brands': twd_missing_brands,
            'missing_prices': twd_missing_prices
        }
    }
    
    with open('quick_quality_check_results.json', 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\n✅ Quality check completed!")
    print(f"📁 Results saved: quick_quality_check_results.json")

if __name__ == "__main__":
    main()