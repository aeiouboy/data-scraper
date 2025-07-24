#!/usr/bin/env python3
"""
Verify that the false positive match fix is working correctly.
"""

import sys
import os
sys.path.append('/Users/chongraktanaka/Documents/Project/ris data scrap')

from src.services.supabase_service import SupabaseService
import json
import re

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

def check_product_match_disabled(product):
    """Check if a product has been marked as match disabled"""
    # Check specifications for match_disabled flag
    specs = product.get('specifications', {})
    if isinstance(specs, str):
        try:
            specs = json.loads(specs)
        except:
            specs = {}
    
    is_disabled = specs.get('match_disabled', False)
    disabled_reason = specs.get('match_disabled_reason', '')
    disabled_at = specs.get('match_disabled_at', '')
    
    return is_disabled, disabled_reason, disabled_at

def main():
    """Main verification function"""
    print("=== VERIFYING FALSE POSITIVE FIX ===")
    
    # Initialize service
    supabase_service = SupabaseService()
    
    # Product IDs from the user's request
    twd_product_id = "5a9f8605-8eaf-4ee2-80f7-96a03caecf7c"
    hp_product_id = "d6f4581a-ba2a-4756-a0c7-d58f1009d82c"
    
    # 1. Check if products are marked as match disabled
    print("1. Checking if products are marked as match disabled...")
    
    twd_product = find_product_by_id(supabase_service, twd_product_id)
    hp_product = find_product_by_id(supabase_service, hp_product_id)
    
    if not twd_product or not hp_product:
        print("❌ Could not find one or both products")
        return
    
    # Check TWD product
    twd_disabled, twd_reason, twd_disabled_at = check_product_match_disabled(twd_product)
    print(f"TWD Product: {twd_product['name'][:60]}...")
    print(f"  Match Disabled: {twd_disabled}")
    if twd_disabled:
        print(f"  Reason: {twd_reason}")
        print(f"  Disabled At: {twd_disabled_at}")
    
    # Check HP product
    hp_disabled, hp_reason, hp_disabled_at = check_product_match_disabled(hp_product)
    print(f"\nHP Product: {hp_product['name'][:60]}...")
    print(f"  Match Disabled: {hp_disabled}")
    if hp_disabled:
        print(f"  Reason: {hp_reason}")
        print(f"  Disabled At: {hp_disabled_at}")
    
    # 2. Check if they're still in the same match group
    print("\n2. Checking current match group memberships...")
    
    twd_mappings = supabase_service.client.table('product_match_mapping').select('*').eq('product_id', twd_product_id).execute()
    hp_mappings = supabase_service.client.table('product_match_mapping').select('*').eq('product_id', hp_product_id).execute()
    
    twd_match_ids = {m['match_group_id'] for m in twd_mappings.data} if twd_mappings.data else set()
    hp_match_ids = {m['match_group_id'] for m in hp_mappings.data} if hp_mappings.data else set()
    
    common_match_ids = twd_match_ids & hp_match_ids
    
    print(f"TWD product is in {len(twd_match_ids)} match group(s)")
    print(f"HP product is in {len(hp_match_ids)} match group(s)")
    print(f"Common match groups: {len(common_match_ids)}")
    
    if common_match_ids:
        print("⚠️  Products are still in the same match group(s):")
        for match_id in common_match_ids:
            print(f"  - {match_id}")
    else:
        print("✅ Products are no longer in the same match group")
    
    # 3. Check the specific match group that was problematic
    problematic_match_id = "28049e86-a525-48ba-8720-abb462fc1042"
    print(f"\n3. Checking problematic match group {problematic_match_id}...")
    
    # Get match group details
    match_result = supabase_service.client.table('match_groups').select('*').eq('id', problematic_match_id).execute()
    
    if match_result.data:
        match_group = match_result.data[0]
        print(f"Match group still exists: {match_group.get('canonical_name', 'N/A')}")
        
        # Get products in this match group
        mappings = supabase_service.client.table('product_match_mapping').select('*').eq('match_group_id', problematic_match_id).execute()
        
        if mappings.data:
            print(f"Products still in this match group: {len(mappings.data)}")
            
            btus_in_group = []
            for mapping in mappings.data:
                product = find_product_by_id(supabase_service, mapping['product_id'])
                if product:
                    btu = extract_btu_from_name(product['name'])
                    if btu:
                        btus_in_group.append(btu)
                    
                    # Check if this product is disabled
                    is_disabled, reason, disabled_at = check_product_match_disabled(product)
                    disabled_flag = "🚫 DISABLED" if is_disabled else "✅ ACTIVE"
                    
                    print(f"  - {product['name'][:60]}... (BTU: {btu}, {disabled_flag})")
            
            if len(btus_in_group) >= 2:
                min_btu = min(btus_in_group)
                max_btu = max(btus_in_group)
                btu_variance = ((max_btu - min_btu) / min_btu) * 100 if min_btu > 0 else 0
                print(f"Current BTU variance: {btu_variance:.1f}%")
                
                if btu_variance > 10:
                    print("❌ BTU variance still exceeds 10% threshold")
                else:
                    print("✅ BTU variance is within acceptable range")
        else:
            print("✅ No products found in this match group")
    else:
        print("✅ Match group has been deleted")
    
    # 4. Test price comparison query behavior
    print("\n4. Testing price comparison behavior...")
    
    # Check if any price comparison API would include these products together
    try:
        # Query for price comparisons that might include these products
        # This is a simplified test - actual API behavior may vary
        
        # Check if there are any product_matches records that would group these
        product_matches = supabase_service.client.table('product_matches').select('*').execute()
        
        if product_matches.data:
            problematic_matches = []
            for match in product_matches.data:
                # Check if this match includes both products
                product_ids = match.get('matched_product_ids', [])
                if isinstance(product_ids, str):
                    try:
                        product_ids = json.loads(product_ids)
                    except:
                        product_ids = []
                
                if twd_product_id in product_ids and hp_product_id in product_ids:
                    problematic_matches.append(match)
            
            if problematic_matches:
                print(f"❌ Found {len(problematic_matches)} product_matches records still linking these products")
                for match in problematic_matches:
                    print(f"  - Match ID: {match.get('id', 'N/A')}")
                    print(f"    Confidence: {match.get('match_confidence', 'N/A')}")
            else:
                print("✅ No product_matches records found linking these products")
        else:
            print("ℹ️  No product_matches records found in database")
    
    except Exception as e:
        print(f"Error checking product_matches: {str(e)}")
    
    # 5. Summary and recommendations
    print("\n=== SUMMARY ===")
    
    both_disabled = twd_disabled and hp_disabled
    if both_disabled:
        print("✅ Both products are marked as match disabled")
    else:
        print("⚠️  One or both products are not marked as disabled")
    
    if not common_match_ids:
        print("✅ Products are no longer in common match groups")
    else:
        print("⚠️  Products are still in common match groups")
    
    print("\n=== RECOMMENDATIONS ===")
    
    if both_disabled:
        print("1. ✅ Products are properly flagged to prevent future matching")
    else:
        print("1. ❌ Ensure both products are marked as match disabled")
    
    print("2. 🔧 Update price comparison APIs to exclude disabled products:")
    print("   - Check specifications.match_disabled before including products in comparisons")
    print("   - Filter out products with match_disabled=true from price comparison results")
    
    print("3. 🔧 Update matching algorithms to respect disabled flags:")
    print("   - Check specifications.match_disabled before matching products")
    print("   - Skip products that have been manually disabled from matching")
    
    print("4. 📊 Consider implementing a review process:")
    print("   - Periodically review disabled matches")
    print("   - Implement approval workflow for re-enabling matches")
    
    print("\n✅ False positive fix verification completed")

if __name__ == "__main__":
    main()