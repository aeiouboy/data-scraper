#!/usr/bin/env python3
"""
Fix model matching issues in the database
"""

import sys
import os
import asyncio
import re
sys.path.append('/Users/chongraktanaka/Documents/Project/ris data scrap')

from src.services.supabase_service import SupabaseService

async def remove_incorrect_match():
    """Remove the specific incorrect match"""
    
    db = SupabaseService()
    
    # The incorrect match we found
    incorrect_match_id = "6cc13e03-5d09-4a73-be69-78d9a96fc1f3"
    
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
        print(f"Master Product: {match.get('master_product_name', 'N/A')}")
        print(f"Confidence: {match['match_confidence']}")
        
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

async def find_model_mismatches():
    """Find other potential model mismatches in DAIKIN products"""
    
    db = SupabaseService()
    
    print("\n=== SCANNING FOR OTHER MODEL MISMATCHES ===")
    
    # Get all DAIKIN product matches
    daikin_matches_result = db.client.table('product_matches')\
        .select('*')\
        .ilike('master_product_name', '%daikin%')\
        .limit(100)\
        .execute()
    
    daikin_matches = daikin_matches_result.data if daikin_matches_result.data else []
    
    print(f"Found {len(daikin_matches)} DAIKIN product matches to check")
    
    # Model extraction pattern for DAIKIN products
    model_pattern = re.compile(r'\b([A-Z]{2,6}\d{2,6}[A-Z0-9\-]*)\b')
    
    mismatches_found = []
    
    for match in daikin_matches:
        master_name = match.get('master_product_name', '')
        master_id = match.get('master_product_id')
        
        # Extract model from master product
        master_models = model_pattern.findall(master_name)
        master_model = master_models[0] if master_models else None
        
        if not master_model:
            continue
        
        # Check each matched product
        for matched_id in match.get('matched_product_ids', []):
            # Get matched product details
            matched_result = db.client.table('products')\
                .select('name')\
                .eq('id', matched_id)\
                .single()\
                .execute()
            
            if matched_result.data:
                matched_name = matched_result.data['name']
                matched_models = model_pattern.findall(matched_name)
                matched_model = matched_models[0] if matched_models else None
                
                if matched_model and master_model != matched_model:
                    # Check if models are significantly different
                    # Remove common prefixes/suffixes to compare core model
                    master_core = re.sub(r'^[A-Z]+|[A-Z0-9]+$', '', master_model)
                    matched_core = re.sub(r'^[A-Z]+|[A-Z0-9]+$', '', matched_model)
                    
                    if master_core and matched_core and master_core != matched_core:
                        mismatch_info = {
                            'match_id': match['id'],
                            'confidence': match.get('match_confidence', 0),
                            'master_model': master_model,
                            'matched_model': matched_model,
                            'master_name': master_name,
                            'matched_name': matched_name
                        }
                        mismatches_found.append(mismatch_info)
    
    # Report findings
    print(f"\nFound {len(mismatches_found)} potential model mismatches:")
    
    for mismatch in mismatches_found:
        print(f"\n❌ Model Mismatch Found:")
        print(f"   Match ID: {mismatch['match_id']}")
        print(f"   Confidence: {mismatch['confidence']}")
        print(f"   Models: {mismatch['master_model']} vs {mismatch['matched_model']}")
        print(f"   Master: {mismatch['master_name'][:60]}...")
        print(f"   Matched: {mismatch['matched_name'][:60]}...")
    
    return mismatches_found

async def remove_all_model_mismatches(mismatches):
    """Remove all identified model mismatches"""
    
    if not mismatches:
        print("\nNo mismatches to remove.")
        return
    
    db = SupabaseService()
    
    print(f"\n=== REMOVING {len(mismatches)} MODEL MISMATCHES ===")
    
    removed_count = 0
    for mismatch in mismatches:
        match_id = mismatch['match_id']
        
        # Delete the mismatch
        delete_result = db.client.table('product_matches')\
            .delete()\
            .eq('id', match_id)\
            .execute()
        
        if delete_result.data:
            removed_count += 1
            print(f"✅ Removed match {match_id}")
        else:
            print(f"❌ Failed to remove match {match_id}")
    
    print(f"\nSuccessfully removed {removed_count} out of {len(mismatches)} mismatches.")

if __name__ == "__main__":
    # First remove the known incorrect match
    asyncio.run(remove_incorrect_match())
    
    # Then find and fix other mismatches
    mismatches = asyncio.run(find_model_mismatches())
    
    if mismatches:
        response = input("\nDo you want to remove all these mismatches? (yes/no): ")
        if response.lower() == 'yes':
            asyncio.run(remove_all_model_mismatches(mismatches))
        else:
            print("Skipping removal of additional mismatches.")