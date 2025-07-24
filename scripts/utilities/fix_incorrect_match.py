#!/usr/bin/env python3
"""
Fix the incorrect product match in database
"""

import sys
import os
import asyncio
sys.path.append('/Users/chongraktanaka/Documents/Project/ris data scrap')

from src.services.supabase_service import SupabaseService

async def fix_incorrect_match():
    """Remove the incorrect match from database"""
    
    db = SupabaseService()
    
    # The match ID we found
    incorrect_match_id = "569e42f3-097e-4792-921e-db5863a0e884"
    
    print("=== REMOVING INCORRECT MATCH ===")
    print(f"Match ID: {incorrect_match_id}")
    
    # Get details before deletion
    match_result = db.client.table('product_matches')\
        .select('*')\
        .eq('id', incorrect_match_id)\
        .single()\
        .execute()
    
    if match_result.data:
        match = match_result.data
        print(f"Master Product ID: {match['master_product_id']}")
        print(f"Matched Product IDs: {match['matched_product_ids']}")
        print(f"Confidence: {match['match_confidence']}")
        print(f"Price Variance: {match['price_variance_percentage']}%")
        
        # Delete the incorrect match
        delete_result = db.client.table('product_matches')\
            .delete()\
            .eq('id', incorrect_match_id)\
            .execute()
        
        if delete_result.data:
            print("✅ Successfully removed incorrect match!")
        else:
            print("❌ Failed to remove match")
    else:
        print("❌ Match not found")

async def check_for_other_incorrect_matches():
    """Check for other potential incorrect matches"""
    
    db = SupabaseService()
    
    print("\n=== CHECKING FOR OTHER INCORRECT MATCHES ===")
    
    # Find matches with very high price variance and high confidence
    # This suggests potential mismatches
    suspicious_matches_result = db.client.table('product_matches')\
        .select('*')\
        .gte('price_variance_percentage', 50)\
        .gte('match_confidence', 0.8)\
        .limit(20)\
        .execute()
    
    suspicious_matches = suspicious_matches_result.data if suspicious_matches_result.data else []
    
    print(f"Found {len(suspicious_matches)} potentially incorrect matches:")
    
    for match in suspicious_matches:
        print(f"\nMatch ID: {match['id']}")
        print(f"  Master: {match.get('master_product_name', 'N/A')}")
        print(f"  Confidence: {match.get('match_confidence', 'N/A')}")
        print(f"  Price Variance: {match.get('price_variance_percentage', 'N/A')}%")
        
        # Get product details to check for BTU differences
        master_result = db.client.table('products')\
            .select('name')\
            .eq('id', match['master_product_id'])\
            .single()\
            .execute()
        
        if master_result.data:
            master_name = master_result.data['name']
            
            # Check for BTU in name
            import re
            master_btu = re.search(r'(\d+(?:,\d+)?)\s*(?:btu|บีทียู)', master_name, re.IGNORECASE)
            if master_btu:
                master_btu_val = int(master_btu.group(1).replace(',', ''))
                
                # Check matched products for BTU
                for matched_id in match.get('matched_product_ids', []):
                    matched_result = db.client.table('products')\
                        .select('name')\
                        .eq('id', matched_id)\
                        .single()\
                        .execute()
                    
                    if matched_result.data:
                        matched_name = matched_result.data['name']
                        matched_btu = re.search(r'(\d+(?:,\d+)?)\s*(?:btu|บีทียู)', matched_name, re.IGNORECASE)
                        
                        if matched_btu:
                            matched_btu_val = int(matched_btu.group(1).replace(',', ''))
                            btu_diff = abs(master_btu_val - matched_btu_val) / master_btu_val
                            
                            if btu_diff > 0.3:  # More than 30% BTU difference
                                print(f"    ⚠️  BTU mismatch: {master_btu_val:,} vs {matched_btu_val:,} ({btu_diff*100:.1f}% diff)")

if __name__ == "__main__":
    asyncio.run(fix_incorrect_match())
    asyncio.run(check_for_other_incorrect_matches())