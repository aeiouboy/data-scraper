#!/usr/bin/env python3
"""
Scan for potential DAIKIN model mismatches in the database
"""

import sys
import os
import asyncio
import re
sys.path.append('/Users/chongraktanaka/Documents/Project/ris data scrap')

from src.services.supabase_service import SupabaseService

async def scan_daikin_matches():
    """Scan for potential model mismatches in DAIKIN products"""
    
    db = SupabaseService()
    
    print("=== SCANNING FOR DAIKIN MODEL MISMATCHES ===")
    
    # Get all product matches that might contain DAIKIN products
    all_matches_result = db.client.table('product_matches')\
        .select('*')\
        .limit(1000)\
        .execute()
    
    all_matches = all_matches_result.data if all_matches_result.data else []
    
    print(f"Found {len(all_matches)} total product matches to check")
    
    # Model extraction pattern for DAIKIN products
    daikin_pattern = re.compile(r'(F[A-Z]{2,3}\d{2}[A-Z0-9]{2,5})', re.IGNORECASE)
    
    mismatches_found = []
    
    for match in all_matches:
        # Get master product details
        master_id = match.get('master_product_id')
        if not master_id:
            continue
            
        master_result = db.client.table('products')\
            .select('name, brand')\
            .eq('id', master_id)\
            .single()\
            .execute()
        
        if not master_result.data:
            continue
            
        master_name = master_result.data['name']
        master_brand = master_result.data.get('brand', '')
        
        # Check if this is a DAIKIN product
        if 'daikin' not in master_name.lower() and 'daikin' not in master_brand.lower():
            continue
            
        # Extract model from master product
        master_models = daikin_pattern.findall(master_name)
        master_model = master_models[0] if master_models else None
        
        if not master_model:
            continue
        
        # Check each matched product
        for matched_id in match.get('matched_product_ids', []):
            # Get matched product details
            matched_result = db.client.table('products')\
                .select('name, brand')\
                .eq('id', matched_id)\
                .single()\
                .execute()
            
            if matched_result.data:
                matched_name = matched_result.data['name']
                matched_brand = matched_result.data.get('brand', '')
                
                # Check if matched product is also DAIKIN
                if 'daikin' not in matched_name.lower() and 'daikin' not in matched_brand.lower():
                    continue
                    
                matched_models = daikin_pattern.findall(matched_name)
                matched_model = matched_models[0] if matched_models else None
                
                if matched_model and master_model != matched_model:
                    # Extract model series for comparison
                    master_series = re.match(r'^([A-Z]{3,4})', master_model.upper())
                    matched_series = re.match(r'^([A-Z]{3,4})', matched_model.upper())
                    
                    if master_series and matched_series:
                        master_series_str = master_series.group(1)
                        matched_series_str = matched_series.group(1)
                        
                        # Flag if different series
                        if master_series_str != matched_series_str:
                            mismatch_info = {
                                'match_id': match['id'],
                                'confidence': match.get('match_confidence', 0),
                                'master_model': master_model,
                                'matched_model': matched_model,
                                'master_series': master_series_str,
                                'matched_series': matched_series_str,
                                'master_name': master_name,
                                'matched_name': matched_name
                            }
                            mismatches_found.append(mismatch_info)
    
    # Report findings
    print(f"\nFound {len(mismatches_found)} potential DAIKIN model mismatches:")
    
    for i, mismatch in enumerate(mismatches_found, 1):
        print(f"\n{i}. ❌ Model Series Mismatch:")
        print(f"   Match ID: {mismatch['match_id']}")
        print(f"   Confidence: {mismatch['confidence']:.3f}")
        print(f"   Models: {mismatch['master_model']} vs {mismatch['matched_model']}")
        print(f"   Series: {mismatch['master_series']} vs {mismatch['matched_series']}")
        print(f"   Master: {mismatch['master_name'][:80]}...")
        print(f"   Matched: {mismatch['matched_name'][:80]}...")
    
    return mismatches_found

async def remove_mismatches(mismatches):
    """Remove the identified mismatches"""
    
    if not mismatches:
        print("\nNo mismatches to remove.")
        return
    
    db = SupabaseService()
    
    print(f"\n=== REMOVING {len(mismatches)} DAIKIN MODEL MISMATCHES ===")
    
    removed_count = 0
    for mismatch in mismatches:
        match_id = mismatch['match_id']
        
        try:
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
        except Exception as e:
            print(f"❌ Error removing match {match_id}: {str(e)}")
    
    print(f"\nSuccessfully removed {removed_count} out of {len(mismatches)} mismatches.")

if __name__ == "__main__":
    # Scan for mismatches
    mismatches = asyncio.run(scan_daikin_matches())
    
    if mismatches:
        print(f"\n{len(mismatches)} DAIKIN model mismatches found.")
        response = input("Do you want to remove all these mismatches? (yes/no): ")
        if response.lower() in ['yes', 'y']:
            asyncio.run(remove_mismatches(mismatches))
        else:
            print("Skipping removal of mismatches.")
    else:
        print("\n✅ No DAIKIN model mismatches found!")