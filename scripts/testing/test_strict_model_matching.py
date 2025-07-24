#!/usr/bin/env python3
"""
Test the stricter model matching for DAIKIN products
"""

import sys
import os
sys.path.append('/Users/chongraktanaka/Documents/Project/ris data scrap')

from src.utils.product_matcher_improved import ImprovedProductMatcher

def test_strict_model_matching():
    """Test stricter model matching with known problematic cases"""
    
    test_cases = [
        # Case 1: Different models - FTKZ09YV2S vs FTM09PV2S (should NOT match)
        {
            'product1': {
                'name': 'แอร์ผนัง DAIKIN FTKZ09YV2S 9200 บีทียู อินเวอร์เตอร์',
                'brand': 'DAIKIN',
                'sku': 'FTKZ09YV2S',
                'specs': {'power': 9200, 'type': 'wall mounted'},
                'category': 'air-conditioner',
                'price': 20000
            },
            'product2': {
                'name': 'แอร์ติดผนัง 9,200 BTU DAIKIN รุ่น FTM09PV2S',
                'brand': 'DAIKIN',
                'sku': 'FTM09PV2S',
                'specs': {'power': 9200, 'type': 'wall mounted'},
                'category': 'air-conditioner',
                'price': 19000
            },
            'expected': 'NO_MATCH',
            'reason': 'Different model series: FTKZ vs FTM'
        },
        
        # Case 2: Same model, slight name variation (should match)
        {
            'product1': {
                'name': 'DAIKIN Air Conditioner FTM18PV2S 18,000 BTU',
                'brand': 'DAIKIN',
                'sku': 'FTM18PV2S',
                'specs': {'power': 18000, 'type': 'wall mounted'},
                'category': 'air-conditioner',
                'price': 25000
            },
            'product2': {
                'name': 'แอร์ DAIKIN รุ่น FTM18PV2S 18000 บีทียู',
                'brand': 'DAIKIN',
                'sku': 'FTM18PV2S',
                'specs': {'power': 18000, 'type': 'wall mounted'},
                'category': 'air-conditioner',
                'price': 24500
            },
            'expected': 'MATCH',
            'reason': 'Same model: FTM18PV2S'
        },
        
        # Case 3: Different capacity same series (should NOT match)
        {
            'product1': {
                'name': 'DAIKIN FTKZ09YV2S 9,200 BTU',
                'brand': 'DAIKIN',
                'sku': 'FTKZ09YV2S',
                'specs': {'power': 9200, 'type': 'wall mounted'},
                'category': 'air-conditioner',
                'price': 18000
            },
            'product2': {
                'name': 'DAIKIN FTKZ15YV2S 15,000 BTU',
                'brand': 'DAIKIN',
                'sku': 'FTKZ15YV2S',
                'specs': {'power': 15000, 'type': 'wall mounted'},
                'category': 'air-conditioner',
                'price': 25000
            },
            'expected': 'NO_MATCH',
            'reason': 'Different capacity in model: 09 vs 15'
        },
        
        # Case 4: Similar model codes but different (should NOT match)
        {
            'product1': {
                'name': 'DAIKIN FTKS25TV2S 9,000 BTU',
                'brand': 'DAIKIN',
                'sku': 'FTKS25TV2S',
                'specs': {'power': 9000, 'type': 'wall mounted'},
                'category': 'air-conditioner',
                'price': 22000
            },
            'product2': {
                'name': 'DAIKIN FTKZ25TV2S 9,000 BTU',
                'brand': 'DAIKIN',
                'sku': 'FTKZ25TV2S',
                'specs': {'power': 9000, 'type': 'wall mounted'},
                'category': 'air-conditioner',
                'price': 23000
            },
            'expected': 'NO_MATCH',
            'reason': 'Different series: FTKS vs FTKZ'
        }
    ]
    
    matcher = ImprovedProductMatcher()
    
    print("=== STRICT MODEL MATCHING TESTS ===\n")
    
    passed = 0
    failed = 0
    
    for i, test_case in enumerate(test_cases, 1):
        product1 = test_case['product1']
        product2 = test_case['product2']
        expected = test_case['expected']
        reason = test_case['reason']
        
        result = matcher.match_products(product1, product2, 'air-conditioner')
        
        print(f"Test Case {i}: {reason}")
        print(f"  Product 1: {product1['sku']} - {product1['name'][:40]}...")
        print(f"  Product 2: {product2['sku']} - {product2['name'][:40]}...")
        print(f"  Expected: {expected}")
        print(f"  Result: Confidence={result.confidence:.3f}, Type={result.match_type}")
        
        # Check if result matches expectation
        if expected == 'MATCH' and result.confidence > 0.7:
            print(f"  ✅ PASS: Products correctly matched")
            passed += 1
        elif expected == 'NO_MATCH' and result.confidence < 0.5:
            print(f"  ✅ PASS: Products correctly not matched")
            if result.rejection_reasons:
                print(f"     Rejection: {result.rejection_reasons[0]}")
            passed += 1
        else:
            print(f"  ❌ FAIL: Unexpected result")
            failed += 1
            
        print(f"  Details: SKU score={result.details.get('sku_score', 0):.3f}")
        print()
    
    print(f"\n=== TEST SUMMARY ===")
    print(f"Total Tests: {len(test_cases)}")
    print(f"Passed: {passed}")
    print(f"Failed: {failed}")
    
    if failed == 0:
        print("\n✅ All tests passed! Model matching is working correctly.")
    else:
        print(f"\n❌ {failed} tests failed. Further adjustments needed.")

if __name__ == "__main__":
    test_strict_model_matching()