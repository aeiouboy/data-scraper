#!/usr/bin/env python3
"""
Remove the identified DAIKIN model mismatches from the database
"""

import sys
import os
import asyncio
sys.path.append('/Users/chongraktanaka/Documents/Project/ris data scrap')

from src.services.supabase_service import SupabaseService

async def remove_daikin_mismatches():
    """Remove the specific DAIKIN model mismatches that were found"""
    
    # IDs of the mismatches found by the scan
    mismatch_ids = [
        "62c6b28f-1796-4b6d-99b6-3ee75abe4d7e",  # FTKD09ZV2S vs FTM09PV2S
        "e88180c0-5146-48ec-8609-13f05559a2cb",  # FTKC18ZV2S vs FTM18PV2S
        "73ffd0d2-fbe5-4614-97b7-edabf7b57a5b",  # FTKQ18YV2S vs FTM18PV2S
        "c729b6b4-c791-4a92-b037-6fdaa71315e6",  # FTKM15YV2S vs FTM15PV2S
        "d0c81126-a4a8-4b37-a655-ede3c6748df6",  # FTKD24ZV2S vs FTKQ24YV2S
        "35826b94-1b94-446c-803e-12abd52378f4",  # FTKC09ZV2S vs FTM09PV2S
        "330ce587-ccb1-4b18-8dd3-cbd7e3fcb950",  # FTKD18ZV2S vs FTM18PV2S
    ]
    
    db = SupabaseService()
    
    print(f"=== REMOVING {len(mismatch_ids)} DAIKIN MODEL MISMATCHES ===")
    
    removed_count = 0
    for match_id in mismatch_ids:
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
    
    print(f"\nSuccessfully removed {removed_count} out of {len(mismatch_ids)} mismatches.")
    
    if removed_count == len(mismatch_ids):
        print("✅ All DAIKIN model mismatches have been successfully removed!")
    else:
        print(f"⚠️  {len(mismatch_ids) - removed_count} mismatches could not be removed.")

if __name__ == "__main__":
    asyncio.run(remove_daikin_mismatches())