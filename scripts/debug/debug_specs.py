#!/usr/bin/env python3
"""
Debug script to understand specification extraction issues
"""

import sys
import os
sys.path.append('/Users/chongraktanaka/Documents/Project/ris data scrap')

from src.utils.product_matcher_ultra_strict import UltraStrictProductMatcher

def debug_spec_extraction():
    """Debug the specification extraction for DAIKIN products"""
    
    # Create the matcher
    matcher = UltraStrictProductMatcher()
    
    # Test products
    homepro_product = {
        'name': 'แอร์ผนัง DAIKIN FTM13PV2S 13000 บีทียู',
        'brand': 'DAIKIN',
        'sku': '',
        'specs': {'btu': 13000},
        'category': 'air_conditioner',
        'price': 18990
    }
    
    twd_product = {
        'name': 'แอร์ติดผนัง 13,000 BTU DAIKIN รุ่น FTM13PV2S',
        'brand': 'DAIKIN', 
        'sku': '',
        'specs': {'btu': 13000},
        'category': 'air_conditioner',
        'price': 14800
    }
    
    print("=== SPECIFICATION EXTRACTION DEBUG ===\n")
    
    # Test _get_all_specs for both products
    print("HomePro Product Specs:")
    homepro_specs = matcher._get_all_specs(homepro_product)
    for key, value in homepro_specs.items():
        print(f"  {key}: {value} ({type(value).__name__})")
    
    print("\nThai Watsadu Product Specs:")
    twd_specs = matcher._get_all_specs(twd_product)
    for key, value in twd_specs.items():
        print(f"  {key}: {value} ({type(value).__name__})")
    
    # Test normalizer directly
    print("\n=== NORMALIZER EXTRACTION ===")
    print("HomePro name specs:")
    homepro_name_specs = matcher.normalizer.extract_specifications(homepro_product['name'])
    for key, value in homepro_name_specs.items():
        print(f"  {key}: {value} ({type(value).__name__})")
        
    print("\nTWD name specs:")
    twd_name_specs = matcher.normalizer.extract_specifications(twd_product['name'])
    for key, value in twd_name_specs.items():
        print(f"  {key}: {value} ({type(value).__name__})")
    
    # Check critical specs for air-conditioner
    print(f"\n=== CRITICAL SPECS FOR AIR-CONDITIONER ===")
    critical_fields = matcher.critical_specs.get('air-conditioner', [])
    print(f"Critical fields: {critical_fields}")
    
    print("\nValidation check per field:")
    for field in critical_fields:
        val1 = homepro_specs.get(field)
        val2 = twd_specs.get(field)
        print(f"  {field}: {val1} vs {val2}")
        
        if field == 'model':
            model1 = val1 or matcher._extract_model_number_enhanced(homepro_product.get('name', ''))
            model2 = val2 or matcher._extract_model_number_enhanced(twd_product.get('name', ''))
            print(f"    Model resolution: '{model1}' vs '{model2}'")
            if model1 and model2:
                similarity = matcher._calculate_model_similarity(model1, model2)
                print(f"    Similarity: {similarity:.3f} ({'PASS' if similarity >= 0.8 else 'FAIL'})")
        elif val1 is not None and val2 is not None:
            if isinstance(val1, (int, float)) and isinstance(val2, (int, float)):
                tolerances = matcher.spec_tolerances.get('air-conditioner', matcher.spec_tolerances['default'])
                tolerance = tolerances.get(field, 0.05)
                diff = abs(val1 - val2)
                max_val = max(val1, val2)
                if max_val > 0:
                    diff_pct = diff / max_val
                    print(f"    Tolerance check: {diff_pct:.3f} <= {tolerance} ({'PASS' if diff_pct <= tolerance else 'FAIL'})")
                    if diff_pct > tolerance:
                        print(f"    FAILURE REASON: {field} mismatch: {val1} vs {val2} (>{tolerance*100:.0f}% tolerance)")

if __name__ == "__main__":
    debug_spec_extraction()