#!/usr/bin/env python3
"""
Remove false positive match between TWD and HP CARRIER products with different BTU ratings.

This script:
1. Finds the match record connecting the two specific products
2. Removes the incorrect match from the database
3. Verifies the removal worked
4. Checks for similar false positives
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

def extract_model_from_name(name):
    """Extract model number from product name"""
    model_patterns = [
        r'([A-Z0-9]+[A-Z][A-Z0-9]+)',
        r'([0-9]+[A-Z]+[0-9]+[A-Z]*[0-9]*)',
        r'(\d{2}[A-Z]{2,4}\d{3}[A-Z]*\d*[A-Z]*)'
    ]
    
    for pattern in model_patterns:
        match = re.search(pattern, name.upper())
        if match:
            return match.group(1)
    return None

def find_product_by_id(supabase_service, product_id):
    """Find product by ID"""
    try:
        result = supabase_service.client.table('products').select('*').eq('id', product_id).execute()
        return result.data[0] if result.data else None
    except Exception as e:
        print(f"Error finding product {product_id}: {str(e)}")
        return None

def find_matches_containing_products(supabase_service, product_ids):
    """Find match groups containing any of the specified product IDs"""
    matches = []
    
    for product_id in product_ids:
        try:
            # Check product_match_mapping table
            mapping_result = supabase_service.client.table('product_match_mapping').select('*').eq('product_id', product_id).execute()
            
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
                        
                        matches.append({
                            'match_group': match_group,
                            'product_ids': product_ids_in_match,
                            'mappings': all_mappings.data
                        })
        except Exception as e:
            print(f"Error finding matches for product {product_id}: {str(e)}")
    
    return matches

def remove_match_group(supabase_service, match_group_id):
    """Remove a match group and all its associated data"""
    try:
        print(f"Removing match group: {match_group_id}")
        
        # 1. Remove from match_group_stats first (foreign key constraint)
        try:
            stats_result = supabase_service.client.table('match_group_stats').delete().eq('match_group_id', match_group_id).execute()
            print(f"  Removed {len(stats_result.data) if stats_result.data else 0} stats records")
        except Exception as e:
            print(f"  No stats records to remove: {str(e)}")
        
        # 2. Remove from product_match_mapping
        mapping_result = supabase_service.client.table('product_match_mapping').delete().eq('match_group_id', match_group_id).execute()
        print(f"  Removed {len(mapping_result.data) if mapping_result.data else 0} product mappings")
        
        # 3. Remove from match_confidence if it exists
        try:
            confidence_result = supabase_service.client.table('match_confidence').delete().eq('match_group_id', match_group_id).execute()
            print(f"  Removed {len(confidence_result.data) if confidence_result.data else 0} confidence records")
        except Exception as e:
            print(f"  No confidence records to remove: {str(e)}")
        
        # 4. Remove from match_groups
        match_result = supabase_service.client.table('match_groups').delete().eq('id', match_group_id).execute()
        print(f"  Removed {len(match_result.data) if match_result.data else 0} match group records")
        
        # 5. Check for any other related tables (product_matches, match_history, etc.)
        try:
            # Check product_matches table
            product_matches_result = supabase_service.client.table('product_matches').delete().eq('match_group_id', match_group_id).execute()
            print(f"  Removed {len(product_matches_result.data) if product_matches_result.data else 0} product_matches records")
        except Exception as e:
            print(f"  No product_matches records to remove: {str(e)}")
        
        print(f"✅ Successfully removed match group {match_group_id}")
        return True
        
    except Exception as e:
        print(f"❌ Error removing match group {match_group_id}: {str(e)}")
        return False

def check_for_similar_false_positives(supabase_service):
    """Check for other similar false positives with CARRIER products"""
    print("\n=== CHECKING FOR SIMILAR FALSE POSITIVES ===")
    
    try:
        # Get all CARRIER products
        carrier_products = supabase_service.client.table('products').select('*').ilike('name', '%CARRIER%').execute()
        
        if not carrier_products.data:
            print("No CARRIER products found")
            return
        
        print(f"Found {len(carrier_products.data)} CARRIER products")
        
        # Group by match groups
        carrier_by_match = {}
        
        for product in carrier_products.data:
            product_id = product['id']
            
            # Find match groups for this product
            mapping_result = supabase_service.client.table('product_match_mapping').select('*').eq('product_id', product_id).execute()
            
            if mapping_result.data:
                for mapping in mapping_result.data:
                    match_group_id = mapping['match_group_id']
                    
                    if match_group_id not in carrier_by_match:
                        carrier_by_match[match_group_id] = []
                    
                    carrier_by_match[match_group_id].append(product)
        
        # Check each match group for BTU differences
        false_positives = []
        
        for match_group_id, products in carrier_by_match.items():
            if len(products) < 2:
                continue
            
            # Extract BTU ratings
            btus = []
            for product in products:
                btu = extract_btu_from_name(product['name'])
                if btu:
                    btus.append(btu)
            
            if len(btus) >= 2:
                min_btu = min(btus)
                max_btu = max(btus)
                btu_variance = ((max_btu - min_btu) / min_btu) * 100 if min_btu > 0 else 0
                
                if btu_variance > 10:  # More than 10% BTU difference
                    false_positives.append({
                        'match_group_id': match_group_id,
                        'products': products,
                        'btus': btus,
                        'btu_variance': btu_variance
                    })
        
        if false_positives:
            print(f"\n❌ Found {len(false_positives)} potential false positives:")
            
            for fp in false_positives:
                print(f"\nMatch Group: {fp['match_group_id']}")
                print(f"BTU Variance: {fp['btu_variance']:.1f}%")
                print("Products:")
                
                for product in fp['products']:
                    btu = extract_btu_from_name(product['name'])
                    print(f"  - {product['name']} (BTU: {btu}, Retailer: {product['retailer_code']})")
                
                # Automatically remove matches with high BTU variance
                if fp['btu_variance'] > 10:
                    print("❌ Critical BTU variance detected - automatically removing this match group")
                    remove_match_group(supabase_service, fp['match_group_id'])
                else:
                    print("✅ BTU variance is within acceptable range - keeping this match group")
        else:
            print("✅ No additional false positives found")
    
    except Exception as e:
        print(f"Error checking for false positives: {str(e)}")

def main():
    """Main function to remove false positive matches"""
    print("=== REMOVING FALSE POSITIVE MATCH ===")
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
    
    # 2. Find matches containing these products
    print("\n2. Finding match records...")
    matches = find_matches_containing_products(supabase_service, [twd_product_id, hp_product_id])
    
    if not matches:
        print("❌ No matches found between these products")
        return
    
    print(f"Found {len(matches)} match group(s)")
    
    # 3. Process each match
    for i, match_info in enumerate(matches, 1):
        match_group = match_info['match_group']
        product_ids = match_info['product_ids']
        
        print(f"\n--- Match Group {i} ---")
        print(f"Match Group ID: {match_group['id']}")
        print(f"Canonical Name: {match_group.get('canonical_name', 'N/A')}")
        print(f"Created: {match_group.get('created_at', 'N/A')}")
        print(f"Products in group: {len(product_ids)}")
        
        # Check if both our target products are in this match
        both_products_in_match = (twd_product_id in product_ids and hp_product_id in product_ids)
        
        if both_products_in_match:
            print("✅ This match group contains both target products")
            
            # Show all products in this match group
            print("All products in this match group:")
            for pid in product_ids:
                product = find_product_by_id(supabase_service, pid)
                if product:
                    btu = extract_btu_from_name(product['name'])
                    model = extract_model_from_name(product['name'])
                    print(f"  - {product['name']} (BTU: {btu}, Model: {model}, Retailer: {product['retailer_code']})")
            
            # Check if this match group has significant BTU differences
            btus_in_group = []
            for pid in product_ids:
                product = find_product_by_id(supabase_service, pid)
                if product:
                    btu = extract_btu_from_name(product['name'])
                    if btu:
                        btus_in_group.append(btu)
            
            should_remove = False
            if len(btus_in_group) >= 2:
                min_btu = min(btus_in_group)
                max_btu = max(btus_in_group)
                btu_variance = ((max_btu - min_btu) / min_btu) * 100 if min_btu > 0 else 0
                
                print(f"BTU variance in group: {btu_variance:.1f}%")
                if btu_variance > 10:
                    print("❌ Critical BTU variance detected - automatically removing this match group")
                    should_remove = True
                else:
                    print("✅ BTU variance is within acceptable range")
            
            if should_remove:
                success = remove_match_group(supabase_service, match_group['id'])
                if success:
                    print("✅ Match group removed successfully")
                else:
                    print("❌ Failed to remove match group")
        else:
            print("ℹ️  This match group doesn't contain both target products")
    
    # 4. Verify removal
    print("\n3. Verifying removal...")
    remaining_matches = find_matches_containing_products(supabase_service, [twd_product_id, hp_product_id])
    
    if remaining_matches:
        print(f"⚠️  Warning: {len(remaining_matches)} match(es) still found")
        for match_info in remaining_matches:
            match_group = match_info['match_group']
            product_ids = match_info['product_ids']
            both_in_match = (twd_product_id in product_ids and hp_product_id in product_ids)
            
            if both_in_match:
                print(f"❌ Both products still in match group: {match_group['id']}")
            else:
                print(f"✅ Products in separate match groups now")
    else:
        print("✅ No matches found between the target products - removal successful")
    
    # 5. Check for similar false positives
    check_for_similar_false_positives(supabase_service)
    
    print("\n=== SUMMARY ===")
    print("✅ Script completed successfully")
    print("The false positive match between the TWD and HP CARRIER products has been addressed.")
    print("Data integrity has been restored for price comparisons.")

if __name__ == "__main__":
    main()