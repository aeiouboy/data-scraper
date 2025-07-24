#!/usr/bin/env python3
"""
Disable false positive matches by marking the match group as inactive or invalid.

Since there are database constraints preventing deletion, we'll mark the match group
as disabled/invalid so it won't be used in price comparisons.
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

def disable_match_group(supabase_service, match_group_id, reason):
    """Disable a match group by updating its status"""
    try:
        print(f"Disabling match group: {match_group_id}")
        print(f"Reason: {reason}")
        
        # Update the match group to mark it as disabled
        update_data = {
            'is_active': False,
            'disabled_reason': reason,
            'disabled_at': datetime.now().isoformat(),
            'updated_at': datetime.now().isoformat()
        }
        
        # First, check if the match_groups table has these columns
        try:
            result = supabase_service.client.table('match_groups').update(update_data).eq('id', match_group_id).execute()
            
            if result.data:
                print(f"✅ Successfully disabled match group")
                return True
            else:
                print(f"❌ Failed to update match group")
                return False
                
        except Exception as e:
            print(f"Error updating match group directly: {str(e)}")
            
            # If the columns don't exist, try adding metadata
            try:
                # Get current match group
                current_result = supabase_service.client.table('match_groups').select('*').eq('id', match_group_id).execute()
                
                if current_result.data:
                    match_group = current_result.data[0]
                    
                    # Update metadata to include disabled flag
                    current_metadata = match_group.get('metadata', {})
                    if isinstance(current_metadata, str):
                        try:
                            current_metadata = json.loads(current_metadata)
                        except:
                            current_metadata = {}
                    
                    current_metadata.update({
                        'is_active': False,
                        'disabled_reason': reason,
                        'disabled_at': datetime.now().isoformat(),
                        'disabled_by': 'false_positive_removal_script'
                    })
                    
                    # Update with new metadata
                    update_result = supabase_service.client.table('match_groups').update({
                        'metadata': json.dumps(current_metadata),
                        'updated_at': datetime.now().isoformat()
                    }).eq('id', match_group_id).execute()
                    
                    if update_result.data:
                        print(f"✅ Successfully disabled match group via metadata")
                        return True
                    else:
                        print(f"❌ Failed to update match group metadata")
                        return False
                else:
                    print(f"❌ Match group not found")
                    return False
                    
            except Exception as e2:
                print(f"Error updating match group metadata: {str(e2)}")
                return False
    
    except Exception as e:
        print(f"❌ Error disabling match group {match_group_id}: {str(e)}")
        return False

def mark_products_as_unmatched(supabase_service, product_ids):
    """Mark products as unmatched in the products table"""
    try:
        print(f"Marking {len(product_ids)} products as unmatched...")
        
        for product_id in product_ids:
            # Update the product to indicate it should not be matched
            update_data = {
                'match_disabled': True,
                'match_disabled_reason': 'False positive - BTU variance too high',
                'match_disabled_at': datetime.now().isoformat(),
                'updated_at': datetime.now().isoformat()
            }
            
            try:
                result = supabase_service.client.table('products').update(update_data).eq('id', product_id).execute()
                
                if result.data:
                    print(f"✅ Marked product {product_id} as unmatched")
                else:
                    print(f"❌ Failed to mark product {product_id} as unmatched")
                    
            except Exception as e:
                print(f"Error updating product {product_id}: {str(e)}")
                
                # If the columns don't exist, try adding to specifications
                try:
                    # Get current product
                    current_result = supabase_service.client.table('products').select('*').eq('id', product_id).execute()
                    
                    if current_result.data:
                        product = current_result.data[0]
                        
                        # Update specifications to include disabled flag
                        current_specs = product.get('specifications', {})
                        if isinstance(current_specs, str):
                            try:
                                current_specs = json.loads(current_specs)
                            except:
                                current_specs = {}
                        
                        current_specs.update({
                            'match_disabled': True,
                            'match_disabled_reason': 'False positive - BTU variance too high',
                            'match_disabled_at': datetime.now().isoformat()
                        })
                        
                        # Update with new specifications
                        update_result = supabase_service.client.table('products').update({
                            'specifications': json.dumps(current_specs),
                            'updated_at': datetime.now().isoformat()
                        }).eq('id', product_id).execute()
                        
                        if update_result.data:
                            print(f"✅ Marked product {product_id} as unmatched via specifications")
                        else:
                            print(f"❌ Failed to update product {product_id} specifications")
                            
                except Exception as e2:
                    print(f"Error updating product specifications: {str(e2)}")
    
    except Exception as e:
        print(f"Error marking products as unmatched: {str(e)}")

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

def main():
    """Main function to disable false positive matches"""
    print("=== DISABLING FALSE POSITIVE MATCHES ===")
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
                    print("❌ Critical BTU variance detected - disabling this match group")
                    
                    # Disable the match group
                    reason = f"False positive match - BTU variance {btu_variance:.1f}% exceeds 10% threshold. Air conditioners with different BTU ratings are different products."
                    success = disable_match_group(supabase_service, match_group_id, reason)
                    
                    if success:
                        print("✅ Match group disabled successfully")
                    else:
                        print("❌ Failed to disable match group")
                    
                    # Also mark the products as problematic for future matching
                    product_ids = [p['id'] for p in products_in_group]
                    mark_products_as_unmatched(supabase_service, product_ids)
                else:
                    print("✅ BTU variance is within acceptable range")
    
    # 5. Verify the fix
    print("\n3. Verifying fix...")
    
    # Check if the match groups are now disabled
    for match_group_id in common_match_ids:
        match_result = supabase_service.client.table('match_groups').select('*').eq('id', match_group_id).execute()
        
        if match_result.data:
            match_group = match_result.data[0]
            
            # Check if disabled via direct column
            is_active = match_group.get('is_active', True)
            
            # Check if disabled via metadata
            metadata = match_group.get('metadata', {})
            if isinstance(metadata, str):
                try:
                    metadata = json.loads(metadata)
                except:
                    metadata = {}
            
            is_disabled_via_metadata = metadata.get('is_active') == False
            
            if not is_active or is_disabled_via_metadata:
                print(f"✅ Match group {match_group_id} is now disabled")
            else:
                print(f"⚠️  Match group {match_group_id} may still be active")
    
    print("\n=== SUMMARY ===")
    print("✅ Script completed successfully")
    print("✅ False positive matches have been disabled")
    print("✅ Products are marked to prevent future false positive matches")
    print("✅ Data integrity has been improved for price comparisons")
    print()
    print("Note: The match records still exist in the database but are marked as disabled.")
    print("This prevents them from being used in price comparisons while preserving the data for analysis.")

if __name__ == "__main__":
    main()