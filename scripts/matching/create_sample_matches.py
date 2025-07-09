#!/usr/bin/env python3
"""
Create sample product matches for testing the UI
"""
import asyncio
from src.services.supabase_service import SupabaseService
from src.services.product_matcher import ProductMatcher
import uuid
from decimal import Decimal

async def create_sample_matches():
    """Create sample matches for existing products"""
    db = SupabaseService()
    matcher = ProductMatcher()
    
    print("🔧 Creating Sample Product Matches")
    print("=" * 60)
    
    # Get all products
    try:
        result = db.client.table('products').select('*').execute()
        products = result.data if result.data else []
        print(f"Found {len(products)} products")
        
        if len(products) < 2:
            print("❌ Need at least 2 products to create matches")
            return
        
        # Create a sample match for demonstration
        # Group products by similar names
        created_matches = 0
        
        # Manually create some matches for similar products
        for i in range(0, min(len(products), 10), 2):
            if i + 1 < len(products):
                product1 = products[i]
                product2 = products[i + 1]
                
                # Get prices safely
                price1 = float(product1['current_price']) if product1.get('current_price') is not None else 0
                price2 = float(product2['current_price']) if product2.get('current_price') is not None else 0
                
                # Skip if both have no prices
                if price1 == 0 and price2 == 0:
                    continue
                
                # Create match data
                match_data = {
                    'id': str(uuid.uuid4()),
                    'master_product_id': product1['id'],
                    'matched_product_ids': [product2['id']],
                    'match_confidence': 0.85,
                    'match_criteria': {
                        'algorithm_version': '1.0',
                        'matched_retailers': [product2['retailer_code']],
                        'confidence_scores': [0.85],
                        'matching_features': ['name', 'brand', 'category']
                    },
                    'normalized_name': product1['name'],
                    'normalized_brand': product1.get('brand', 'Unknown'),
                    'unified_category': product1.get('unified_category', 'electronics'),
                    'key_specifications': {},
                    'price_range_min': min(price1, price2) if price1 > 0 and price2 > 0 else price1 or price2,
                    'price_range_max': max(price1, price2) if price1 > 0 and price2 > 0 else price1 or price2,
                    'best_price_retailer': product1['retailer_code'] if price1 < price2 else product2['retailer_code'],
                    'price_variance_percentage': abs(price1 - price2) / max(price1, price2) * 100 if price1 > 0 and price2 > 0 else 0
                }
                
                try:
                    result = db.client.table('product_matches').insert(match_data).execute()
                    print(f"✅ Created match: {product1['name'][:50]}...")
                    created_matches += 1
                except Exception as e:
                    print(f"❌ Error creating match: {e}")
        
        # Also create some match history entries
        print("\n📜 Creating Match History...")
        try:
            history_data = {
                'id': str(uuid.uuid4()),
                'product1_id': products[0]['id'],
                'product2_id': products[1]['id'] if len(products) > 1 else products[0]['id'],
                'match_score': 0.85,
                'match_details': {
                    'name_similarity': 0.8,
                    'brand_match': True,
                    'sku_match': False,
                    'spec_match': 0.7
                },
                'user_decision': 'pending',
                'created_by': 'system'
            }
            
            result = db.client.table('match_history').insert(history_data).execute()
            print("✅ Created match history entry")
        except Exception as e:
            print(f"❌ Error creating match history: {e}")
        
        print(f"\n✅ Successfully created {created_matches} product matches")
        print("\n💡 Next Steps:")
        print("  1. Refresh the Price Comparisons page")
        print("  2. You should now see data in the dashboard")
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    asyncio.run(create_sample_matches())