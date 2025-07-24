#!/usr/bin/env python3
"""
Check database for incorrect product matches
"""

import sys
import os
import asyncio
sys.path.append('/Users/chongraktanaka/Documents/Project/ris data scrap')

from src.services.supabase_service import SupabaseService

async def check_database_matches():
    """Check if the problematic products are matched in the database"""
    
    db = SupabaseService()
    
    # Search for the specific products
    print("=== SEARCHING FOR PROBLEMATIC PRODUCTS ===")
    
    # HomePro product: FCFC30EV2S-WH, 30,000 BTU
    hp_result = db.client.table('products').select('*').ilike('name', '%FCFC30EV2S%').execute()
    hp_products = hp_result.data if hp_result.data else []
    
    # TWD product: FTM18PV2S, 18,090 BTU
    twd_result = db.client.table('products').select('*').ilike('name', '%FTM18PV2S%').execute()
    twd_products = twd_result.data if twd_result.data else []
    
    print(f"Found {len(hp_products)} HomePro products with FCFC30EV2S")
    for product in hp_products:
        print(f"  HP: {product['name']} (ID: {product['id']})")
        print(f"      BTU/Power: {product.get('specifications', {}).get('power', 'N/A')}")
        print(f"      Price: ฿{product.get('current_price', 'N/A')}")
    
    print(f"\nFound {len(twd_products)} TWD products with FTM18PV2S")
    for product in twd_products:
        print(f"  TWD: {product['name']} (ID: {product['id']})")
        print(f"       BTU/Power: {product.get('specifications', {}).get('power', 'N/A')}")
        print(f"       Price: ฿{product.get('current_price', 'N/A')}")
    
    # Check if these are matched in product_matches table
    if hp_products and twd_products:
        print("\n=== CHECKING FOR MATCHES ===")
        
        hp_product_ids = [p['id'] for p in hp_products]
        twd_product_ids = [p['id'] for p in twd_products]
        
        # Check if any HP product is master and TWD is matched
        for hp_id in hp_product_ids:
            matches_result = db.client.table('product_matches')\
                .select('*')\
                .eq('master_product_id', hp_id)\
                .execute()
            
            matches = matches_result.data if matches_result.data else []
            for match in matches:
                matched_ids = match.get('matched_product_ids', [])
                for twd_id in twd_product_ids:
                    if twd_id in matched_ids:
                        print(f"❌ FOUND INCORRECT MATCH!")
                        print(f"   Master: HP product {hp_id}")
                        print(f"   Matched: TWD product {twd_id}")
                        print(f"   Confidence: {match.get('match_confidence', 'N/A')}")
                        print(f"   Price Variance: {match.get('price_variance_percentage', 'N/A')}%")
                        print(f"   Match ID: {match['id']}")
                        return match
        
        # Check if any TWD product is master and HP is matched
        for twd_id in twd_product_ids:
            matches_result = db.client.table('product_matches')\
                .select('*')\
                .eq('master_product_id', twd_id)\
                .execute()
            
            matches = matches_result.data if matches_result.data else []
            for match in matches:
                matched_ids = match.get('matched_product_ids', [])
                for hp_id in hp_product_ids:
                    if hp_id in matched_ids:
                        print(f"❌ FOUND INCORRECT MATCH!")
                        print(f"   Master: TWD product {twd_id}")
                        print(f"   Matched: HP product {hp_id}")
                        print(f"   Confidence: {match.get('match_confidence', 'N/A')}")
                        print(f"   Price Variance: {match.get('price_variance_percentage', 'N/A')}%")
                        print(f"   Match ID: {match['id']}")
                        return match
    
    print("✅ No matches found between these specific products in the database.")
    
    # Check for any DAIKIN air conditioner matches with large BTU differences
    print("\n=== CHECKING FOR OTHER INCORRECT DAIKIN MATCHES ===")
    
    daikin_matches_result = db.client.table('product_matches')\
        .select('*')\
        .ilike('master_product_name', '%daikin%')\
        .ilike('master_product_name', '%btu%')\
        .limit(10)\
        .execute()
    
    daikin_matches = daikin_matches_result.data if daikin_matches_result.data else []
    
    for match in daikin_matches:
        print(f"Match ID: {match['id']}")
        print(f"  Master: {match.get('master_product_name', 'N/A')}")
        print(f"  Confidence: {match.get('match_confidence', 'N/A')}")
        print(f"  Price Variance: {match.get('price_variance_percentage', 'N/A')}%")
        print()
    
    return None

if __name__ == "__main__":
    result = asyncio.run(check_database_matches())