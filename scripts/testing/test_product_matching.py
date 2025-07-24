#!/usr/bin/env python3
"""
Test the product matching algorithm with the specific problematic products
"""

import sys
import os
sys.path.append('/Users/chongraktanaka/Documents/Project/ris data scrap')

from src.utils.product_matcher_enhanced import EnhancedProductMatcher

def test_problematic_match():
    """Test the specific products that are incorrectly matched"""
    
    # HomePro Product: FCFC30EV2S-WH, 30,000 BTU, Cassette/Ceiling Mounted
    homepro_product = {
        'name': 'DAIKIN เครื่องปรับอากาศแบบฝังฝ้าเพดาน 30,000 BTU รุ่น FCFC30EV2S-WH',
        'brand': 'DAIKIN',
        'sku': 'FCFC30EV2S-WH',
        'specs': {
            'power': 30000,  # BTU
            'type': 'cassette ceiling mounted',
            'voltage': '220V'
        },
        'category': 'air-conditioner',
        'price': 45000  # Example price
    }
    
    # Thai Watsadu Product: FTM18PV2S, 18,090 BTU, Wall-Mounted  
    twd_product = {
        'name': 'แอร์ติดผนัง 18,090 BTU DAIKIN รุ่น FTM18PV2S',
        'brand': 'DAIKIN', 
        'sku': 'FTM18PV2S',
        'specs': {
            'power': 18090,  # BTU
            'type': 'wall mounted',
            'refrigerant': 'R32'
        },
        'category': 'air-conditioner',
        'price': 24535
    }
    
    # Test the matching
    matcher = EnhancedProductMatcher()
    result = matcher.match_products(homepro_product, twd_product)
    
    print("=== PRODUCT MATCHING TEST ===")
    print(f"HomePro: {homepro_product['name']}")
    print(f"Model: {homepro_product['sku']}, BTU: {homepro_product['specs']['power']}")
    print()
    print(f"TWD: {twd_product['name']}")  
    print(f"Model: {twd_product['sku']}, BTU: {twd_product['specs']['power']}")
    print()
    
    print("=== MATCHING RESULTS ===")
    print(f"Overall Confidence: {result.confidence:.2f}")
    print(f"Match Type: {result.match_type}")
    print(f"Matched Fields: {result.matched_fields}")
    print()
    
    print("=== DETAILED SCORES ===")
    for key, value in result.details.items():
        if isinstance(value, dict):
            print(f"{key}: {value}")
        else:
            print(f"{key}: {value:.3f}")
    print()
    
    print("=== WARNINGS ===")
    for warning in result.warnings:
        print(f"- {warning}")
    print()
    
    # Should these be matched?
    print("=== ANALYSIS ===")
    print("These products should NOT be matched because:")
    print("1. Different models: FCFC30EV2S-WH vs FTM18PV2S")
    print("2. Different BTU capacity: 30,000 vs 18,090 (66% difference)")
    print("3. Different types: Cassette/Ceiling vs Wall-Mounted")
    print()
    
    if result.confidence > 0.5:
        print("❌ PROBLEM: Algorithm incorrectly suggests these might match!")
        print("   This is a false positive that needs to be fixed.")
    else:
        print("✅ GOOD: Algorithm correctly identifies these as different products.")

if __name__ == "__main__":
    test_problematic_match()