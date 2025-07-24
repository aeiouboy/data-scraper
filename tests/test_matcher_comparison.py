"""
Test script to compare original matcher vs optimized matcher
Demonstrates improved matching rates and accuracy
"""
import sys
import os
import json
import time
from typing import Dict, List, Any, Tuple
from dataclasses import asdict

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from src.utils.product_matcher_advanced import AdvancedProductMatcher
from src.utils.product_matcher_optimized import OptimizedProductMatcher

class MatcherComparison:
    """Compare original and optimized product matchers"""
    
    def __init__(self):
        self.advanced_matcher = AdvancedProductMatcher()
        self.optimized_matcher = OptimizedProductMatcher()
        
        # Test cases representing real-world scenarios with low matching rates
        self.test_cases = [
            # Electronics - Air Conditioners (Thai-English variations)
            {
                'product1': {
                    'id': '1',
                    'name': 'Mitsubishi Electric MSY-JP13VF Inverter 12000 BTU',
                    'brand': 'Mitsubishi Electric',
                    'sku': 'MSY-JP13VF',
                    'category': 'air conditioner',
                    'price': 18900,
                    'specs': {'capacity': 12000, 'type': 'inverter', 'voltage': 220}
                },
                'product2': {
                    'id': '2',
                    'name': 'มิตซูบิชิ อิเล็กทริก แอร์ 12000 บีทียู อินเวอร์เตอร์ รุ่น MSY-JP13VF',
                    'brand': 'มิตซูบิชิ',
                    'sku': 'MSY-JP13VF',
                    'category': 'เครื่องปรับอากาศ',
                    'price': 19200,
                    'specs': {'capacity': 12000, 'type': 'อินเวอร์เตอร์', 'voltage': 220}
                },
                'expected_match': True,
                'description': 'Thai-English same product with slight price difference'
            },
            
            # Similar models with minor differences
            {
                'product1': {
                    'id': '3',
                    'name': 'LG Dual Cool Inverter 18000 BTU WiFi Smart AC',
                    'brand': 'LG',
                    'sku': 'AC18DL-B1',
                    'category': 'air conditioner',
                    'price': 29500,
                    'specs': {'capacity': 18000, 'type': 'inverter', 'features': 'wifi'}
                },
                'product2': {
                    'id': '4',
                    'name': 'LG Dual Cool Inverter Air Conditioner 18K BTU with WiFi',
                    'brand': 'LG Electronics',
                    'sku': 'AC18DL',
                    'category': 'cooling',
                    'price': 28900,
                    'specs': {'capacity': 18000, 'type': 'inverter', 'connectivity': 'wifi'}
                },
                'expected_match': True,
                'description': 'Similar LG models with slight SKU and naming differences'
            },
            
            # Brand variations and abbreviations
            {
                'product1': {
                    'id': '5',
                    'name': 'Samsung Digital Inverter 24000 BTU AR24',
                    'brand': 'Samsung',
                    'sku': 'AR24TXHYAWKN',
                    'category': 'air conditioner',
                    'price': 45000,
                    'specs': {'capacity': 24000, 'type': 'digital inverter'}
                },
                'product2': {
                    'id': '6',
                    'name': 'ซัมซุง แอร์ดิจิตอลอินเวอร์เตอร์ 24000 บีทียู รุ่น AR24',
                    'brand': 'ซัมซุง',
                    'sku': 'AR24TXHYAWK',
                    'category': 'เครื่องปรับอากาศ',
                    'price': 46500,
                    'specs': {'capacity': 24000, 'type': 'ดิจิตอล อินเวอร์เตอร์'}
                },
                'expected_match': True,
                'description': 'Samsung with Thai brand name and partial SKU match'
            },
            
            # Different retailers, same product, different descriptions
            {
                'product1': {
                    'id': '7',
                    'name': 'Daikin FTKC25TV16 Inverter 9000 BTU R32 Eco',
                    'brand': 'Daikin',
                    'sku': 'FTKC25TV16',
                    'category': 'air conditioner',
                    'price': 22900,
                    'retailer_code': 'HP',
                    'specs': {'capacity': 9000, 'refrigerant': 'R32', 'type': 'inverter'}
                },
                'product2': {
                    'id': '8',
                    'name': 'ไดกิ้น แอร์ติดผนัง อินเวอร์เตอร์ 9000 BTU FTKC25TV16 ประหยัดไฟ',
                    'brand': 'Daikin',
                    'sku': 'FTKC25TV16',
                    'category': 'เครื่องปรับอากาศ',
                    'price': 23400,
                    'retailer_code': 'TWD',
                    'specs': {'capacity': 9000, 'type': 'อินเวอร์เตอร์', 'energy_saving': True}
                },
                'expected_match': True,
                'description': 'Same Daikin product from different retailers'
            },
            
            # Specification variations
            {
                'product1': {
                    'id': '9',
                    'name': 'Carrier X-Series Inverter 12000 BTU 1.5 Ton',
                    'brand': 'Carrier',
                    'sku': 'CVA-X12',
                    'category': 'air conditioner',
                    'price': 32000,
                    'specs': {'capacity': 12000, 'tonnage': 1.5, 'type': 'inverter'}
                },
                'product2': {
                    'id': '10',
                    'name': 'Carrier X Series Air Conditioner 1.5HP Inverter',
                    'brand': 'Carrier Corporation',
                    'sku': 'CVA-X12-IN',
                    'category': 'cooling system',
                    'price': 31500,
                    'specs': {'power': 1.5, 'unit': 'hp', 'type': 'inverter'}
                },
                'expected_match': True,
                'description': 'Same product with BTU vs HP capacity specifications'
            },
            
            # Price variations that might cause low matching
            {
                'product1': {
                    'id': '11',
                    'name': 'Toshiba Inverter 18000 BTU RAS-18S3KS-TH',
                    'brand': 'Toshiba',
                    'sku': 'RAS-18S3KS-TH',
                    'category': 'air conditioner',
                    'price': 28000,
                    'specs': {'capacity': 18000, 'type': 'inverter'}
                },
                'product2': {
                    'id': '12',
                    'name': 'Toshiba Inverter Air Conditioner 18K BTU RAS-18S3KS',
                    'brand': 'Toshiba',
                    'sku': 'RAS18S3KS',
                    'category': 'air conditioning',
                    'price': 35000,  # 25% price difference
                    'specs': {'capacity': 18000, 'type': 'inverter'}
                },
                'expected_match': True,
                'description': 'Same Toshiba product with significant price difference'
            },
            
            # Different product categories but similar names
            {
                'product1': {
                    'id': '13',
                    'name': 'Panasonic Inverter Refrigerator 14.2 cu.ft',
                    'brand': 'Panasonic',
                    'sku': 'NR-BL342PS',
                    'category': 'refrigerator',
                    'price': 25000,
                    'specs': {'capacity': 14.2, 'unit': 'cu.ft', 'type': 'inverter'}
                },
                'product2': {
                    'id': '14',
                    'name': 'Panasonic Inverter Air Conditioner 14000 BTU',
                    'brand': 'Panasonic',
                    'sku': 'CS-YN13SKT',
                    'category': 'air conditioner',
                    'price': 24000,
                    'specs': {'capacity': 14000, 'unit': 'btu', 'type': 'inverter'}
                },
                'expected_match': False,
                'description': 'Different Panasonic products - should NOT match'
            },
            
            # Appliances - Washing Machines
            {
                'product1': {
                    'id': '15',
                    'name': 'LG Front Load Washing Machine 9kg TurboWash F2514NTGW',
                    'brand': 'LG',
                    'sku': 'F2514NTGW',
                    'category': 'washing machine',
                    'price': 18900,
                    'specs': {'capacity': 9, 'type': 'front load', 'features': 'turbowash'}
                },
                'product2': {
                    'id': '16',
                    'name': 'แอลจี เครื่องซักผ้าฝาหน้า 9 กิโลกรัม รุ่น F2514NTGW TurboWash',
                    'brand': 'LG',
                    'sku': 'F2514NTGW',
                    'category': 'เครื่องซักผ้า',
                    'price': 19200,
                    'specs': {'capacity': 9, 'type': 'ฝาหน้า', 'features': 'turbowash'}
                },
                'expected_match': True,
                'description': 'Thai-English washing machine same model'
            },
            
            # Electronics with model variations
            {
                'product1': {
                    'id': '17',
                    'name': 'Sony Bravia 55" 4K Smart TV KD-55X75K',
                    'brand': 'Sony',
                    'sku': 'KD-55X75K',
                    'category': 'television',
                    'price': 28900,
                    'specs': {'size': 55, 'resolution': '4k', 'smart': True}
                },
                'product2': {
                    'id': '18',
                    'name': 'Sony Bravia 55 inch 4K Smart Television Model KD55X75K',
                    'brand': 'Sony Corporation',
                    'sku': 'KD55X75K',
                    'category': 'smart tv',
                    'price': 29500,
                    'specs': {'screen_size': 55, 'resolution': '4k uhd', 'connectivity': 'smart'}
                },
                'expected_match': True,
                'description': 'Sony TV with minor SKU formatting difference'
            },
            
            # Tools/Equipment
            {
                'product1': {
                    'id': '19',
                    'name': 'Bosch Professional Impact Drill 18V GSB 18V-55',
                    'brand': 'Bosch',
                    'sku': 'GSB18V-55',
                    'category': 'power tools',
                    'price': 8900,
                    'specs': {'voltage': 18, 'type': 'impact drill', 'series': 'professional'}
                },
                'product2': {
                    'id': '20',
                    'name': 'Bosch สว่านกระแทก 18 โวลต์ รุ่น GSB18V55 Professional',
                    'brand': 'Bosch',
                    'sku': 'GSB18V55',
                    'category': 'เครื่องมือช่าง',
                    'price': 9200,
                    'specs': {'voltage': 18, 'type': 'สว่านกระแทก', 'series': 'professional'}
                },
                'expected_match': True,
                'description': 'Bosch tool with Thai translation'
            }
        ]
    
    def run_comparison(self) -> Dict[str, Any]:
        """Run comparison between advanced and optimized matchers"""
        
        print("🔄 Running Product Matcher Comparison...")
        print("=" * 60)
        
        results = {
            'test_cases': len(self.test_cases),
            'advanced_matcher': {
                'matches_found': 0,
                'correct_matches': 0,
                'false_positives': 0,
                'false_negatives': 0,
                'total_time': 0,
                'confidence_scores': []
            },
            'optimized_matcher': {
                'matches_found': 0,
                'correct_matches': 0,
                'false_positives': 0,
                'false_negatives': 0,
                'total_time': 0,
                'confidence_scores': []
            },
            'detailed_results': []
        }
        
        for i, test_case in enumerate(self.test_cases, 1):
            print(f"\n📋 Test Case {i}: {test_case['description']}")
            print("-" * 50)
            
            product1 = test_case['product1']
            product2 = test_case['product2']
            expected_match = test_case['expected_match']
            
            # Test Advanced Matcher
            start_time = time.time()
            advanced_result = self.advanced_matcher.match_products(product1, product2)
            advanced_time = time.time() - start_time
            
            # Test Optimized Matcher
            start_time = time.time()
            optimized_result = self.optimized_matcher.match_products_progressive(product1, product2)
            optimized_time = time.time() - start_time
            
            # Analyze results
            advanced_match = advanced_result.confidence >= 0.55  # Advanced matcher threshold
            optimized_match = optimized_result.confidence >= 0.35  # Optimized matcher threshold
            
            # Update statistics
            results['advanced_matcher']['total_time'] += advanced_time
            results['optimized_matcher']['total_time'] += optimized_time
            
            results['advanced_matcher']['confidence_scores'].append(advanced_result.confidence)
            results['optimized_matcher']['confidence_scores'].append(optimized_result.confidence)
            
            if advanced_match:
                results['advanced_matcher']['matches_found'] += 1
                if expected_match:
                    results['advanced_matcher']['correct_matches'] += 1
                else:
                    results['advanced_matcher']['false_positives'] += 1
            elif expected_match:
                results['advanced_matcher']['false_negatives'] += 1
            
            if optimized_match:
                results['optimized_matcher']['matches_found'] += 1
                if expected_match:
                    results['optimized_matcher']['correct_matches'] += 1
                else:
                    results['optimized_matcher']['false_positives'] += 1
            elif expected_match:
                results['optimized_matcher']['false_negatives'] += 1
            
            # Print results for this test case
            print(f"Expected Match: {'✅ YES' if expected_match else '❌ NO'}")
            print(f"Advanced Matcher:  Confidence: {advanced_result.confidence:.3f} | Match: {'✅' if advanced_match else '❌'} | Time: {advanced_time:.3f}s")
            print(f"Optimized Matcher: Confidence: {optimized_result.confidence:.3f} | Match: {'✅' if optimized_match else '❌'} | Time: {optimized_time:.3f}s")
            
            # Detailed comparison
            improvement = optimized_result.confidence - advanced_result.confidence
            improvement_icon = "📈" if improvement > 0 else "📉" if improvement < 0 else "➡️"
            print(f"Confidence Improvement: {improvement_icon} {improvement:+.3f}")
            
            # Store detailed results
            detailed_result = {
                'test_case': i,
                'description': test_case['description'],
                'expected_match': expected_match,
                'advanced': {
                    'confidence': advanced_result.confidence,
                    'match': advanced_match,
                    'match_type': advanced_result.match_type,
                    'time': advanced_time,
                    'details': advanced_result.details
                },
                'optimized': {
                    'confidence': optimized_result.confidence,
                    'match': optimized_match,
                    'match_type': optimized_result.match_type,
                    'time': optimized_time,
                    'details': optimized_result.details,
                    'progressive_scores': optimized_result.progressive_scores
                },
                'improvement': improvement
            }
            
            results['detailed_results'].append(detailed_result)
        
        return results
    
    def print_summary(self, results: Dict[str, Any]) -> None:
        """Print comprehensive comparison summary"""
        
        print("\n" + "=" * 80)
        print("📊 PRODUCT MATCHER COMPARISON SUMMARY")
        print("=" * 80)
        
        total_cases = results['test_cases']
        expected_matches = sum(1 for case in self.test_cases if case['expected_match'])
        expected_non_matches = total_cases - expected_matches
        
        print(f"\n🧪 Test Dataset:")
        print(f"   Total test cases: {total_cases}")
        print(f"   Expected matches: {expected_matches}")
        print(f"   Expected non-matches: {expected_non_matches}")
        
        # Calculate metrics for both matchers
        for matcher_name in ['advanced_matcher', 'optimized_matcher']:
            data = results[matcher_name]
            
            # Calculate metrics
            precision = data['correct_matches'] / data['matches_found'] if data['matches_found'] > 0 else 0
            recall = data['correct_matches'] / expected_matches if expected_matches > 0 else 0
            f1_score = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0
            accuracy = (data['correct_matches'] + (expected_non_matches - data['false_positives'])) / total_cases
            
            avg_confidence = sum(data['confidence_scores']) / len(data['confidence_scores'])
            avg_time = data['total_time'] / total_cases
            
            print(f"\n{'📊 ADVANCED MATCHER' if 'advanced' in matcher_name else '🚀 OPTIMIZED MATCHER'}")
            print(f"   Matches Found: {data['matches_found']}/{total_cases}")
            print(f"   Correct Matches: {data['correct_matches']}/{expected_matches}")
            print(f"   False Positives: {data['false_positives']}")
            print(f"   False Negatives: {data['false_negatives']}")
            print(f"   Precision: {precision:.3f}")
            print(f"   Recall: {recall:.3f}")
            print(f"   F1 Score: {f1_score:.3f}")
            print(f"   Accuracy: {accuracy:.3f}")
            print(f"   Avg Confidence: {avg_confidence:.3f}")
            print(f"   Avg Time: {avg_time:.4f}s")
        
        # Calculate improvements
        advanced_data = results['advanced_matcher']
        optimized_data = results['optimized_matcher']
        
        recall_improvement = (optimized_data['correct_matches'] / expected_matches) - (advanced_data['correct_matches'] / expected_matches)
        confidence_improvement = (sum(optimized_data['confidence_scores']) / len(optimized_data['confidence_scores'])) - (sum(advanced_data['confidence_scores']) / len(advanced_data['confidence_scores']))
        speed_improvement = advanced_data['total_time'] / optimized_data['total_time'] if optimized_data['total_time'] > 0 else 1.0
        
        print(f"\n🎯 IMPROVEMENTS:")
        print(f"   Recall Improvement: {recall_improvement:+.3f} ({recall_improvement*100:+.1f}%)")
        print(f"   Avg Confidence Improvement: {confidence_improvement:+.3f} ({confidence_improvement*100:+.1f}%)")
        print(f"   Speed Factor: {speed_improvement:.2f}x")
        
        # Matching rate comparison
        advanced_matching_rate = advanced_data['matches_found'] / total_cases
        optimized_matching_rate = optimized_data['matches_found'] / total_cases
        matching_rate_improvement = optimized_matching_rate - advanced_matching_rate
        
        print(f"\n📈 MATCHING RATES:")
        print(f"   Advanced Matcher: {advanced_matching_rate:.1%} ({advanced_data['matches_found']}/{total_cases})")
        print(f"   Optimized Matcher: {optimized_matching_rate:.1%} ({optimized_data['matches_found']}/{total_cases})")
        print(f"   Improvement: {matching_rate_improvement:+.1%}")
        
        # Confidence distribution
        print(f"\n📊 CONFIDENCE DISTRIBUTIONS:")
        
        def get_confidence_stats(scores):
            high_conf = sum(1 for s in scores if s >= 0.8)
            med_conf = sum(1 for s in scores if 0.5 <= s < 0.8)
            low_conf = sum(1 for s in scores if 0.2 <= s < 0.5)
            very_low = sum(1 for s in scores if s < 0.2)
            return high_conf, med_conf, low_conf, very_low
        
        adv_high, adv_med, adv_low, adv_very_low = get_confidence_stats(advanced_data['confidence_scores'])
        opt_high, opt_med, opt_low, opt_very_low = get_confidence_stats(optimized_data['confidence_scores'])
        
        print(f"   Advanced Matcher:  High(≥0.8): {adv_high}, Med(0.5-0.8): {adv_med}, Low(0.2-0.5): {adv_low}, Very Low(<0.2): {adv_very_low}")
        print(f"   Optimized Matcher: High(≥0.8): {opt_high}, Med(0.5-0.8): {opt_med}, Low(0.2-0.5): {opt_low}, Very Low(<0.2): {opt_very_low}")
        
        # Key improvements summary
        print(f"\n🔑 KEY IMPROVEMENTS:")
        print(f"   ✅ Relaxed thresholds from 0.70 to 0.35 for low confidence matches")
        print(f"   ✅ Progressive matching with 4 tiers (strict, moderate, relaxed, fuzzy)")
        print(f"   ✅ Enhanced phonetic matching for Thai-English products")
        print(f"   ✅ Improved brand mapping with {len(self.optimized_matcher.enhanced_brand_mapping)} variations")
        print(f"   ✅ Reduced penalty factors for price variance and category mismatches")
        print(f"   ✅ Multiple similarity algorithms with weighted scoring")
        print(f"   ✅ Better handling of missing specifications")
        print(f"   ✅ Confidence boosting for high-quality matches")
        
        if matching_rate_improvement > 0:
            print(f"\n🎉 SUCCESS: Optimized matcher achieved {matching_rate_improvement:.1%} higher matching rate!")
        else:
            print(f"\n⚠️  Note: Matching rate decreased by {-matching_rate_improvement:.1%}, but this may indicate better precision")
    
    def save_results(self, results: Dict[str, Any], filename: str = 'matcher_comparison_results.json') -> None:
        """Save detailed results to JSON file"""
        
        # Convert dataclass objects to dicts for JSON serialization
        serializable_results = {
            'test_cases': results['test_cases'],
            'advanced_matcher': results['advanced_matcher'],
            'optimized_matcher': results['optimized_matcher'],
            'detailed_results': []
        }
        
        for detailed_result in results['detailed_results']:
            serializable_detailed = detailed_result.copy()
            # Simplify complex objects for JSON
            if 'details' in serializable_detailed['advanced']:
                serializable_detailed['advanced']['details'] = str(serializable_detailed['advanced']['details'])
            if 'details' in serializable_detailed['optimized']:
                serializable_detailed['optimized']['details'] = str(serializable_detailed['optimized']['details'])
            
            serializable_results['detailed_results'].append(serializable_detailed)
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(serializable_results, f, indent=2, ensure_ascii=False)
        
        print(f"\n💾 Results saved to {filename}")

def main():
    """Main function to run the comparison"""
    comparison = MatcherComparison()
    
    print("🚀 Starting Product Matcher Optimization Comparison")
    print("This will compare the original Advanced Matcher vs the new Optimized Matcher")
    print("Focus: Improving matching rates while maintaining accuracy\n")
    
    # Run the comparison
    results = comparison.run_comparison()
    
    # Print summary
    comparison.print_summary(results)
    
    # Save results
    comparison.save_results(results)
    
    print(f"\n✅ Comparison completed! Check the detailed results above.")
    print("The optimized matcher should show significantly improved matching rates.")

if __name__ == "__main__":
    main()