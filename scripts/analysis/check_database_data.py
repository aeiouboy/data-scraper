#!/usr/bin/env python3
"""
Check database for existing data
"""
import asyncio
from src.services.supabase_service import SupabaseService

async def check_data():
    """Check what data exists in the database"""
    db = SupabaseService()
    
    print("🔍 Checking Database Data")
    print("=" * 60)
    
    # Check products
    try:
        result = db.client.table('products').select('*').limit(5).execute()
        product_count = len(result.data) if result.data else 0
        print(f"\n📦 Products: {product_count} found")
        if result.data:
            print("Sample products:")
            for p in result.data[:3]:
                print(f"  - {p['name']} ({p['retailer_code']}) - ฿{p.get('current_price', 'N/A')}")
    except Exception as e:
        print(f"❌ Error checking products: {e}")
    
    # Check product_matches
    try:
        result = db.client.table('product_matches').select('*').limit(5).execute()
        match_count = len(result.data) if result.data else 0
        print(f"\n🔗 Product Matches: {match_count} found")
    except Exception as e:
        print(f"❌ Error checking matches: {e}")
    
    # Check match_history
    try:
        result = db.client.table('match_history').select('*').limit(5).execute()
        history_count = len(result.data) if result.data else 0
        print(f"\n📜 Match History: {history_count} found")
    except Exception as e:
        print(f"❌ Error checking history: {e}")
    
    # Check price_histories
    try:
        result = db.client.table('price_histories').select('*').limit(5).execute()
        price_count = len(result.data) if result.data else 0
        print(f"\n💰 Price Histories: {price_count} found")
    except Exception as e:
        print(f"❌ Error checking price histories: {e}")
    
    # Check retailers
    try:
        result = db.client.table('retailers').select('*').execute()
        print(f"\n🏪 Retailers: {len(result.data)} found")
        for r in result.data:
            print(f"  - {r['name']} ({r['code']})")
    except Exception as e:
        print(f"❌ Error checking retailers: {e}")
    
    print("\n" + "=" * 60)
    print("💡 Next Steps:")
    if product_count == 0:
        print("  1. No products found - need to scrape some products first")
        print("  2. Use the Scraping page to add products")
    else:
        print("  1. Products exist - can create matches")
        print("  2. Run 'Process New Products' in Price Tracking Dashboard")

if __name__ == "__main__":
    asyncio.run(check_data())