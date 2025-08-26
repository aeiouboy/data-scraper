#!/usr/bin/env python3
"""
Check data statistics from the imported product matches
"""
import sys
from pathlib import Path

# Add project root to path  
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.services.supabase_service import SupabaseService
import json

def check_data_stats():
    """Check comprehensive data statistics"""
    print("🔍 Data Quality Analysis")
    print("=" * 50)
    
    db_service = SupabaseService()
    
    # Get total records
    result = db_service.client.table('product_matches')\
        .select('*', count='exact')\
        .contains('match_criteria', {"source": "imported_json"})\
        .execute()
    
    total_records = result.count if hasattr(result, 'count') else len(result.data or [])
    print(f"📊 Total Records: {total_records:,}")
    
    # Get category breakdown
    category_result = db_service.client.table('product_matches')\
        .select('unified_category', count='exact')\
        .contains('match_criteria', {"source": "imported_json"})\
        .execute()
    
    categories = {}
    for item in category_result.data or []:
        cat = item['unified_category']
        categories[cat] = categories.get(cat, 0) + 1
    
    print(f"\n📋 Categories ({len(categories)}):")
    for cat, count in sorted(categories.items(), key=lambda x: x[1], reverse=True):
        print(f"   {cat}: {count:,} products")
    
    # Get price range analysis
    print(f"\n💰 Price Analysis:")
    
    # Sample some records for price analysis
    sample_result = db_service.client.table('product_matches')\
        .select('price_range_min, price_range_max, price_variance_percentage, best_price_retailer, match_criteria')\
        .contains('match_criteria', {"source": "imported_json"})\
        .limit(100)\
        .execute()
    
    if sample_result.data:
        prices_min = [r['price_range_min'] for r in sample_result.data if r.get('price_range_min')]
        prices_max = [r['price_range_max'] for r in sample_result.data if r.get('price_range_max')]
        variances = [r['price_variance_percentage'] for r in sample_result.data if r.get('price_variance_percentage')]
        
        if prices_min and prices_max:
            print(f"   Price Range: ฿{min(prices_min):,.0f} - ฿{max(prices_max):,.0f}")
            print(f"   Average Min Price: ฿{sum(prices_min)/len(prices_min):,.0f}")
            print(f"   Average Max Price: ฿{sum(prices_max)/len(prices_max):,.0f}")
        
        if variances:
            print(f"   Average Price Variance: {sum(variances)/len(variances):.1f}%")
            print(f"   Max Price Variance: {max(variances):.1f}%")
    
    # Get retailer distribution
    print(f"\n🏪 Retailer Analysis:")
    retailers = {}
    for item in sample_result.data or []:
        criteria = item.get('match_criteria', {})
        retailers_list = criteria.get('retailers', [])
        for retailer in retailers_list:
            retailers[retailer] = retailers.get(retailer, 0) + 1
    
    for retailer, count in sorted(retailers.items(), key=lambda x: x[1], reverse=True):
        print(f"   {retailer}: {count} samples")
    
    print(f"\n✅ Data import successful!")
    print(f"📊 Ready for price comparisons: {total_records:,} products")
    print(f"🌐 Frontend: http://localhost:3000/price-comparisons")
    print(f"🔗 API: http://localhost:8001/api/price-comparisons-direct/comparisons-direct")

if __name__ == "__main__":
    check_data_stats()