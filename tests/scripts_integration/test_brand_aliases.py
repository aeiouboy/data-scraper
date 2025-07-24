#!/usr/bin/env python3
"""
Test brand aliases functionality
"""
import asyncio
from src.services.supabase_service import SupabaseService
from src.utils.text_normalizer import TextNormalizer, ProductMatcher

async def test_brand_aliases():
    """Test the brand aliases functionality"""
    
    print("🧪 Testing Brand Aliases Functionality")
    print("=" * 60)
    
    # Initialize services
    supabase = SupabaseService()
    normalizer = TextNormalizer()
    matcher = ProductMatcher()
    
    # Test 1: Check if brand aliases were inserted
    print("\n1️⃣ Testing brand aliases in database...")
    try:
        result = supabase.client.table('brand_aliases').select('*').limit(10).execute()
        print(f"   ✅ Found {len(result.data)} brand aliases in database")
        for alias in result.data[:5]:
            print(f"      - {alias['alias']} → {alias['canonical_brand']} ({alias['language']})")
    except Exception as e:
        print(f"   ❌ Error: {str(e)}")
    
    # Test 2: Test get_canonical_brand function
    print("\n2️⃣ Testing get_canonical_brand function...")
    test_brands = [
        ('มิตซูบิชิ', 'MITSUBISHI'),
        ('samsung', 'SAMSUNG'),
        ('แอลจี', 'LG'),
        ('Unknown Brand', 'UNKNOWN BRAND')  # Should return uppercase of original
    ]
    
    for brand_input, expected in test_brands:
        try:
            result = supabase.client.rpc('get_canonical_brand', {'brand_name': brand_input}).execute()
            canonical = result.data if result.data else brand_input.upper()
            status = "✅" if canonical == expected else "❌"
            print(f"   {status} '{brand_input}' → '{canonical}' (expected: '{expected}')")
        except Exception as e:
            print(f"   ❌ Error testing '{brand_input}': {str(e)}")
    
    # Test 3: Test text normalization with real products
    print("\n3️⃣ Testing text normalization...")
    test_texts = [
        "MITSUBISHI แอร์ติดผนัง รุ่น MSY-KP13VF 12000BTU",
        "มิตซูบิชิ เครื่องปรับอากาศ MSY-KP13VF 12,000 บีทียู",
        "Samsung ตู้เย็น 2 ประตู 300 ลิตร RT29K5511S8",
        "ซัมซุง ตู้เย็น 2 ประตู 300L รุ่น RT29K5511S8"
    ]
    
    for text in test_texts:
        normalized = normalizer.normalize(text)
        sku = normalizer.extract_sku(text)
        specs = normalizer.extract_specifications(text)
        print(f"\n   Original: {text}")
        print(f"   Normalized: {normalized}")
        print(f"   SKU: {sku}")
        print(f"   Specs: {specs}")
    
    # Test 4: Test complete product matching
    print("\n\n4️⃣ Testing complete product matching...")
    match_tests = [
        {
            'p1': "MITSUBISHI แอร์ติดผนัง รุ่น MSY-KP13VF 12000BTU",
            'p2': "มิตซูบิชิ เครื่องปรับอากาศ MSY-KP13VF 12,000 บีทียู",
            'b1': "MITSUBISHI",
            'b2': "มิตซูบิชิ"
        },
        {
            'p1': "Samsung ตู้เย็น 2 ประตู 300 ลิตร RT29K5511S8",
            'p2': "ซัมซุง ตู้เย็น 2 ประตู 300L รุ่น RT29K5511S8",
            'b1': "Samsung",
            'b2': "ซัมซุง"
        }
    ]
    
    for test in match_tests:
        result = matcher.match_products(test['p1'], test['p2'], test['b1'], test['b2'])
        print(f"\n   Product 1: {test['p1']}")
        print(f"   Product 2: {test['p2']}")
        print(f"   Match Confidence: {result['overall_confidence']:.1%}")
        print(f"   Details:")
        print(f"      - Name similarity: {result['name_similarity']:.1%}")
        print(f"      - Brand match: {'✅' if result['brand_match'] > 0.8 else '❌'}")
        print(f"      - SKU match: {'✅' if result['sku_match'] == 1.0 else '❌'}")
        print(f"      - Spec match: {result['spec_match']:.1%}")
    
    print("\n" + "=" * 60)
    print("✅ Brand aliases testing completed!")

if __name__ == "__main__":
    asyncio.run(test_brand_aliases())