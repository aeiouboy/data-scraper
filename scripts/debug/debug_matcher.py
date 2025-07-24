#!/usr/bin/env python3
"""
Debug script to test ultra-strict matcher with the specific DAIKIN products
that should match but are being rejected.
"""

import sys
import os
sys.path.append('/Users/chongraktanaka/Documents/Project/ris data scrap')

from src.utils.product_matcher_ultra_strict import UltraStrictProductMatcher

def debug_daikin_match():
    """Debug the DAIKIN FTM13PV2S matching issue"""
    
    # Create the matcher
    matcher = UltraStrictProductMatcher()
    
    # Test products based on the URLs provided
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
    
    print("=== DEBUGGING DAIKIN FTM13PV2S MATCHING ===\n")
    
    print("HomePro Product:")
    print(f"  Name: {homepro_product['name']}")
    print(f"  Brand: {homepro_product['brand']}")
    print(f"  Price: ฿{homepro_product['price']:,}")
    
    print("\nThai Watsadu Product:")
    print(f"  Name: {twd_product['name']}")
    print(f"  Brand: {twd_product['brand']}")
    print(f"  Price: ฿{twd_product['price']:,}")
    
    # Test model extraction
    print("\n=== MODEL EXTRACTION TEST ===")
    model1 = matcher._extract_model_number_enhanced(homepro_product['name'])
    model2 = matcher._extract_model_number_enhanced(twd_product['name'])
    print(f"HomePro extracted model: '{model1}'")
    print(f"TWD extracted model: '{model2}'")
    
    # Test model similarity
    if model1 and model2:
        similarity = matcher._calculate_model_similarity(model1, model2)
        print(f"Model similarity: {similarity:.3f}")
        
        # Test model decomposition
        parts1 = matcher._decompose_model(model1)
        parts2 = matcher._decompose_model(model2)
        print(f"Model 1 parts: {parts1}")
        print(f"Model 2 parts: {parts2}")
    
    # Test BTU extraction
    print("\n=== BTU EXTRACTION TEST ===")
    btu1 = matcher._extract_btu_enhanced(homepro_product['name'])
    btu2 = matcher._extract_btu_enhanced(twd_product['name'])
    print(f"HomePro BTU: {btu1}")
    print(f"TWD BTU: {btu2}")
    
    if btu1 and btu2:
        btu_diff = abs(btu1 - btu2) / max(btu1, btu2)
        print(f"BTU difference: {btu_diff*100:.1f}%")
        print(f"BTU tolerance (5%): {'PASS' if btu_diff <= 0.05 else 'FAIL'}")
    
    # Test early rejection
    print("\n=== EARLY REJECTION TEST ===")
    early_rejections = matcher._check_early_rejection_strict(
        homepro_product, twd_product, 'air-conditioner'
    )
    print(f"Early rejections: {early_rejections}")
    
    # Test full matching
    print("\n=== FULL MATCHING TEST ===")
    result = matcher.match_products(
        homepro_product, twd_product, 'air_conditioner'
    )
    
    print(f"Final confidence: {result.confidence:.3f}")
    print(f"Match type: {result.match_type}")
    print(f"Matched fields: {result.matched_fields}")
    print(f"Warnings: {result.warnings}")
    print(f"Rejection reasons: {result.rejection_reasons}")
    print(f"Details: {result.details}")
    
    # Test individual component scores
    if 'sku_score' in result.details:
        print(f"\nComponent Scores:")
        print(f"  SKU Score: {result.details.get('sku_score', 'N/A'):.3f}")
        print(f"  Brand Score: {result.details.get('brand_score', 'N/A'):.3f}")
        print(f"  Name Score: {result.details.get('name_score', 'N/A'):.3f}")
        print(f"  Spec Score: {result.details.get('spec_score', 'N/A'):.3f}")
        print(f"  Category Score: {result.details.get('category_score', 'N/A'):.3f}")

if __name__ == "__main__":
    debug_daikin_match()