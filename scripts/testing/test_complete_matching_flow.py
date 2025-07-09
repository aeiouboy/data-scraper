#!/usr/bin/env python3
"""
Test complete product matching flow with real products
"""
import asyncio
import json
from src.services.supabase_service import SupabaseService
from src.services.product_matcher import ProductMatcher, ProductMatchAnalyzer

async def test_complete_flow():
    """Test the complete product matching flow"""
    
    print("🚀 Testing Complete Product Matching Flow")
    print("=" * 60)
    
    # Initialize services
    supabase = SupabaseService()
    matcher = ProductMatcher()
    analyzer = ProductMatchAnalyzer()
    
    # Step 1: Get some real products from database
    print("\n1️⃣ Fetching products from database...")
    try:
        # Get products from different retailers
        result = await supabase.search_products(
            query='',
            filters={},
            limit=20
        )
        
        if result and result['products']:
            products = result['products']
            print(f"   ✅ Found {len(products)} products")
            
            # Group by retailer
            by_retailer = {}
            for product in products:
                retailer = product.get('retailer_code', 'Unknown')
                if retailer not in by_retailer:
                    by_retailer[retailer] = []
                by_retailer[retailer].append(product)
            
            print(f"   📊 Products by retailer:")
            for retailer, prods in by_retailer.items():
                print(f"      - {retailer}: {len(prods)} products")
                
        else:
            print("   ⚠️  No products found in database")
            return
            
    except Exception as e:
        print(f"   ❌ Error fetching products: {str(e)}")
        return
    
    # Step 2: Test product matching between retailers
    print("\n2️⃣ Testing cross-retailer matching...")
    
    # If we have products from multiple retailers, try to match them
    if len(by_retailer) > 1:
        retailers = list(by_retailer.keys())
        product1 = by_retailer[retailers[0]][0]  # First product from first retailer
        
        print(f"\n   Base product:")
        print(f"   - Name: {product1['name']}")
        print(f"   - Retailer: {product1['retailer_name']}")
        print(f"   - SKU: {product1.get('sku', 'N/A')}")
        print(f"   - Price: ฿{product1.get('current_price', 0):,.2f}")
        
        # Convert dict to Product object
        from src.models.product import Product
        base_product = Product(**product1)
        
        # Find matches
        matches = await matcher.find_product_matches(base_product)
        
        if matches:
            print(f"\n   Found {len(matches)} potential matches:")
            for matched_product, criteria in matches[:3]:  # Show top 3
                print(f"\n   Match confidence: {criteria.overall_confidence:.1%}")
                print(f"   - Name: {matched_product.name}")
                print(f"   - Retailer: {matched_product.retailer_name}")
                print(f"   - Price: ฿{matched_product.current_price:,.2f}")
                print(f"   - Name similarity: {criteria.name_similarity:.1%}")
                print(f"   - Brand match: {'✅' if criteria.brand_match else '❌'}")
                print(f"   - Category match: {'✅' if criteria.category_match else '❌'}")
        else:
            print("   ℹ️  No matches found for this product")
    
    # Step 3: Test batch processing
    print("\n\n3️⃣ Testing batch product matching...")
    try:
        # Process a small batch
        results = await matcher.process_all_products(limit=10)
        
        print(f"   ✅ Batch processing results:")
        print(f"      - Total products: {results['total_products']}")
        print(f"      - Matches created: {results['matches_created']}")
        print(f"      - Retailers: {', '.join(results['retailers_processed'])}")
        print(f"      - Categories: {len(results['categories_matched'])}")
        print(f"      - Savings identified: ฿{results['price_savings_identified']:,.2f}")
        
    except Exception as e:
        print(f"   ❌ Error in batch processing: {str(e)}")
    
    # Step 4: Test analytics
    print("\n\n4️⃣ Testing analytics generation...")
    try:
        # Generate price comparison report
        report = await analyzer.generate_price_comparison_report()
        
        print(f"   📊 Price Comparison Report:")
        print(f"      - Total matches: {report['total_matches']}")
        print(f"      - Avg price variance: {report['price_variance_stats']['average_variance']:.1f}%")
        print(f"      - Max price variance: {report['price_variance_stats']['max_variance']:.1f}%")
        
        if report['savings_opportunities']:
            print(f"\n   💰 Top savings opportunities:")
            for opp in report['savings_opportunities'][:3]:
                print(f"      - {opp['product_name']}")
                print(f"        Price range: {opp['price_range']}")
                print(f"        Savings: ฿{opp['savings_amount']:,.2f}")
                print(f"        Best retailer: {opp['best_retailer']}")
        
    except Exception as e:
        print(f"   ⚠️  Analytics not available yet (need product matches): {str(e)}")
    
    print("\n" + "=" * 60)
    print("✅ Complete flow testing finished!")

if __name__ == "__main__":
    asyncio.run(test_complete_flow())