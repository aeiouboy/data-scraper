#!/usr/bin/env python3
"""
Quick integration demo of all Phase 2 components working together
"""

import sys
import os
import time

# Add src to Python path
project_root = os.path.dirname(__file__)
sys.path.insert(0, os.path.join(project_root, 'src'))

def demo_complete_workflow():
    """Demonstrate complete matching workflow"""
    print("🚀 Phase 2 Complete Integration Demo")
    print("=" * 50)
    
    # Import all components
    from src.utils.fuzzy_matcher import FuzzyMatcher
    from src.utils.semantic_similarity import SemanticSimilarity
    from src.utils.text_normalizer_enhanced import EnhancedTextNormalizer
    from src.utils.brand_alias_manager import BrandAliasManager
    from src.utils.sku_extractor import SkuExtractor
    from src.utils.confidence_calculator import ConfidenceCalculator
    from src.services.advanced_product_matcher import AdvancedProductMatcher
    
    # Test products
    product1 = {
        'id': 'hp_001',
        'name': 'MITSUBISHI แอร์ติดผนัง รุ่น MSY-KP13VF 12000BTU อินเวอร์เตอร์',
        'brand': 'Mitsubishi',
        'category': 'Air Conditioner',
        'specifications': {'capacity': '12000BTU', 'type': 'Split', 'inverter': True},
        'price': 25000,
        'retailer': 'HomePro'
    }
    
    product2 = {
        'id': 'twd_001',
        'name': 'มิตซูบิชิ เครื่องปรับอากาศ MSY-KP13VF 12000 บีทียู Inverter',
        'brand': 'Mitsubishi',
        'category': 'Air Conditioner',
        'specifications': {'capacity': '12000BTU', 'type': 'Split', 'inverter': True},
        'price': 25500,
        'retailer': 'Thai Watsadu'
    }
    
    print("📝 Test Products:")
    print(f"  Product 1: {product1['name']}")
    print(f"  Product 2: {product2['name']}")
    print()
    
    # Step 1: Text Normalization
    print("🔄 Step 1: Text Normalization")
    normalizer = EnhancedTextNormalizer()
    
    norm1 = normalizer.normalize(product1['name'])
    norm2 = normalizer.normalize(product2['name'])
    
    print(f"  Normalized 1: {norm1}")
    print(f"  Normalized 2: {norm2}")
    print()
    
    # Step 2: Brand Management
    print("🏢 Step 2: Brand Management")
    brand_manager = BrandAliasManager()
    
    brand1 = brand_manager.normalize_brand(product1['brand'])
    brand2 = brand_manager.normalize_brand(product2['brand'])
    
    print(f"  Brand 1: {product1['brand']} -> {brand1}")
    print(f"  Brand 2: {product2['brand']} -> {brand2}")
    print()
    
    # Step 3: SKU Extraction
    print("🔍 Step 3: SKU Extraction")
    sku_extractor = SkuExtractor()
    
    sku1 = sku_extractor.extract_sku(product1['name'])
    sku2 = sku_extractor.extract_sku(product2['name'])
    
    print(f"  SKU 1: {sku1.sku if sku1 else 'None'} (confidence: {sku1.confidence if sku1 else 0:.3f})")
    print(f"  SKU 2: {sku2.sku if sku2 else 'None'} (confidence: {sku2.confidence if sku2 else 0:.3f})")
    print()
    
    # Step 4: Fuzzy Matching
    print("🔀 Step 4: Fuzzy String Matching")
    fuzzy_matcher = FuzzyMatcher()
    
    fuzzy_result = fuzzy_matcher.calculate_similarity(product1['name'], product2['name'])
    
    print(f"  Fuzzy Similarity: {fuzzy_result.similarity:.3f}")
    print(f"  Confidence: {fuzzy_result.confidence:.3f}")
    print(f"  Top algorithms:")
    for method, score in list(fuzzy_result.details['individual_scores'].items())[:3]:
        print(f"    {method}: {score:.3f}")
    print()
    
    # Step 5: Semantic Similarity
    print("🧠 Step 5: Semantic Similarity")
    semantic = SemanticSimilarity()
    
    # Train with sample data
    training_data = [
        product1['name'], product2['name'],
        'Samsung Smart TV 55 นิ้ว',
        'LG ตู้เย็น 300 ลิตร',
        'Panasonic เครื่องซักผ้า 8 กิโลกรัม',
        'Daikin แอร์ 24000 BTU'
    ]
    semantic.train(training_data)
    
    semantic_result = semantic.calculate_similarity(product1['name'], product2['name'])
    
    print(f"  Semantic Similarity: {semantic_result.similarity:.3f}")
    print(f"  Method: {semantic_result.method}")
    print()
    
    # Step 6: Confidence Calculation
    print("📊 Step 6: Confidence Calculation")
    confidence_calc = ConfidenceCalculator()
    
    confidence_result = confidence_calc.calculate_confidence(product1, product2)
    
    print(f"  Overall Confidence: {confidence_result.overall_confidence:.3f}")
    print(f"  Top factors:")
    sorted_factors = sorted(confidence_result.breakdown.items(), key=lambda x: x[1], reverse=True)
    for factor, score in sorted_factors[:5]:
        print(f"    {factor}: {score:.3f}")
    print()
    
    # Step 7: Advanced Product Matching
    print("🎯 Step 7: Advanced Product Matching")
    advanced_matcher = AdvancedProductMatcher()
    
    start_time = time.time()
    match_result = advanced_matcher.match_products(product1, product2)
    processing_time = time.time() - start_time
    
    print(f"  Final Match Confidence: {match_result.confidence:.3f}")
    print(f"  Processing Time: {processing_time:.4f} seconds")
    print(f"  Match Decision: {'✅ MATCH' if match_result.confidence > 0.7 else '❌ NO MATCH'}")
    
    if hasattr(match_result, 'details') and match_result.details:
        print(f"  Key factors:")
        for key, value in list(match_result.details.items())[:3]:
            if isinstance(value, (int, float)):
                print(f"    {key}: {value:.3f}")
            else:
                print(f"    {key}: {str(value)[:50]}...")
    
    print()
    
    # Summary
    print("📋 Workflow Summary:")
    print(f"  • Text normalization: ✅")
    print(f"  • Brand management: ✅")
    print(f"  • SKU extraction: ✅")
    print(f"  • Fuzzy matching: {fuzzy_result.similarity:.3f}")
    print(f"  • Semantic similarity: {semantic_result.similarity:.3f}")
    print(f"  • Confidence calculation: {confidence_result.overall_confidence:.3f}")
    print(f"  • Final matching: {match_result.confidence:.3f}")
    print(f"  • Processing time: {processing_time:.4f}s")
    
    print("\n🎉 Phase 2 Integration Demo Complete!")
    print("All ML components working together successfully!")
    
    return True

if __name__ == "__main__":
    demo_complete_workflow()