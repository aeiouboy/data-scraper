#!/usr/bin/env python3
"""
Analyze the false match issue where CARRIER products with different BTU ratings were incorrectly matched
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '../..'))

from src.services.supabase_service import SupabaseService
from src.utils.product_matcher import ProductMatcher
from src.utils.product_matcher_enhanced import EnhancedProductMatcher
from src.utils.product_matcher_ultra_strict import UltraStrictProductMatcher
import json

def analyze_false_match():
    """Analyze the false match identified in the schema debug"""
    
    # Initialize services
    supabase_service = SupabaseService()
    
    # Match group ID with the problematic CARRIER matches
    match_group_id = "28049e86-a525-48ba-8720-abb462fc1042"
    
    print("=== ANALYZING FALSE MATCH FOR CARRIER PRODUCTS ===\n")
    
    try:
        # Get the match group details
        match_query = supabase_service.client.table('match_groups').select('*').eq('id', match_group_id).execute()
        match_group = match_query.data[0]
        
        print(f"Match Group ID: {match_group_id}")
        print(f"Canonical Name: {match_group.get('canonical_name', 'N/A')}")
        print(f"Brand: {match_group.get('canonical_brand', 'N/A')}")
        print(f"Product Type: {match_group.get('product_type', 'N/A')}")
        print(f"Created: {match_group.get('created_at', 'N/A')}")
        
        # Get confidence scores
        confidence_query = supabase_service.client.table('match_confidence').select('*').eq('match_group_id', match_group_id).execute()
        
        if confidence_query.data:
            confidence = confidence_query.data[0]
            print(f"\n=== CONFIDENCE SCORES ===")
            print(f"Overall Score: {confidence.get('overall_score', 'N/A')}")
            print(f"Name Match Score: {confidence.get('name_match_score', 'N/A')}")
            print(f"Brand Match Score: {confidence.get('brand_match_score', 'N/A')}")
            print(f"Spec Match Score: {confidence.get('spec_match_score', 'N/A')}")
            print(f"Price Consistency Score: {confidence.get('price_consistency_score', 'N/A')}")
            print(f"Confidence Level: {confidence.get('confidence_level', 'N/A')}")
        
        # Get all products in this match group
        mapping_query = supabase_service.client.table('product_match_mapping').select('*').eq('match_group_id', match_group_id).execute()
        
        print(f"\n=== PRODUCTS IN MATCH GROUP ({len(mapping_query.data)} products) ===")
        
        products = []
        for mapping in mapping_query.data:
            product_query = supabase_service.client.table('products').select('*').eq('id', mapping['product_id']).execute()
            if product_query.data:
                product = product_query.data[0]
                products.append(product)
                
                print(f"\nProduct: {product.get('name', 'N/A')}")
                print(f"  ID: {product.get('id', 'N/A')}")
                print(f"  Retailer: {product.get('retailer_code', 'N/A')}")
                print(f"  Brand: {product.get('brand', 'N/A')}")
                print(f"  Price: ฿{product.get('price', 'N/A')}")
                
                # Extract BTU from name
                import re
                name = product.get('name', '')
                btu_match = re.search(r'(\d{1,3}[,.]?\d{3})\s*BTU', name, re.IGNORECASE)
                if btu_match:
                    btu = btu_match.group(1).replace(',', '').replace('.', '')
                    print(f"  BTU: {btu}")
                else:
                    print(f"  BTU: Not found in name")
                
                # Extract model number
                model_patterns = [
                    r'([A-Z0-9]+[A-Z][A-Z0-9]+)',
                    r'([0-9]+[A-Z]+[0-9]+[A-Z]*[0-9]*)',
                    r'(\d{2}[A-Z]{2,4}\d{3}[A-Z]*\d*[A-Z]*)'
                ]
                
                model_found = None
                for pattern in model_patterns:
                    match = re.search(pattern, name.upper())
                    if match:
                        model_found = match.group(1)
                        break
                
                print(f"  Model: {model_found or 'Not found'}")
        
        print(f"\n=== ANALYSIS OF FALSE MATCH ===")
        
        # BTU Analysis
        btus = []
        for product in products:
            name = product.get('name', '')
            btu_match = re.search(r'(\d{1,3}[,.]?\d{3})\s*BTU', name, re.IGNORECASE)
            if btu_match:
                btu = int(btu_match.group(1).replace(',', '').replace('.', ''))
                btus.append(btu)
        
        if btus:
            min_btu = min(btus)
            max_btu = max(btus)
            btu_range = max_btu - min_btu
            btu_variance = (btu_range / min_btu) * 100 if min_btu > 0 else 0
            
            print(f"BTU Range: {min_btu} - {max_btu}")
            print(f"BTU Variance: {btu_variance:.1f}%")
            
            if btu_variance > 10:
                print("❌ CRITICAL ISSUE: BTU variance > 10% - These products should NOT match!")
                print("   Air conditioners with different BTU ratings are completely different products.")
            else:
                print("✅ BTU variance within acceptable range")
        
        # Model Analysis
        models = []
        for product in products:
            name = product.get('name', '')
            model_patterns = [
                r'([A-Z0-9]+[A-Z][A-Z0-9]+)',
                r'([0-9]+[A-Z]+[0-9]+[A-Z]*[0-9]*)',
                r'(\d{2}[A-Z]{2,4}\d{3}[A-Z]*\d*[A-Z]*)'
            ]
            
            for pattern in model_patterns:
                match = re.search(pattern, name.upper())
                if match:
                    models.append(match.group(1))
                    break
        
        unique_models = set(models)
        print(f"\nUnique Models Found: {len(unique_models)}")
        for model in unique_models:
            print(f"  - {model}")
        
        if len(unique_models) > 1:
            print("❌ CRITICAL ISSUE: Multiple different models in same match group!")
            print("   Different model numbers indicate different products.")
        else:
            print("✅ All products have the same model number")
        
        # Test with different matchers to understand how this match occurred
        print(f"\n=== TESTING WITH DIFFERENT MATCHERS ===")
        
        if len(products) >= 2:
            # Test the first two products that are most problematic
            twd_product = None
            hp_product = None
            
            for product in products:
                if product.get('retailer_code') == 'TWD' and '25,200' in product.get('name', ''):
                    twd_product = product
                elif product.get('retailer_code') == 'HP' and '12200' in product.get('name', ''):
                    hp_product = product
            
            if twd_product and hp_product:
                print(f"\nTesting match between:")
                print(f"  TWD: {twd_product.get('name', 'N/A')}")
                print(f"  HP: {hp_product.get('name', 'N/A')}")
                
                # Prepare product data for matcher
                p1_data = {
                    'name': twd_product.get('name', ''),
                    'brand': twd_product.get('brand', ''),
                    'sku': twd_product.get('sku', ''),
                    'specs': twd_product.get('specifications', {}),
                    'category': twd_product.get('category', ''),
                    'price': twd_product.get('price', 0)
                }
                
                p2_data = {
                    'name': hp_product.get('name', ''),
                    'brand': hp_product.get('brand', ''),
                    'sku': hp_product.get('sku', ''),
                    'specs': hp_product.get('specifications', {}),
                    'category': hp_product.get('category', ''),
                    'price': hp_product.get('price', 0)
                }
                
                # Convert string specs to dict if needed
                for p_data in [p1_data, p2_data]:
                    if isinstance(p_data['specs'], str):
                        try:
                            p_data['specs'] = json.loads(p_data['specs'])
                        except:
                            p_data['specs'] = {}
                
                # Test with Ultra Strict Matcher (should reject)
                print(f"\n--- Ultra Strict Matcher ---")
                try:
                    matcher = UltraStrictProductMatcher()
                    result = matcher.match_products(p1_data, p2_data, 'air_conditioner')
                    
                    print(f"  Confidence: {result.confidence:.3f}")
                    print(f"  Match Type: {result.match_type}")
                    print(f"  Matched: {'YES' if result.confidence > 0.8 else 'NO'}")
                    print(f"  Warnings: {result.warnings}")
                    print(f"  Rejection Reasons: {result.rejection_reasons}")
                    
                    if result.confidence > 0.8:
                        print("  ❌ ULTRA STRICT MATCHER FAILED - Should have rejected this match!")
                    else:
                        print("  ✅ Ultra Strict Matcher correctly rejected this match")
                        
                except Exception as e:
                    print(f"  Error: {str(e)}")
                
                # Test with Enhanced Matcher
                print(f"\n--- Enhanced Matcher ---")
                try:
                    matcher = EnhancedProductMatcher()
                    result = matcher.match_products(p1_data, p2_data, 'air_conditioner')
                    
                    print(f"  Confidence: {result.confidence:.3f}")
                    print(f"  Match Type: {result.match_type}")
                    print(f"  Matched: {'YES' if result.confidence > 0.8 else 'NO'}")
                    print(f"  Warnings: {result.warnings}")
                    print(f"  Rejection Reasons: {result.rejection_reasons}")
                    
                    if result.confidence > 0.8:
                        print("  ❌ ENHANCED MATCHER FAILED - Should have rejected this match!")
                    else:
                        print("  ✅ Enhanced Matcher correctly rejected this match")
                        
                except Exception as e:
                    print(f"  Error: {str(e)}")
                
                # Test with Basic Matcher
                print(f"\n--- Basic Matcher ---")
                try:
                    matcher = ProductMatcher()
                    result = matcher.match_products(p1_data, p2_data, 'air_conditioner')
                    
                    print(f"  Confidence: {result.confidence:.3f}")
                    print(f"  Match Type: {result.match_type}")
                    print(f"  Matched: {'YES' if result.confidence > 0.8 else 'NO'}")
                    print(f"  Warnings: {result.warnings}")
                    print(f"  Rejection Reasons: {result.rejection_reasons}")
                    
                    if result.confidence > 0.8:
                        print("  ❌ BASIC MATCHER FAILED - Should have rejected this match!")
                        print("  This suggests the basic matcher is too permissive for air conditioners")
                    else:
                        print("  ✅ Basic Matcher correctly rejected this match")
                        
                except Exception as e:
                    print(f"  Error: {str(e)}")
        
        print(f"\n=== RECOMMENDATIONS ===")
        print("1. BTU Validation: Add strict BTU validation for air conditioners")
        print("   - Air conditioners with >5% BTU difference should never match")
        print("   - BTU is a critical specification that defines the product's capacity")
        
        print("\n2. Model Number Validation: Improve model number extraction and comparison")
        print("   - Different model numbers should prevent matching")
        print("   - Use more sophisticated model number parsing")
        
        print("\n3. Category-Specific Rules: Implement category-specific matching rules")
        print("   - Air conditioners require strict BTU and model matching")
        print("   - Other categories may have different critical specifications")
        
        print("\n4. Review Existing Matches: Audit all existing matches for similar issues")
        print("   - Check for other products with significant BTU differences")
        print("   - Implement automated validation for existing matches")
        
        print("\n5. Matching Algorithm Improvements:")
        print("   - Increase weight of BTU specifications in scoring")
        print("   - Add hard rejection rules for critical specification mismatches")
        print("   - Implement specification tolerance ranges per category")
        
    except Exception as e:
        print(f"Error: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    analyze_false_match()