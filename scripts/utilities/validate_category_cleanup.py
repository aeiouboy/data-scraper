#!/usr/bin/env python3
"""
Validate the category cleanup results
"""
import sys
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).parent))

from src.services.supabase_service import SupabaseService

def main():
    print("📊 CATEGORY CLEANUP VALIDATION")
    print("=" * 50)
    
    service = SupabaseService()
    
    # Check all HomePro products
    print("🔍 Analyzing all HomePro products...")
    
    try:
        # Get total count
        total_response = service.client.table('products').select('count', count='exact').eq('retailer_code', 'HP').execute()
        total_count = total_response.count
        
        # Get products with missing categories
        missing_response = service.client.table('products').select('count', count='exact').eq('retailer_code', 'HP').is_('category', 'null').execute()
        missing_count = missing_response.count
        
        # Get products with empty categories
        empty_response = service.client.table('products').select('count', count='exact').eq('retailer_code', 'HP').eq('category', '').execute()
        empty_count = empty_response.count
        
        # Get products with General category
        general_response = service.client.table('products').select('count', count='exact').eq('retailer_code', 'HP').eq('category', 'General').execute()
        general_count = general_response.count
        
        # Calculate statistics
        problematic_count = missing_count + empty_count + general_count
        good_count = total_count - problematic_count
        success_rate = (good_count / total_count) * 100 if total_count > 0 else 0
        
        print(f"\n📈 RESULTS:")
        print(f"   📦 Total HomePro products: {total_count:,}")
        print(f"   ✅ Products with proper categories: {good_count:,}")
        print(f"   📊 Success rate: {success_rate:.1f}%")
        print(f"\n❌ REMAINING ISSUES:")
        print(f"   🚫 Missing categories (NULL): {missing_count}")
        print(f"   📝 Empty categories (''): {empty_count}")
        print(f"   🏷️ General categories: {general_count}")
        print(f"   🔢 Total problematic: {problematic_count}")
        
        if problematic_count == 0:
            print(f"\n🎉 CLEANUP COMPLETE! All {total_count:,} products have proper categories!")
        else:
            improvement = 100 - ((problematic_count / total_count) * 100)
            print(f"\n💡 Data quality improvement: {improvement:.1f}%")
            print(f"   Before cleanup: ~588 problematic products (58.8%)")
            print(f"   After cleanup: {problematic_count} problematic products ({(problematic_count/total_count)*100:.1f}%)")
        
        # Show sample of well-categorized products
        print(f"\n📋 Sample of properly categorized products:")
        sample_response = service.client.table('products').select('sku,name,category').eq('retailer_code', 'HP').not_.is_('category', 'null').not_.eq('category', '').not_.eq('category', 'General').order('updated_at', desc=True).limit(10).execute()
        
        for i, product in enumerate(sample_response.data[:5], 1):
            print(f"   {i}. {product['sku']}: {product['category']} - {product['name'][:40]}...")
            
    except Exception as e:
        print(f"❌ Error analyzing database: {e}")

if __name__ == "__main__":
    main()