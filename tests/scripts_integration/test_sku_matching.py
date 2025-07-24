#!/usr/bin/env python3
"""
Test script to demonstrate SKU matching functionality
"""
import asyncio
from src.utils.text_normalizer import TextNormalizer, ProductMatcher

async def test_sku_matching():
    """Test SKU extraction and matching"""
    
    normalizer = TextNormalizer()
    matcher = ProductMatcher()
    
    print("🔍 SKU Matching Demonstration")
    print("=" * 80)
    
    # Test cases with various SKU formats
    test_cases = [
        {
            "name": "Basic SKU Match",
            "product1": "MITSUBISHI แอร์ติดผนัง รุ่น MSY-KP13VF 12000BTU",
            "product2": "มิตซูบิชิ เครื่องปรับอากาศ MSY-KP13VF 12,000 บีทียู",
            "brand1": "MITSUBISHI",
            "brand2": "มิตซูบิชิ"
        },
        {
            "name": "Different Format SKU",
            "product1": "DAIKIN แอร์ FTKF24UV2S Inverter 24000 BTU",
            "product2": "ไดกิ้น รุ่น FTKF24UV2S อินเวอร์เตอร์ 24,000บีทียู",
            "brand1": "DAIKIN",
            "brand2": "ไดกิ้น"
        },
        {
            "name": "SKU with Dashes",
            "product1": "Samsung เครื่องซักผ้า WW90T554DAW/ST 9kg",
            "product2": "ซัมซุง รุ่น WW90T554DAW-ST ขนาด 9 กก.",
            "brand1": "Samsung",
            "brand2": "ซัมซุง"
        },
        {
            "name": "Complex Model Number",
            "product1": "LG ตู้เย็น 2 ประตู GN-X392PBGB 14 คิว",
            "product2": "แอลจี ตู้เย็น GN-X392PBGB ขนาด 14 คิว 2 ประตู",
            "brand1": "LG",
            "brand2": "แอลจี"
        },
        {
            "name": "No SKU Match",
            "product1": "พัดลมติดผนัง 16 นิ้ว HATARI",
            "product2": "พัดลมติดผนัง HATARI ขนาด 18 นิ้ว",
            "brand1": "HATARI",
            "brand2": "HATARI"
        },
        {
            "name": "Partial SKU in Name",
            "product1": "PANASONIC CS-PU24WKT แอร์ 24000BTU",
            "product2": "พานาโซนิค แอร์ติดผนัง PU24WKT 24,000 บีทียู",
            "brand1": "PANASONIC",
            "brand2": "พานาโซนิค"
        }
    ]
    
    for i, test in enumerate(test_cases, 1):
        print(f"\n📌 Test Case {i}: {test['name']}")
        print("-" * 60)
        
        # Extract SKUs
        sku1 = normalizer.extract_sku(test['product1'])
        sku2 = normalizer.extract_sku(test['product2'])
        
        print(f"Product 1: {test['product1']}")
        print(f"SKU 1: {sku1 or 'None found'}")
        print(f"\nProduct 2: {test['product2']}")
        print(f"SKU 2: {sku2 or 'None found'}")
        
        # Perform matching
        match_result = matcher.match_products(
            test['product1'],
            test['product2'],
            test['brand1'],
            test['brand2']
        )
        
        print(f"\n🎯 Matching Results:")
        print(f"   SKU Match Score: {match_result['sku_match']:.2f}")
        print(f"   Name Similarity: {match_result['name_similarity']:.2f}")
        print(f"   Brand Match: {match_result['brand_match']:.2f}")
        print(f"   Spec Match: {match_result['spec_match']:.2f}")
        confidence = match_result.get('confidence', match_result.get('overall_confidence', 0))
        print(f"   Overall Confidence: {confidence:.2f}")
        print(f"   Is Match: {'✅ YES' if confidence >= 0.7 else '❌ NO'}")
        
        if match_result['sku_match'] == 1.0:
            print(f"   💡 SKU Match Details: Both products have SKU '{sku1}'")
    
    # Test SKU extraction patterns
    print("\n\n🔧 SKU Extraction Pattern Tests")
    print("=" * 80)
    
    sku_samples = [
        "แอร์ MITSUBISHI MSY-KP13VF 12000BTU",
        "รุ่น CS-PU24WKT",
        "Model: WW90T554DAW/ST",
        "DAIKIN FTKF24UV2S",
        "LG GN-X392PBGB",
        "Samsung รุ่น RT22FGRADSA/ST",
        "เครื่องซักผ้า NA-F70B3 7kg",
        "Product Code: ABC-123-XYZ",
        "Item #12345",
        "SKU: MH-2023-001"
    ]
    
    print("\nTesting various SKU formats:")
    for sample in sku_samples:
        extracted = normalizer.extract_sku(sample)
        print(f"  '{sample}' → SKU: {extracted or 'None'}")
    
    # Test normalization of SKUs
    print("\n\n🔄 SKU Normalization Tests")
    print("=" * 80)
    
    sku_pairs = [
        ("MSY-KP13VF", "MSY-KP13VF"),
        ("WW90T554DAW/ST", "WW90T554DAW-ST"),
        ("CS-PU24WKT", "PU24WKT"),
        ("FTKF24UV2S", "FTKF24UV2S"),
        ("GN-X392PBGB", "GN-X392PBGB")
    ]
    
    print("\nTesting SKU normalization and comparison:")
    for sku1, sku2 in sku_pairs:
        norm1 = normalizer.normalize_sku(sku1)
        norm2 = normalizer.normalize_sku(sku2)
        match = normalizer.compare_skus(sku1, sku2)
        print(f"  '{sku1}' vs '{sku2}'")
        print(f"    Normalized: '{norm1}' vs '{norm2}'")
        print(f"    Match: {'✅ YES' if match else '❌ NO'}")

if __name__ == "__main__":
    asyncio.run(test_sku_matching())