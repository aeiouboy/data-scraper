#!/usr/bin/env python3
"""
Debug script to investigate the specific match ID: c6417b23-647b-4532-afd1-54cde654a1f5
For CARRIER products with different BTU ratings that were incorrectly matched.
"""

import sys
import os
sys.path.append('/Users/chongraktanaka/Documents/Project/ris data scrap')

from src.services.supabase_service import SupabaseService
from src.utils.product_matcher import ProductMatcher
from src.utils.product_matcher_enhanced import EnhancedProductMatcher
from src.utils.product_matcher_ultra_strict import UltraStrictProductMatcher
import json

def debug_specific_match():
    """Debug the specific match ID for CARRIER products"""
    
    match_id = "c6417b23-647b-4532-afd1-54cde654a1f5"
    
    # Initialize services
    supabase_service = SupabaseService()
    
    print(f"=== DEBUGGING MATCH ID: {match_id} ===\n")
    
    try:
        # Query the match_groups table for this specific match
        match_query = supabase_service.client.table('match_groups').select('*').eq('id', match_id).execute()
        
        if not match_query.data:
            print(f"No match found with ID: {match_id}")
            
            # Try to find similar matches by searching for CARRIER products
            print("\nSearching for CARRIER matches...")
            carrier_matches = supabase_service.client.table('match_groups').select('*').ilike('products', '%CARRIER%').limit(10).execute()
            
            if carrier_matches.data:
                print(f"Found {len(carrier_matches.data)} CARRIER matches:")
                for match in carrier_matches.data:
                    print(f"  ID: {match['id']}")
                    print(f"  Products: {match.get('products', 'N/A')}")
                    print(f"  Confidence: {match.get('confidence_score', 'N/A')}")
                    print(f"  Created: {match.get('created_at', 'N/A')}")
                    print("  ---")
            return
        
        match_data = match_query.data[0]
        print("Match Found:")
        print(f"  ID: {match_data['id']}")
        print(f"  Confidence Score: {match_data.get('confidence_score', 'N/A')}")
        print(f"  Match Type: {match_data.get('match_type', 'N/A')}")
        print(f"  Created: {match_data.get('created_at', 'N/A')}")
        print(f"  Updated: {match_data.get('updated_at', 'N/A')}")
        
        # Get the products in this match
        products_data = match_data.get('products', [])
        if isinstance(products_data, str):
            try:
                products_data = json.loads(products_data)
            except:
                pass
        
        print(f"\nProducts in Match ({len(products_data)} products):")
        
        product_details = []
        for i, product_id in enumerate(products_data):
            # Get product details
            product_query = supabase_service.client.table('products').select('*').eq('id', product_id).execute()
            
            if product_query.data:
                product = product_query.data[0]
                product_details.append(product)
                
                print(f"\n  Product {i+1}:")
                print(f"    ID: {product['id']}")
                print(f"    Name: {product.get('name', 'N/A')}")
                print(f"    Brand: {product.get('brand', 'N/A')}")
                print(f"    SKU: {product.get('sku', 'N/A')}")
                print(f"    Price: ฿{product.get('price', 'N/A')}")
                print(f"    Retailer: {product.get('retailer_code', 'N/A')}")
                print(f"    Category: {product.get('category', 'N/A')}")
                
                # Extract BTU from specifications
                specs = product.get('specifications', {})
                if isinstance(specs, str):
                    try:
                        specs = json.loads(specs)
                    except:
                        specs = {}
                
                btu = specs.get('btu') or specs.get('BTU') or 'N/A'
                print(f"    BTU: {btu}")
                
                # Try to extract BTU from name if not in specs
                if btu == 'N/A':
                    name = product.get('name', '')
                    import re
                    btu_match = re.search(r'(\d{1,3}[,.]?\d{3})\s*BTU', name, re.IGNORECASE)
                    if btu_match:
                        btu_from_name = btu_match.group(1).replace(',', '').replace('.', '')
                        print(f"    BTU (from name): {btu_from_name}")
                
                print(f"    Specs: {specs}")
            else:
                print(f"\n  Product {i+1}: NOT FOUND (ID: {product_id})")
        
        # Analyze the matching if we have exactly 2 products
        if len(product_details) == 2:
            print("\n=== MATCHING ANALYSIS ===")
            
            product1, product2 = product_details
            
            # Test with different matchers
            matchers = [
                ("Basic Matcher", ProductMatcher()),
                ("Enhanced Matcher", EnhancedProductMatcher()),
                ("Ultra Strict Matcher", UltraStrictProductMatcher())
            ]
            
            for matcher_name, matcher in matchers:
                print(f"\n--- {matcher_name} ---")
                
                # Prepare product data for matcher
                p1_data = {
                    'name': product1.get('name', ''),
                    'brand': product1.get('brand', ''),
                    'sku': product1.get('sku', ''),
                    'specs': product1.get('specifications', {}),
                    'category': product1.get('category', ''),
                    'price': product1.get('price', 0)
                }
                
                p2_data = {
                    'name': product2.get('name', ''),
                    'brand': product2.get('brand', ''),
                    'sku': product2.get('sku', ''),
                    'specs': product2.get('specifications', {}),
                    'category': product2.get('category', ''),
                    'price': product2.get('price', 0)
                }
                
                # Convert string specs to dict if needed
                for p_data in [p1_data, p2_data]:
                    if isinstance(p_data['specs'], str):
                        try:
                            p_data['specs'] = json.loads(p_data['specs'])
                        except:
                            p_data['specs'] = {}
                
                try:
                    result = matcher.match_products(p1_data, p2_data, 'air_conditioner')
                    
                    print(f"  Confidence: {result.confidence:.3f}")
                    print(f"  Match Type: {result.match_type}")
                    print(f"  Matched Fields: {result.matched_fields}")
                    print(f"  Warnings: {result.warnings}")
                    print(f"  Rejection Reasons: {result.rejection_reasons}")
                    
                    if hasattr(result, 'details') and result.details:
                        print(f"  Details: {result.details}")
                        
                except Exception as e:
                    print(f"  Error: {str(e)}")
            
            # Manual BTU analysis
            print("\n=== BTU ANALYSIS ===")
            
            # Extract BTU from both products
            def extract_btu(product):
                # Check specifications
                specs = product.get('specifications', {})
                if isinstance(specs, str):
                    try:
                        specs = json.loads(specs)
                    except:
                        specs = {}
                
                btu = specs.get('btu') or specs.get('BTU')
                if btu:
                    return btu
                
                # Check name
                name = product.get('name', '')
                import re
                btu_match = re.search(r'(\d{1,3}[,.]?\d{3})\s*BTU', name, re.IGNORECASE)
                if btu_match:
                    return int(btu_match.group(1).replace(',', '').replace('.', ''))
                
                return None
            
            btu1 = extract_btu(product1)
            btu2 = extract_btu(product2)
            
            print(f"Product 1 BTU: {btu1}")
            print(f"Product 2 BTU: {btu2}")
            
            if btu1 and btu2:
                btu_diff = abs(btu1 - btu2)
                btu_diff_percent = (btu_diff / max(btu1, btu2)) * 100
                print(f"BTU Difference: {btu_diff} ({btu_diff_percent:.1f}%)")
                
                if btu_diff_percent > 5:
                    print("❌ PROBLEM: BTU difference > 5% - This should NOT match!")
                else:
                    print("✅ BTU difference within tolerance")
            
            # Model number analysis
            print("\n=== MODEL NUMBER ANALYSIS ===")
            
            def extract_model(name):
                # Look for model patterns
                import re
                patterns = [
                    r'([A-Z0-9]+[A-Z][A-Z0-9]+)',  # General alphanumeric model
                    r'([0-9]+[A-Z]+[0-9]+[A-Z]*[0-9]*)',  # Number-letter-number pattern
                ]
                
                for pattern in patterns:
                    match = re.search(pattern, name.upper())
                    if match:
                        return match.group(1)
                return None
            
            model1 = extract_model(product1.get('name', ''))
            model2 = extract_model(product2.get('name', ''))
            
            print(f"Product 1 Model: {model1}")
            print(f"Product 2 Model: {model2}")
            
            if model1 and model2:
                if model1 == model2:
                    print("✅ Exact model match")
                else:
                    print("❌ Different models - This should NOT match!")
                    
                    # Check similarity
                    from difflib import SequenceMatcher
                    similarity = SequenceMatcher(None, model1, model2).ratio()
                    print(f"Model similarity: {similarity:.3f}")
        
        # Check matching metadata
        print("\n=== MATCH METADATA ===")
        metadata = match_data.get('metadata', {})
        if isinstance(metadata, str):
            try:
                metadata = json.loads(metadata)
            except:
                metadata = {}
        
        print(f"Metadata: {metadata}")
        
        # Check if there are any matching algorithm details
        matching_details = match_data.get('matching_details', {})
        if isinstance(matching_details, str):
            try:
                matching_details = json.loads(matching_details)
            except:
                matching_details = {}
        
        print(f"Matching Details: {matching_details}")
        
    except Exception as e:
        print(f"Error: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_specific_match()