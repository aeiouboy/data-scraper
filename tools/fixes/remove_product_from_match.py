#!/usr/bin/env python3
"""
Remove specific products from match groups to break false positive matches.

This script removes products from match groups instead of deleting entire match groups,
which should avoid foreign key constraint issues.
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '../..'))

from src.services.supabase_service import SupabaseService
import json
import re
from datetime import datetime

def extract_btu_from_name(name):
    """Extract BTU rating from product name"""
    # Try English "BTU" first
    btu_match = re.search(r'(\d{1,3}[,.]?\d{3})\s*BTU', name, re.IGNORECASE)
    if btu_match:
        return int(btu_match.group(1).replace(',', '').replace('.', ''))
    
    # Try Thai "บีทียู"
    btu_match = re.search(r'(\d{1,3}[,.]?\d{3})\s*บีทียู', name, re.IGNORECASE)
    if btu_match:
        return int(btu_match.group(1).replace(',', '').replace('.', ''))
    
    # Try without space
    btu_match = re.search(r'(\d{2,5})\s*(?:BTU|บีทียู)', name, re.IGNORECASE)
    if btu_match:
        return int(btu_match.group(1))
    
    return None

def find_product_by_id(supabase_service, product_id):
    """Find product by ID"""
    try:
        result = supabase_service.client.table('products').select('*').eq('id', product_id).execute()
        return result.data[0] if result.data else None
    except Exception as e:
        print(f"Error finding product {product_id}: {str(e)}")
        return None

def remove_product_from_match_group(supabase_service, product_id, match_group_id):
    """Remove a specific product from a match group"""
    try:
        print(f"Removing product {product_id} from match group {match_group_id}")
        
        # Remove from product_match_mapping
        mapping_result = supabase_service.client.table('product_match_mapping').delete().eq('product_id', product_id).eq('match_group_id', match_group_id).execute()
        
        if mapping_result.data:
            print(f"✅ Successfully removed product from match group")
            return True
        else:
            print(f"❌ Product mapping not found or already removed")
            return False
        
    except Exception as e:
        print(f"❌ Error removing product from match group: {str(e)}")
        return False

def find_matches_for_product(supabase_service, product_id):
    """Find all match groups containing a specific product"""
    try:
        mapping_result = supabase_service.client.table('product_match_mapping').select('*').eq('product_id', product_id).execute()
        
        match_groups = []
        if mapping_result.data:
            for mapping in mapping_result.data:
                match_group_id = mapping['match_group_id']
                
                # Get the full match group
                match_result = supabase_service.client.table('match_groups').select('*').eq('id', match_group_id).execute()
                
                if match_result.data:
                    match_group = match_result.data[0]
                    
                    # Get all products in this match group
                    all_mappings = supabase_service.client.table('product_match_mapping').select('*').eq('match_group_id', match_group_id).execute()
                    
                    product_ids_in_match = [m['product_id'] for m in all_mappings.data] if all_mappings.data else []
                    
                    match_groups.append({
                        'match_group': match_group,
                        'product_ids': product_ids_in_match
                    })
        
        return match_groups
        
    except Exception as e:
        print(f"Error finding matches for product {product_id}: {str(e)}")
        return []

def check_match_group_integrity(supabase_service, match_group_id):
    """Check if a match group still has valid products after removal"""
    try:
        # Get remaining products in the match group
        mappings = supabase_service.client.table('product_match_mapping').select('*').eq('match_group_id', match_group_id).execute()
        
        if not mappings.data or len(mappings.data) < 2:
            print(f"Match group {match_group_id} has fewer than 2 products, cleaning up...")
            
            # Remove remaining mappings
            for mapping in mappings.data:
                supabase_service.client.table('product_match_mapping').delete().eq('id', mapping['id']).execute()
            
            # Remove the match group itself
            supabase_service.client.table('match_groups').delete().eq('id', match_group_id).execute()
            
            print(f"✅ Cleaned up empty match group {match_group_id}")
            return False
        
        return True
        
    except Exception as e:
        print(f"Error checking match group integrity: {str(e)}")
        return True

def main():
    """Main function to remove products from problematic match groups"""
    print("=== REMOVING PRODUCTS FROM FALSE POSITIVE MATCHES ===")
    print("TWD: CARRIER 38TVEA028A42TVEA028A, 25,200 BTU")
    print("HP: CARRIER 42TVAB013ABI, 12,200 BTU")
    print()
    
    # Initialize service
    supabase_service = SupabaseService()
    
    # Product IDs from the user's request
    twd_product_id = "5a9f8605-8eaf-4ee2-80f7-96a03caecf7c"
    hp_product_id = "d6f4581a-ba2a-4756-a0c7-d58f1009d82c"
    
    # 1. Find the products
    print("1. Finding products...")
    twd_product = find_product_by_id(supabase_service, twd_product_id)
    hp_product = find_product_by_id(supabase_service, hp_product_id)
    
    if not twd_product:
        print(f"❌ TWD product not found: {twd_product_id}")
        return
    
    if not hp_product:
        print(f"❌ HP product not found: {hp_product_id}")
        return
    
    print(f"✅ TWD Product: {twd_product['name']}")
    print(f"✅ HP Product: {hp_product['name']}")
    
    # Extract BTU ratings to confirm they're different
    twd_btu = extract_btu_from_name(twd_product['name'])
    hp_btu = extract_btu_from_name(hp_product['name'])
    
    print(f"TWD BTU: {twd_btu}")
    print(f"HP BTU: {hp_btu}")
    
    if twd_btu and hp_btu:
        btu_diff = abs(twd_btu - hp_btu)
        btu_diff_percent = (btu_diff / max(twd_btu, hp_btu)) * 100
        print(f"BTU Difference: {btu_diff} ({btu_diff_percent:.1f}%)")
        
        if btu_diff_percent > 5:
            print("❌ Confirmed: These products have significantly different BTU ratings")
        else:
            print("⚠️  Warning: BTU difference is small - please verify this is a false positive")
    
    # 2. Find matches for each product
    print("\n2. Finding match groups for each product...")
    
    twd_matches = find_matches_for_product(supabase_service, twd_product_id)
    hp_matches = find_matches_for_product(supabase_service, hp_product_id)
    
    print(f"TWD product is in {len(twd_matches)} match group(s)")
    print(f"HP product is in {len(hp_matches)} match group(s)")
    
    # 3. Find common match groups
    twd_match_ids = {m['match_group']['id'] for m in twd_matches}
    hp_match_ids = {m['match_group']['id'] for m in hp_matches}
    
    common_match_ids = twd_match_ids & hp_match_ids
    
    if not common_match_ids:
        print("❌ No common match groups found between these products")
        return
    
    print(f"Found {len(common_match_ids)} common match group(s)")
    
    # 4. Process each common match group
    for match_group_id in common_match_ids:
        print(f"\n--- Processing Match Group {match_group_id} ---")
        
        # Get match group details
        match_result = supabase_service.client.table('match_groups').select('*').eq('id', match_group_id).execute()
        
        if match_result.data:
            match_group = match_result.data[0]
            print(f"Canonical Name: {match_group.get('canonical_name', 'N/A')}")
            print(f"Created: {match_group.get('created_at', 'N/A')}")
        
        # Get all products in this match group
        mappings = supabase_service.client.table('product_match_mapping').select('*').eq('match_group_id', match_group_id).execute()
        
        if mappings.data:
            print(f"Products in group: {len(mappings.data)}")
            
            # Show all products and their BTU ratings
            products_in_group = []
            btus_in_group = []
            
            for mapping in mappings.data:
                product = find_product_by_id(supabase_service, mapping['product_id'])
                if product:
                    products_in_group.append(product)
                    btu = extract_btu_from_name(product['name'])
                    if btu:
                        btus_in_group.append(btu)
                    print(f"  - {product['name'][:80]}... (BTU: {btu}, Retailer: {product['retailer_code']})")
            
            # Calculate BTU variance
            if len(btus_in_group) >= 2:
                min_btu = min(btus_in_group)
                max_btu = max(btus_in_group)
                btu_variance = ((max_btu - min_btu) / min_btu) * 100 if min_btu > 0 else 0
                
                print(f"BTU variance in group: {btu_variance:.1f}%")
                
                if btu_variance > 10:
                    print("❌ Critical BTU variance detected - removing problematic products")
                    
                    # Strategy: Remove products that are outliers in BTU rating
                    # Keep products with similar BTU ratings together
                    
                    # Group products by similar BTU ratings (within 10% tolerance)
                    btu_groups = {}
                    for product in products_in_group:
                        btu = extract_btu_from_name(product['name'])
                        if btu:
                            # Find if this BTU fits in any existing group
                            found_group = False
                            for group_btu in btu_groups:
                                if abs(btu - group_btu) / max(btu, group_btu) <= 0.1:  # 10% tolerance
                                    btu_groups[group_btu].append(product)
                                    found_group = True
                                    break
                            
                            if not found_group:
                                btu_groups[btu] = [product]
                    
                    print(f"Found {len(btu_groups)} BTU groups:")
                    for group_btu, products in btu_groups.items():
                        print(f"  BTU {group_btu}: {len(products)} products")
                    
                    # Keep the largest group, remove others
                    if len(btu_groups) > 1:
                        largest_group = max(btu_groups.values(), key=len)
                        products_to_remove = [p for p in products_in_group if p not in largest_group]
                        
                        print(f"Removing {len(products_to_remove)} products from match group:")
                        for product in products_to_remove:
                            btu = extract_btu_from_name(product['name'])
                            print(f"  - {product['name'][:80]}... (BTU: {btu})")
                            
                            success = remove_product_from_match_group(supabase_service, product['id'], match_group_id)
                            if success:
                                print(f"    ✅ Removed successfully")
                            else:
                                print(f"    ❌ Failed to remove")
                        
                        # Check if the match group still has enough products
                        check_match_group_integrity(supabase_service, match_group_id)
                        
                else:
                    print("✅ BTU variance is within acceptable range")
    
    # 5. Verify the fix
    print("\n3. Verifying fix...")
    
    # Check if the two specific products are still in the same match group
    twd_matches_after = find_matches_for_product(supabase_service, twd_product_id)
    hp_matches_after = find_matches_for_product(supabase_service, hp_product_id)
    
    twd_match_ids_after = {m['match_group']['id'] for m in twd_matches_after}
    hp_match_ids_after = {m['match_group']['id'] for m in hp_matches_after}
    
    common_match_ids_after = twd_match_ids_after & hp_match_ids_after
    
    if common_match_ids_after:
        print(f"❌ Products are still in {len(common_match_ids_after)} common match group(s)")
        for match_id in common_match_ids_after:
            print(f"  - {match_id}")
    else:
        print("✅ Products are no longer in the same match group")
    
    print("\n=== SUMMARY ===")
    print("✅ Script completed successfully")
    if not common_match_ids_after:
        print("✅ False positive match has been resolved")
        print("✅ Data integrity has been restored for price comparisons")
    else:
        print("⚠️  Some match groups may still need manual review")

if __name__ == "__main__":
    main()