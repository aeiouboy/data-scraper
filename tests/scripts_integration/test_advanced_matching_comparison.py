"""
Test script to compare original vs advanced matching algorithms
Demonstrates improvements in Thai-English price matching
"""
import asyncio
import json
import time
from typing import Dict, List, Any, Tuple
from datetime import datetime

# Import both matchers for comparison
from src.utils.product_matcher_enhanced import EnhancedProductMatcher
from src.utils.product_matcher_advanced import AdvancedProductMatcher
from src.utils.text_normalizer_enhanced import EnhancedTextNormalizer
from src.utils.text_normalizer_advanced import AdvancedTextNormalizer

class MatchingComparison:
    """Compare original and advanced matching algorithms"""
    
    def __init__(self):
        self.original_matcher = EnhancedProductMatcher()
        self.advanced_matcher = AdvancedProductMatcher()
        self.original_normalizer = EnhancedTextNormalizer()
        self.advanced_normalizer = AdvancedTextNormalizer()
    
    def create_test_products(self) -> List[Tuple[Dict[str, Any], Dict[str, Any], str]]:
        """Create test product pairs with expected match quality"""
        return [
            # Test 1: Thai brand vs English brand (same product)
            (
                {
                    'id': 'p1',
                    'name': 'แอร์มิตซูบิชิ รุ่น MSY-KP13VF 12000 BTU',
                    'brand': 'มิตซูบิชิ',
                    'sku': 'MSY-KP13VF',
                    'price': 15900,
                    'specs': {'btu': 12000, 'type': 'wall'},
                    'category': 'air_conditioner'
                },
                {
                    'id': 'p2',
                    'name': 'Mitsubishi Air Conditioner MSY-KP13VF 12000BTU',
                    'brand': 'Mitsubishi',
                    'sku': 'MSYKP13VF',
                    'price': 16500,
                    'specs': {'btu': 12000, 'type': 'wall'},
                    'category': 'air_conditioner'
                },
                'Should match with high confidence - same model, different language'
            ),
            
            # Test 2: Phonetic variations
            (
                {
                    'id': 'p3',
                    'name': 'เครื่องปรับอากาศ ไดกิ้น FTKF25UV2S อินเวอร์เตอร์',
                    'brand': 'ไดกิ้น',
                    'sku': 'FTKF25UV2S',
                    'price': 22900,
                    'specs': {'btu': 9000, 'inverter': True},
                    'category': 'แอร์'
                },
                {
                    'id': 'p4',
                    'name': 'Daikin Inverter AC FTKF25UV2S 9000 BTU',
                    'brand': 'DAIKIN',
                    'sku': 'FTKF-25UV2S',
                    'price': 23500,
                    'specs': {'btu': 9000, 'inverter': True},
                    'category': 'Air Conditioner'
                },
                'Should match - phonetic brand match and similar SKU'
            ),
            
            # Test 3: Mixed language product names
            (
                {
                    'id': 'p5',
                    'name': 'Samsung ตู้เย็น 2 ประตู รุ่น RT20HAR1DSA 208 ลิตร',
                    'brand': 'Samsung',
                    'sku': 'RT20HAR1DSA',
                    'price': 8990,
                    'specs': {'capacity': 208, 'doors': 2},
                    'category': 'ตู้เย็น'
                },
                {
                    'id': 'p6',
                    'name': 'ตู้เย็นซัมซุง 2 door model RT20HAR1DSA 208L',
                    'brand': 'ซัมซุง',
                    'sku': 'RT-20HAR1DSA',
                    'price': 9290,
                    'specs': {'capacity': 208, 'doors': 2},
                    'category': 'Refrigerator'
                },
                'Should match - mixed language with same model'
            ),
            
            # Test 4: Abbreviations and variations
            (
                {
                    'id': 'p7',
                    'name': 'LG แอร์ 18000บีทียู รุ่น IG18R.SE1 Dual Inverter',
                    'brand': 'LG',
                    'sku': 'IG18R.SE1',
                    'price': 24900,
                    'specs': {'btu': 18000, 'inverter': True},
                    'category': 'เครื่องปรับอากาศ'
                },
                {
                    'id': 'p8',
                    'name': 'แอลจี Dual Inverter 18000BTU Model IG18R-SE1',
                    'brand': 'แอลจี',
                    'sku': 'IG18RSE1',
                    'price': 25400,
                    'specs': {'btu': 18000, 'inverter': True},
                    'category': 'Air Conditioner'
                },
                'Should match - abbreviation handling'
            ),
            
            # Test 5: Different products (should not match)
            (
                {
                    'id': 'p9',
                    'name': 'Panasonic แอร์ติดผนัง 12000 BTU รุ่น CS-PU12WKT',
                    'brand': 'Panasonic',
                    'sku': 'CS-PU12WKT',
                    'price': 16900,
                    'specs': {'btu': 12000},
                    'category': 'แอร์'
                },
                {
                    'id': 'p10',
                    'name': 'พานาโซนิค ตู้เย็น 2 ประตู NR-BX418VS 407 ลิตร',
                    'brand': 'พานาโซนิค',
                    'sku': 'NR-BX418VS',
                    'price': 18900,
                    'specs': {'capacity': 407, 'doors': 2},
                    'category': 'ตู้เย็น'
                },
                'Should NOT match - different product types'
            ),
            
            # Test 6: Typos and misspellings
            (
                {
                    'id': 'p11',
                    'name': 'ไฮเซนส์ แอร์ อินเวอเตอร์ 12000 BTU รุ่น AS12TQ',
                    'brand': 'ไฮเซนส์',
                    'sku': 'AS12TQ',
                    'price': 11900,
                    'specs': {'btu': 12000, 'inverter': True},
                    'category': 'แอร์'
                },
                {
                    'id': 'p12',
                    'name': 'Hisense Inveter Air 12,000BTU Model AS-12TQ',  # Note: "Inveter" typo
                    'brand': 'Hisense',
                    'sku': 'AS12TQ',
                    'price': 12400,
                    'specs': {'btu': 12000, 'inverter': True},
                    'category': 'air conditioner'
                },
                'Should match despite typo in "Inverter"'
            ),
            
            # Test 7: Complex model numbers
            (
                {
                    'id': 'p13',
                    'name': 'Sharp แอร์ AH-X12SEV 12050 BTU Plasmacluster',
                    'brand': 'Sharp',
                    'sku': 'AH-X12SEV',
                    'price': 15900,
                    'specs': {'btu': 12050, 'features': ['plasmacluster']},
                    'category': 'แอร์บ้าน'
                },
                {
                    'id': 'p14',
                    'name': 'ชาร์ป แอร์ติดผนัง AHX12SEV 12050BTU พลาสม่าคลัสเตอร์',
                    'brand': 'ชาร์ป',
                    'sku': 'AH X12 SEV',
                    'price': 16200,
                    'specs': {'btu': 12050, 'features': ['plasma cluster']},
                    'category': 'Air Conditioner'
                },
                'Should match - handle model number variations'
            ),
            
            # Test 8: Similar but different models
            (
                {
                    'id': 'p15',
                    'name': 'Daikin FTKF25UV2S Inverter 9000 BTU',
                    'brand': 'Daikin',
                    'sku': 'FTKF25UV2S',
                    'price': 21900,
                    'specs': {'btu': 9000, 'series': 'FTKF'},
                    'category': 'air_conditioner'
                },
                {
                    'id': 'p16',
                    'name': 'Daikin FTKF35UV2S Inverter 12000 BTU',
                    'brand': 'Daikin',
                    'sku': 'FTKF35UV2S',
                    'price': 26900,
                    'specs': {'btu': 12000, 'series': 'FTKF'},
                    'category': 'air_conditioner'
                },
                'Should have medium match - same series, different model'
            )
        ]
    
    def run_comparison(self) -> Dict[str, Any]:
        """Run comparison tests"""
        test_products = self.create_test_products()
        results = []
        
        print("=" * 80)
        print("PRICE MATCHING ALGORITHM COMPARISON TEST")
        print("=" * 80)
        print()
        
        for i, (product1, product2, description) in enumerate(test_products, 1):
            print(f"Test {i}: {description}")
            print("-" * 80)
            
            # Original matcher
            start_time = time.time()
            original_result = self.original_matcher.match_products(product1, product2)
            original_time = time.time() - start_time
            
            # Advanced matcher
            start_time = time.time()
            advanced_result = self.advanced_matcher.match_products(product1, product2)
            advanced_time = time.time() - start_time
            
            # Display results
            self._display_comparison(
                product1, product2,
                original_result, advanced_result,
                original_time, advanced_time
            )
            
            # Store results
            results.append({
                'test_number': i,
                'description': description,
                'products': {
                    'product1': self._format_product(product1),
                    'product2': self._format_product(product2)
                },
                'original_result': {
                    'confidence': original_result.confidence,
                    'match_type': original_result.match_type,
                    'matched_fields': original_result.matched_fields,
                    'time_ms': round(original_time * 1000, 2)
                },
                'advanced_result': {
                    'confidence': advanced_result.confidence,
                    'match_type': advanced_result.match_type,
                    'matched_fields': advanced_result.matched_fields,
                    'linguistic_scores': advanced_result.linguistic_scores,
                    'time_ms': round(advanced_time * 1000, 2)
                },
                'improvement': {
                    'confidence_diff': advanced_result.confidence - original_result.confidence,
                    'better_match': advanced_result.match_type != original_result.match_type,
                    'speed_improvement': original_time - advanced_time
                }
            })
            
            print()
        
        # Summary
        self._display_summary(results)
        
        return {
            'test_results': results,
            'summary': self._calculate_summary(results),
            'timestamp': datetime.now().isoformat()
        }
    
    def _display_comparison(
        self,
        product1: Dict[str, Any],
        product2: Dict[str, Any],
        original_result: Any,
        advanced_result: Any,
        original_time: float,
        advanced_time: float
    ):
        """Display comparison results"""
        print(f"\nProduct 1: {product1['name']}")
        print(f"Product 2: {product2['name']}")
        print()
        
        print("Original Matcher Results:")
        print(f"  Confidence: {original_result.confidence:.3f}")
        print(f"  Match Type: {original_result.match_type}")
        print(f"  Matched Fields: {', '.join(original_result.matched_fields)}")
        print(f"  Time: {original_time*1000:.2f}ms")
        
        print("\nAdvanced Matcher Results:")
        print(f"  Confidence: {advanced_result.confidence:.3f}")
        print(f"  Match Type: {advanced_result.match_type}")
        print(f"  Matched Fields: {', '.join(advanced_result.matched_fields)}")
        
        # Show linguistic scores
        if hasattr(advanced_result, 'linguistic_scores') and advanced_result.linguistic_scores:
            print("  Linguistic Analysis:")
            for field, scores in advanced_result.linguistic_scores.items():
                if scores:
                    print(f"    {field}: {', '.join(f'{k}={v:.2f}' for k, v in scores.items())}")
        
        print(f"  Time: {advanced_time*1000:.2f}ms")
        
        # Improvement
        conf_diff = advanced_result.confidence - original_result.confidence
        if conf_diff > 0:
            print(f"\n✅ Improvement: +{conf_diff:.3f} confidence")
        elif conf_diff < 0:
            print(f"\n⚠️  Regression: {conf_diff:.3f} confidence")
        else:
            print(f"\n➖ No change in confidence")
    
    def _format_product(self, product: Dict[str, Any]) -> Dict[str, Any]:
        """Format product for results"""
        return {
            'id': product['id'],
            'name': product['name'],
            'brand': product.get('brand'),
            'sku': product.get('sku'),
            'price': product.get('price'),
            'category': product.get('category')
        }
    
    def _calculate_summary(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate summary statistics"""
        improvements = [r['improvement']['confidence_diff'] for r in results]
        
        original_times = [r['original_result']['time_ms'] for r in results]
        advanced_times = [r['advanced_result']['time_ms'] for r in results]
        
        better_matches = sum(1 for r in results if r['improvement']['confidence_diff'] > 0)
        worse_matches = sum(1 for r in results if r['improvement']['confidence_diff'] < 0)
        
        return {
            'total_tests': len(results),
            'improved_matches': better_matches,
            'worse_matches': worse_matches,
            'unchanged_matches': len(results) - better_matches - worse_matches,
            'average_confidence_improvement': sum(improvements) / len(improvements),
            'max_improvement': max(improvements),
            'min_improvement': min(improvements),
            'average_time': {
                'original_ms': sum(original_times) / len(original_times),
                'advanced_ms': sum(advanced_times) / len(advanced_times)
            },
            'performance_gain': (sum(original_times) - sum(advanced_times)) / sum(original_times) * 100
        }
    
    def _display_summary(self, results: List[Dict[str, Any]]):
        """Display summary of results"""
        summary = self._calculate_summary(results)
        
        print("=" * 80)
        print("SUMMARY")
        print("=" * 80)
        print(f"\nTotal Tests: {summary['total_tests']}")
        print(f"Improved Matches: {summary['improved_matches']} "
              f"({summary['improved_matches']/summary['total_tests']*100:.1f}%)")
        print(f"Worse Matches: {summary['worse_matches']} "
              f"({summary['worse_matches']/summary['total_tests']*100:.1f}%)")
        print(f"Unchanged: {summary['unchanged_matches']}")
        
        print(f"\nAverage Confidence Improvement: {summary['average_confidence_improvement']:+.3f}")
        print(f"Max Improvement: {summary['max_improvement']:+.3f}")
        print(f"Min Improvement: {summary['min_improvement']:+.3f}")
        
        print(f"\nPerformance:")
        print(f"  Original Avg Time: {summary['average_time']['original_ms']:.2f}ms")
        print(f"  Advanced Avg Time: {summary['average_time']['advanced_ms']:.2f}ms")
        print(f"  Performance Gain: {summary['performance_gain']:.1f}%")
    
    def test_normalizers(self):
        """Test text normalizers separately"""
        print("\n" + "=" * 80)
        print("TEXT NORMALIZER COMPARISON")
        print("=" * 80)
        
        test_texts = [
            ('มิตซูบิชิ', 'Thai brand name'),
            ('Mitsubishi Electric', 'English brand with suffix'),
            ('แอร์ไดกิ้น รุ่น FTKF25UV2S', 'Thai text with model'),
            ('Samsung ตู้เย็น 2 ประตู', 'Mixed language'),
            ('12000 BTU', 'Specification'),
            ('12,000 บีทียู', 'Thai specification with comma'),
            ('เครื่องปรับอากาศอินเวอร์เตอร์', 'Thai compound word'),
            ('INVERTER Air Conditioner', 'English terms')
        ]
        
        for text, description in test_texts:
            print(f"\nTest: {description}")
            print(f"Input: '{text}'")
            
            # Original normalizer
            orig_norm = self.original_normalizer.normalize(text)
            orig_tokens = self.original_normalizer.extract_tokens(text)
            
            # Advanced normalizer
            adv_norm = self.advanced_normalizer.normalize(text)
            adv_tokens = self.advanced_normalizer.extract_tokens(text)
            
            print(f"Original Normalized: '{orig_norm}'")
            print(f"Original Tokens: {orig_tokens}")
            print(f"Advanced Normalized: '{adv_norm}'")
            print(f"Advanced Tokens: {adv_tokens}")
            
            # Check for Thai text
            if self.advanced_normalizer.is_thai_text(text):
                print(f"Contains Thai: Yes")
                if hasattr(self.advanced_normalizer, 'romanize_thai'):
                    romanized = self.advanced_normalizer.romanize_thai(text)
                    print(f"Romanized: '{romanized}'")

def main():
    """Main test function"""
    comparison = MatchingComparison()
    
    # Run main comparison
    results = comparison.run_comparison()
    
    # Test normalizers
    comparison.test_normalizers()
    
    # Save results
    output_file = 'matching_comparison_results.json'
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    
    print(f"\n\nResults saved to: {output_file}")
    
    # Show key improvements
    print("\n" + "=" * 80)
    print("KEY IMPROVEMENTS IN ADVANCED MATCHER:")
    print("=" * 80)
    print("1. ✅ Better Thai-English brand matching (phonetic matching)")
    print("2. ✅ Improved model number normalization and matching")
    print("3. ✅ N-gram based similarity for partial matches")
    print("4. ✅ Linguistic analysis for cross-language matching")
    print("5. ✅ Context-aware weighting based on product category")
    print("6. ✅ Fuzzy matching for typos and variations")
    print("7. ✅ Better handling of mixed-language product names")
    print("8. ✅ Phonetic transliteration for Thai brands")

if __name__ == "__main__":
    main()