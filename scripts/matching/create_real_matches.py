#!/usr/bin/env python3
"""
Create real product matches from existing scraped products
"""
import asyncio
from src.services.supabase_service import SupabaseService
from src.services.product_matcher import ProductMatcher
from src.models.product import Product
from datetime import datetime

async def create_real_matches():
    """Find and create matches from existing products"""
    db = SupabaseService()
    matcher = ProductMatcher()
    
    print("🔍 Creating Real Product Matches from Scraped Data")
    print("=" * 60)
    
    # Get all products grouped by retailer
    try:
        result = db.client.table('products').select('*').execute()
        all_products = result.data if result.data else []
        print(f"Found {len(all_products)} total products")
        
        # Group products by retailer
        products_by_retailer = {}
        for product in all_products:
            retailer = product['retailer_code']
            if retailer not in products_by_retailer:
                products_by_retailer[retailer] = []
            products_by_retailer[retailer].append(product)
        
        print("\nProducts by retailer:")
        for retailer, products in products_by_retailer.items():
            print(f"  {retailer}: {len(products)} products")
        
        # Clear existing matches
        print("\n🧹 Clearing existing sample matches...")
        db.client.table('product_matches').delete().neq('id', '00000000-0000-0000-0000-000000000000').execute()
        
        # Process products to find matches
        print("\n🔄 Processing products for matching...")
        
        # Use the ProductMatcher's process_all_products method directly
        # It will handle the product loading internally
        
        # Process all products to find matches
        results = await matcher.process_all_products()
        
        print(f"\n✅ Matching Results:")
        print(f"  - Total products processed: {results['total_products']}")
        print(f"  - Matches created: {results['matches_created']}")
        print(f"  - Retailers involved: {results['retailers_processed']}")
        print(f"  - Categories matched: {results['categories_matched']}")
        print(f"  - Total savings identified: ฿{results['price_savings_identified']:,.2f}")
        
        # Get some example matches
        print("\n📊 Sample Matches Created:")
        matches_result = db.client.table('product_matches').select('*').limit(5).execute()
        sample_matches = matches_result.data if matches_result.data else []
        
        for match in sample_matches:
            print(f"\n  Product: {match['normalized_name']}")
            print(f"  Category: {match['unified_category']}")
            print(f"  Price Range: ฿{float(match['price_range_min']):,.2f} - ฿{float(match['price_range_max']):,.2f}")
            print(f"  Best Price: {match['best_price_retailer']}")
            print(f"  Variance: {match['price_variance_percentage']:.1f}%")
        
        print("\n💡 Next Steps:")
        print("  1. Refresh the Price Comparisons page")
        print("  2. Enable Multi-Retailer mode")
        print("  3. You'll see real price comparisons from your scraped data")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(create_real_matches())