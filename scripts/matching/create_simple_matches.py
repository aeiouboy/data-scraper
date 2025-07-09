#!/usr/bin/env python3
"""
Simple script to create product matches based on similar names
"""
import asyncio
from src.services.supabase_service import SupabaseService
from src.utils.text_normalizer import TextNormalizer, ProductMatcher
import uuid

async def create_simple_matches():
    """Create matches based on product name similarity"""
    db = SupabaseService()
    text_matcher = ProductMatcher()
    
    print("🔍 Creating Product Matches Based on Name Similarity")
    print("=" * 60)
    
    try:
        # Get all products
        result = db.client.table('products').select('*').execute()
        all_products = result.data if result.data else []
        print(f"Found {len(all_products)} total products")
        
        # Filter products with prices
        products_with_prices = [p for p in all_products if p.get('current_price') is not None]
        print(f"Found {len(products_with_prices)} products with prices")
        
        # Group by retailer
        by_retailer = {}
        for p in products_with_prices:
            retailer = p['retailer_code']
            if retailer not in by_retailer:
                by_retailer[retailer] = []
            by_retailer[retailer].append(p)
        
        print("\nProducts by retailer:")
        for retailer, prods in by_retailer.items():
            print(f"  {retailer}: {len(prods)} products")
        
        # Clear existing matches
        print("\n🧹 Clearing existing matches...")
        db.client.table('product_matches').delete().neq('id', '00000000-0000-0000-0000-000000000000').execute()
        
        # Find matches between retailers
        matches_created = 0
        print("\n🔄 Finding matches...")
        
        # Compare products from different retailers
        if 'HP' in by_retailer and 'TWD' in by_retailer:
            hp_products = by_retailer['HP'][:50]  # Limit to first 50 for testing
            twd_products = by_retailer['TWD'][:50]
            
            for hp_product in hp_products:
                best_match = None
                best_score = 0
                
                for twd_product in twd_products:
                    # Use the text matcher to compare products
                    match_result = text_matcher.match_products(
                        hp_product['name'],
                        twd_product['name'],
                        hp_product.get('brand'),
                        twd_product.get('brand')
                    )
                    
                    score = match_result.get('overall_confidence', 0)
                    if score > best_score and score >= 0.7:  # 70% confidence threshold
                        best_score = score
                        best_match = twd_product
                
                if best_match:
                    # Create a match record
                    price1 = float(hp_product['current_price'])
                    price2 = float(best_match['current_price'])
                    
                    match_data = {
                        'id': str(uuid.uuid4()),
                        'master_product_id': hp_product['id'],
                        'matched_product_ids': [best_match['id']],
                        'match_confidence': best_score,
                        'match_criteria': {
                            'algorithm_version': '1.0',
                            'matched_retailers': [best_match['retailer_code']],
                            'confidence_scores': [best_score],
                            'matching_features': ['name', 'brand']
                        },
                        'normalized_name': hp_product['name'],
                        'normalized_brand': hp_product.get('brand', 'Unknown'),
                        'unified_category': hp_product.get('unified_category', hp_product.get('category', 'unknown')),
                        'key_specifications': {},
                        'price_range_min': min(price1, price2),
                        'price_range_max': max(price1, price2),
                        'best_price_retailer': 'HP' if price1 < price2 else 'TWD',
                        'price_variance_percentage': abs(price1 - price2) / max(price1, price2) * 100 if max(price1, price2) > 0 else 0
                    }
                    
                    try:
                        db.client.table('product_matches').insert(match_data).execute()
                        matches_created += 1
                        
                        if matches_created <= 5:  # Show first 5 matches
                            print(f"\n✅ Match found (confidence: {best_score:.2f}):")
                            print(f"   HP: {hp_product['name']} - ฿{price1:,.2f}")
                            print(f"   TWD: {best_match['name']} - ฿{price2:,.2f}")
                            print(f"   Savings: ฿{abs(price1 - price2):,.2f} ({match_data['price_variance_percentage']:.1f}%)")
                    except Exception as e:
                        print(f"❌ Error creating match: {e}")
        
        print(f"\n✅ Created {matches_created} product matches")
        
        # Show summary
        result = db.client.table('product_matches').select('*').execute()
        all_matches = result.data if result.data else []
        
        if all_matches:
            total_savings = sum(float(m['price_range_max']) - float(m['price_range_min']) for m in all_matches if m.get('price_range_max') and m.get('price_range_min'))
            avg_variance = sum(m['price_variance_percentage'] for m in all_matches if m.get('price_variance_percentage')) / len(all_matches)
            
            print(f"\n📊 Summary:")
            print(f"   Total matches: {len(all_matches)}")
            print(f"   Total potential savings: ฿{total_savings:,.2f}")
            print(f"   Average price variance: {avg_variance:.1f}%")
        
        print("\n💡 Next Steps:")
        print("  1. Go to http://localhost:3001")
        print("  2. Navigate to Price Comparisons")
        print("  3. Enable Multi-Retailer mode")
        print("  4. Select HP and TWD retailers")
        print("  5. You'll see the price comparison data")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(create_simple_matches())