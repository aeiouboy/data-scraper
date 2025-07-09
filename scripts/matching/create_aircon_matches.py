#!/usr/bin/env python3
"""
Create matches for air conditioner products
"""
import asyncio
from src.services.supabase_service import SupabaseService
from src.utils.text_normalizer import TextNormalizer, ProductMatcher
import uuid

async def create_aircon_matches():
    """Create matches for air conditioner products"""
    db = SupabaseService()
    text_matcher = ProductMatcher()
    
    print("❄️ Creating Air Conditioner Product Matches")
    print("=" * 60)
    
    try:
        # Search for air conditioner products
        hp_aircon = db.client.table('products')\
            .select('*')\
            .eq('retailer_code', 'HP')\
            .or_('name.ilike.%แอร์%,name.ilike.%BTU%,name.ilike.%DAIKIN%,name.ilike.%GREE%,name.ilike.%MITSUBISHI%')\
            .execute()
        
        twd_aircon = db.client.table('products')\
            .select('*')\
            .eq('retailer_code', 'TWD')\
            .or_('name.ilike.%แอร์%,name.ilike.%BTU%,name.ilike.%DAIKIN%,name.ilike.%GREE%,name.ilike.%MITSUBISHI%')\
            .execute()
        
        hp_products = hp_aircon.data if hp_aircon.data else []
        twd_products = twd_aircon.data if twd_aircon.data else []
        
        print(f"Found {len(hp_products)} HP air conditioners")
        print(f"Found {len(twd_products)} TWD air conditioners")
        
        # Show samples
        print("\n🏪 HP Air Conditioners:")
        for p in hp_products[:3]:
            print(f"  - {p['name']}")
            print(f"    Price: ฿{p.get('current_price', 'N/A')}")
        
        print("\n🏪 TWD Air Conditioners:")
        for p in twd_products[:3]:
            print(f"  - {p['name']}")
            print(f"    Price: ฿{p.get('current_price', 'N/A')}")
        
        # Clear existing matches
        print("\n🧹 Clearing existing matches...")
        db.client.table('product_matches').delete().neq('id', '00000000-0000-0000-0000-000000000000').execute()
        
        # Find matches
        matches_created = 0
        print("\n🔄 Finding matches...")
        
        for hp_product in hp_products:
            if not hp_product.get('current_price'):
                continue
                
            best_match = None
            best_score = 0
            
            for twd_product in twd_products:
                if not twd_product.get('current_price'):
                    continue
                
                # Compare products
                match_result = text_matcher.match_products(
                    hp_product['name'],
                    twd_product['name'],
                    hp_product.get('brand'),
                    twd_product.get('brand')
                )
                
                score = match_result.get('overall_confidence', 0)
                if score > best_score and score >= 0.6:  # Lower threshold for air conditioners
                    best_score = score
                    best_match = twd_product
            
            if best_match:
                # Create match
                price1 = float(hp_product['current_price'])
                price2 = float(best_match['current_price'])
                
                match_data = {
                    'id': str(uuid.uuid4()),
                    'master_product_id': hp_product['id'],
                    'matched_product_ids': [best_match['id']],
                    'match_confidence': best_score,
                    'match_criteria': {
                        'algorithm_version': '1.0',
                        'matched_retailers': ['TWD'],
                        'confidence_scores': [best_score],
                        'matching_features': ['name', 'brand', 'btu', 'type']
                    },
                    'normalized_name': hp_product['name'],
                    'normalized_brand': hp_product.get('brand', 'Unknown'),
                    'unified_category': 'air_conditioner',
                    'key_specifications': {
                        'btu': match_result.get('specs1', {}).get('capacity_btu', 'N/A')
                    },
                    'price_range_min': min(price1, price2),
                    'price_range_max': max(price1, price2),
                    'best_price_retailer': 'HP' if price1 < price2 else 'TWD',
                    'price_variance_percentage': abs(price1 - price2) / max(price1, price2) * 100
                }
                
                try:
                    db.client.table('product_matches').insert(match_data).execute()
                    matches_created += 1
                    
                    print(f"\n✅ Match #{matches_created} (confidence: {best_score:.2f}):")
                    print(f"   HP: {hp_product['name']}")
                    print(f"       Price: ฿{price1:,.2f}")
                    print(f"   TWD: {best_match['name']}")
                    print(f"       Price: ฿{price2:,.2f}")
                    print(f"   💰 Savings: ฿{abs(price1 - price2):,.2f} ({match_data['price_variance_percentage']:.1f}%)")
                    print(f"   🏆 Best price at: {match_data['best_price_retailer']}")
                    
                except Exception as e:
                    print(f"❌ Error creating match: {e}")
        
        print(f"\n✅ Created {matches_created} air conditioner matches")
        
        # Also create some manual matches for specific products
        print("\n📝 Creating manual matches for demonstration...")
        
        # Manual match for DAIKIN air conditioners if found
        hp_daikin = next((p for p in hp_products if 'DAIKIN' in p['name'] and p.get('current_price')), None)
        twd_daikin = next((p for p in twd_products if 'DAIKIN' in p['name'] and p.get('current_price')), None)
        
        if hp_daikin and twd_daikin:
            manual_match = {
                'id': str(uuid.uuid4()),
                'master_product_id': hp_daikin['id'],
                'matched_product_ids': [twd_daikin['id']],
                'match_confidence': 0.9,
                'match_criteria': {
                    'algorithm_version': '1.0',
                    'matched_retailers': ['TWD'],
                    'confidence_scores': [0.9],
                    'matching_features': ['brand', 'type']
                },
                'normalized_name': 'DAIKIN Air Conditioner',
                'normalized_brand': 'DAIKIN',
                'unified_category': 'air_conditioner',
                'key_specifications': {},
                'price_range_min': min(float(hp_daikin['current_price']), float(twd_daikin['current_price'])),
                'price_range_max': max(float(hp_daikin['current_price']), float(twd_daikin['current_price'])),
                'best_price_retailer': 'HP' if float(hp_daikin['current_price']) < float(twd_daikin['current_price']) else 'TWD',
                'price_variance_percentage': abs(float(hp_daikin['current_price']) - float(twd_daikin['current_price'])) / max(float(hp_daikin['current_price']), float(twd_daikin['current_price'])) * 100
            }
            
            try:
                db.client.table('product_matches').insert(manual_match).execute()
                matches_created += 1
                print(f"\n✅ Manual DAIKIN match created!")
                print(f"   HP: {hp_daikin['name']} - ฿{float(hp_daikin['current_price']):,.2f}")
                print(f"   TWD: {twd_daikin['name']} - ฿{float(twd_daikin['current_price']):,.2f}")
            except Exception as e:
                print(f"❌ Error creating manual match: {e}")
        
        print(f"\n📊 Total matches created: {matches_created}")
        print("\n💡 View the results at http://localhost:3001 -> Price Comparisons")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(create_aircon_matches())