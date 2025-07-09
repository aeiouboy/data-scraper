#!/usr/bin/env python3
"""
Analyze products to find potential matches
"""
from src.services.supabase_service import SupabaseService

def analyze_products():
    """Analyze products from different retailers"""
    db = SupabaseService()
    
    print("📊 Analyzing Products for Potential Matches")
    print("=" * 60)
    
    # Get products from each retailer
    hp_result = db.client.table('products').select('name, brand, category, current_price').eq('retailer_code', 'HP').limit(10).execute()
    twd_result = db.client.table('products').select('name, brand, category, current_price').eq('retailer_code', 'TWD').limit(10).execute()
    
    print("\n🏪 HomePro (HP) Sample Products:")
    for p in hp_result.data[:5]:
        print(f"  - {p['name'][:60]}...")
        print(f"    Brand: {p.get('brand', 'N/A')}, Category: {p.get('category', 'N/A')}, Price: ฿{p.get('current_price', 'N/A')}")
    
    print("\n🏪 Thai Watsadu (TWD) Sample Products:")
    for p in twd_result.data[:5]:
        print(f"  - {p['name'][:60]}...")
        print(f"    Brand: {p.get('brand', 'N/A')}, Category: {p.get('category', 'N/A')}, Price: ฿{p.get('current_price', 'N/A')}")
    
    # Check categories
    print("\n📂 Categories in each retailer:")
    hp_cats = db.client.table('products').select('category').eq('retailer_code', 'HP').execute()
    twd_cats = db.client.table('products').select('category').eq('retailer_code', 'TWD').execute()
    
    hp_categories = set(p['category'] for p in hp_cats.data if p.get('category'))
    twd_categories = set(p['category'] for p in twd_cats.data if p.get('category'))
    
    print(f"\nHP Categories: {', '.join(list(hp_categories)[:10])}")
    print(f"\nTWD Categories: {', '.join(list(twd_categories)[:10])}")
    
    common_categories = hp_categories & twd_categories
    print(f"\nCommon Categories: {', '.join(common_categories)}")

if __name__ == "__main__":
    analyze_products()