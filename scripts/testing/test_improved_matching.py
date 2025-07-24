#!/usr/bin/env python3
"""
Test the improved product matching algorithm
"""

import sys
import os
sys.path.append('/Users/chongraktanaka/Documents/Project/ris data scrap')

from src.utils.product_matcher_improved import ImprovedProductMatcher

def test_improved_matching():
    """Test the improved matching algorithm with problematic products"""
    
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
        'price': 70000
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
    
    # Test with improved matcher
    matcher = ImprovedProductMatcher()
    result = matcher.match_products(homepro_product, twd_product, 'air-conditioner')
    
    print("=== IMPROVED PRODUCT MATCHING TEST ===")
    print(f"HomePro: {homepro_product['name']}")
    print(f"Model: {homepro_product['sku']}, BTU: {homepro_product['specs']['power']:,}")
    print()
    print(f"TWD: {twd_product['name']}")  
    print(f"Model: {twd_product['sku']}, BTU: {twd_product['specs']['power']:,}")
    print()
    
    print("=== IMPROVED MATCHING RESULTS ===")
    print(f"Overall Confidence: {result.confidence:.3f}")
    print(f"Match Type: {result.match_type}")
    print(f"Matched Fields: {result.matched_fields}")
    print()
    
    print("=== DETAILED SCORES ===")
    for key, value in result.details.items():
        if isinstance(value, dict) and key != 'spec_validation':
            print(f"{key}:")
            for sub_key, sub_value in value.items():
                print(f"  {sub_key}: {sub_value}")
        else:
            print(f"{key}: {value}")
    print()
    
    print("=== WARNINGS ===")
    for warning in result.warnings:
        print(f"- {warning}")
    print()
    
    print("=== REJECTION REASONS ===")
    for reason in result.rejection_reasons:
        print(f"- {reason}")
    print()
    
    # Should these be matched?
    print("=== ANALYSIS ===")
    print("These products should NOT be matched because:")
    print("1. Different models: FCFC30EV2S-WH vs FTM18PV2S")
    print("2. Different BTU capacity: 30,000 vs 18,090 (66% difference)")
    print("3. Different types: Cassette/Ceiling vs Wall-Mounted")
    print("4. Large price difference: ฿70,000 vs ฿24,535 (65% difference)")
    print()
    
    if result.confidence > 0.5:
        print("❌ PROBLEM: Improved algorithm still suggests these might match!")
        print("   Further improvements needed.")
    else:
        print("✅ EXCELLENT: Improved algorithm correctly rejects this match!")
        if result.rejection_reasons:
            print("   Rejection was based on:")
            for reason in result.rejection_reasons:
                print(f"   - {reason}")

def test_valid_match():
    """Test with products that should match"""
    
    print("\n" + "="*60)
    print("=== TESTING VALID MATCH ===")
    
    # Same product from different retailers
    product1 = {
        'name': 'DAIKIN เครื่องปรับอากาศติดผนัง 18,000 BTU รุ่น FTM18PV2S อินเวอร์เตอร์',
        'brand': 'DAIKIN',
        'sku': 'FTM18PV2S',
        'specs': {
            'power': 18000,  # BTU
            'type': 'wall mounted',
            'voltage': '220V'
        },
        'category': 'air-conditioner',
        'price': 24000
    }
    
    product2 = {
        'name': 'แอร์ติดผนัง DAIKIN 18,000 บีทียู รุ่น FTM18PV2S Inverter R32',
        'brand': 'DAIKIN', 
        'sku': 'FTM18PV2S',
        'specs': {
            'power': 18000,  # BTU
            'type': 'wall mounted',
            'refrigerant': 'R32'
        },
        'category': 'air-conditioner',
        'price': 23500
    }
    
    matcher = ImprovedProductMatcher()
    result = matcher.match_products(product1, product2, 'air-conditioner')
    
    print(f"Product 1: {product1['name']}")
    print(f"Product 2: {product2['name']}")
    print()
    print(f"Confidence: {result.confidence:.3f}")
    print(f"Match Type: {result.match_type}")
    print(f"Matched Fields: {result.matched_fields}")
    
    if result.confidence > 0.7:
        print("✅ GOOD: Valid products are correctly matched!")
    else:
        print("❌ PROBLEM: Valid products are not being matched!")
        print("   Rejection reasons:", result.rejection_reasons)

if __name__ == "__main__":
    test_improved_matching()
    test_valid_match()