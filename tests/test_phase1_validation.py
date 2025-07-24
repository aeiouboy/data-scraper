"""
Phase 1 Implementation Validation Tests
Validates all components of the matching accuracy improvement plan Phase 1
"""

import unittest
from unittest.mock import Mock, patch
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.utils.text_normalizer_enhanced import EnhancedTextNormalizer
from src.utils.brand_alias_manager import BrandAliasManager
from src.utils.sku_extractor import SkuExtractor
from src.utils.confidence_calculator import ConfidenceCalculator
from src.services.advanced_product_matcher import AdvancedProductMatcher
from src.config.text_normalization_config import DEFAULT_CONFIG


class TestPhase1Implementation(unittest.TestCase):
    """Test suite for Phase 1 implementation validation"""
    
    def setUp(self):
        """Set up test components"""
        self.text_normalizer = EnhancedTextNormalizer()
        self.brand_manager = BrandAliasManager()
        self.sku_extractor = SkuExtractor()
        self.confidence_calculator = ConfidenceCalculator()
        self.advanced_matcher = AdvancedProductMatcher()
    
    def test_enhanced_text_normalization(self):
        """Test enhanced text normalization with Thai language support"""
        # Test Thai to English brand mapping
        thai_text = "มิตซูบิชิ เครื่องปรับอากาศ MSY-KP13VF 12,000 บีทียู"
        normalized = self.text_normalizer.normalize(thai_text)
        
        # Should convert Thai brand to English
        self.assertIn('mitsubishi', normalized.lower())
        self.assertIn('air conditioner', normalized.lower())
        
        # Test specification extraction
        specs = self.text_normalizer.extract_specifications(thai_text)
        self.assertIn('capacity_btu', specs)
        self.assertEqual(specs['capacity_btu'], '12000')
        
        # Test SKU extraction
        sku = self.text_normalizer.extract_sku(thai_text)
        self.assertEqual(sku, 'MSY-KP13VF')
        
        print("✓ Enhanced text normalization working correctly")
    
    def test_brand_alias_management(self):
        """Test brand alias mapping system"""
        # Test brand normalization
        thai_brand = "มิตซูบิชิ"
        english_brand = "MITSUBISHI"
        
        norm_thai = self.brand_manager.normalize_brand(thai_brand)
        norm_english = self.brand_manager.normalize_brand(english_brand)
        
        # Should normalize to the same canonical form
        self.assertEqual(norm_thai, norm_english.lower())
        
        # Test alias checking
        self.assertTrue(self.brand_manager.are_aliases(thai_brand, english_brand))
        
        # Test brand finding in text
        text = "MITSUBISHI แอร์ รุ่น MSY-KP13VF"
        found_brands = self.brand_manager.find_brand_in_text(text)
        self.assertGreater(len(found_brands), 0)
        
        print("✓ Brand alias management working correctly")
    
    def test_sku_extraction(self):
        """Test standardized SKU/model number extraction"""
        test_cases = [
            ("MITSUBISHI แอร์ รุ่น MSY-KP13VF 12000BTU", "MSY-KP13VF"),
            ("Samsung ตู้เย็น RT29K5511S8 300 ลิตร", "RT29K5511S8"),
            ("LG Smart TV 55 นิ้ว รุ่น 55UN7300PTC", "55UN7300PTC"),
            ("Panasonic เครื่องซักผ้า NA-F70B3", "NA-F70B3")
        ]
        
        for text, expected_sku in test_cases:
            result = self.sku_extractor.extract_sku(text)
            self.assertIsNotNone(result, f"Failed to extract SKU from: {text}")
            self.assertEqual(result.sku, expected_sku, f"Wrong SKU extracted from: {text}")
        
        # Test SKU comparison
        self.assertTrue(self.sku_extractor.compare_skus("MSY-KP13VF", "MSYKP13VF"))
        self.assertTrue(self.sku_extractor.compare_skus("RT29K5511S8", "RT29K5511S8-ST"))
        self.assertFalse(self.sku_extractor.compare_skus("MSY-KP13VF", "RT29K5511S8"))
        
        print("✓ SKU extraction working correctly")
    
    def test_confidence_scoring(self):
        """Test enhanced confidence scoring with weighted factors"""
        product1 = {
            'name': 'MITSUBISHI แอร์ติดผนัง รุ่น MSY-KP13VF 12000BTU',
            'brand': 'MITSUBISHI',
            'sku': 'MSY-KP13VF',
            'price': 15000,
            'category': 'air-conditioner',
            'specifications': {'capacity_btu': 12000}
        }
        
        product2 = {
            'name': 'มิตซูบิชิ เครื่องปรับอากาศ MSY-KP13VF 12,000 บีทียู',
            'brand': 'มิตซูบิชิ',
            'sku': 'MSY-KP13VF',
            'price': 15500,
            'category': 'air-conditioner',
            'specifications': {'capacity_btu': 12000}
        }
        
        result = self.confidence_calculator.calculate_confidence(product1, product2)
        
        # Should have reasonable confidence for similar products
        self.assertGreater(result.overall_confidence, 0.0)
        self.assertIsInstance(result.factors, list)
        self.assertGreater(len(result.factors), 0)
        
        # Check that all expected factors are present
        factor_names = [f.name for f in result.factors]
        expected_factors = ['name_similarity', 'brand_match', 'sku_match', 'spec_match', 'price_match']
        for expected in expected_factors:
            self.assertIn(expected, factor_names)
        
        print("✓ Confidence scoring working correctly")
    
    def test_integrated_advanced_matcher(self):
        """Test integrated advanced product matcher"""
        product1 = {
            'id': 1,
            'name': 'MITSUBISHI แอร์ติดผนัง รุ่น MSY-KP13VF 12000BTU',
            'brand': 'MITSUBISHI',
            'price': 15000,
            'category': 'air-conditioner',
            'retailer': 'homepro'
        }
        
        product2 = {
            'id': 2,
            'name': 'มิตซูบิชิ เครื่องปรับอากาศ MSY-KP13VF 12,000 บีทียู',
            'brand': 'มิตซูบิชิ',
            'price': 15500,
            'category': 'air-conditioner',
            'retailer': 'thaiwatsadu'
        }
        
        result = self.advanced_matcher.match_products(product1, product2)
        
        # Check result structure
        self.assertIsNotNone(result)
        self.assertIsInstance(result.confidence, float)
        self.assertIn(result.match_quality, ['excellent', 'very_good', 'good', 'fair', 'poor', 'very_poor', 'error'])
        self.assertGreater(result.processing_time, 0)
        
        # Check product enrichment
        self.assertIn('normalized_name', result.product1)
        self.assertIn('normalized_brand', result.product1)
        
        print("✓ Integrated advanced matcher working correctly")
    
    def test_configuration_system(self):
        """Test configurable system components"""
        # Test that configuration is loaded
        self.assertIsNotNone(DEFAULT_CONFIG)
        self.assertIn('brand_mappings', DEFAULT_CONFIG)
        self.assertIn('thresholds', DEFAULT_CONFIG)
        
        # Test configuration validation
        issues = self.advanced_matcher.validate_configuration()
        self.assertIsInstance(issues, list)
        # Configuration should be valid with no issues
        self.assertEqual(len(issues), 0)
        
        print("✓ Configuration system working correctly")
    
    def test_performance_and_caching(self):
        """Test performance optimizations and caching"""
        # Test caching in text normalizer
        text = "MITSUBISHI แอร์ติดผนัง รุ่น MSY-KP13VF 12000BTU"
        
        # First normalization
        norm1 = self.text_normalizer.normalize(text)
        
        # Second normalization (should use cache)
        norm2 = self.text_normalizer.normalize(text)
        
        self.assertEqual(norm1, norm2)
        
        # Check cache stats
        stats = self.text_normalizer.get_cache_stats()
        self.assertIsInstance(stats, dict)
        self.assertIn('sku_cache_size', stats)
        self.assertIn('spec_cache_size', stats)
        
        print("✓ Performance and caching working correctly")
    
    def test_error_handling(self):
        """Test error handling and edge cases"""
        # Test with empty/None inputs
        result = self.advanced_matcher.match_products({}, {})
        self.assertIsNotNone(result)
        self.assertEqual(result.confidence, 0.0)
        
        # Test with malformed products
        malformed_product = {'name': None, 'brand': '', 'price': 'invalid'}
        normal_product = {'name': 'Test Product', 'brand': 'Test', 'price': 100}
        
        result = self.advanced_matcher.match_products(malformed_product, normal_product)
        self.assertIsNotNone(result)
        
        print("✓ Error handling working correctly")
    
    def test_batch_processing(self):
        """Test batch processing capabilities"""
        products = [
            {'id': 1, 'name': 'Product 1', 'brand': 'Brand A'},
            {'id': 2, 'name': 'Product 2', 'brand': 'Brand B'},
            {'id': 3, 'name': 'Product 3', 'brand': 'Brand A'},
        ]
        
        # Test batch matching
        pairs = [(products[0], products[1]), (products[0], products[2])]
        results = self.advanced_matcher.batch_match_products(pairs)
        
        self.assertEqual(len(results), 2)
        for result in results:
            self.assertIsInstance(result.confidence, float)
        
        # Test matching against list
        list_results = self.advanced_matcher.match_product_against_list(
            products[0], products[1:], top_k=2
        )
        
        self.assertLessEqual(len(list_results), 2)
        
        print("✓ Batch processing working correctly")
    
    def test_statistics_and_monitoring(self):
        """Test statistics collection and monitoring"""
        # Run some matches to generate stats
        product1 = {'name': 'Test Product 1', 'brand': 'Test Brand'}
        product2 = {'name': 'Test Product 2', 'brand': 'Test Brand'}
        
        self.advanced_matcher.match_products(product1, product2)
        
        # Check statistics
        stats = self.advanced_matcher.get_statistics()
        
        self.assertIsInstance(stats, dict)
        self.assertIn('total_matches', stats)
        self.assertIn('successful_matches', stats)
        self.assertIn('success_rate', stats)
        self.assertIn('component_stats', stats)
        
        self.assertGreater(stats['total_matches'], 0)
        
        print("✓ Statistics and monitoring working correctly")


def run_phase1_validation():
    """Run complete Phase 1 validation suite"""
    print("Phase 1 Implementation Validation")
    print("=" * 50)
    
    # Create test suite
    suite = unittest.TestLoader().loadTestsFromTestCase(TestPhase1Implementation)
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Summary
    print("\n" + "=" * 50)
    print("PHASE 1 VALIDATION SUMMARY")
    print("=" * 50)
    
    if result.wasSuccessful():
        print("✅ ALL TESTS PASSED")
        print("✅ Phase 1 implementation is COMPLETE and VALIDATED")
        print("\nImplemented Components:")
        print("- ✅ Enhanced Thai text normalization")
        print("- ✅ Brand alias mapping system")
        print("- ✅ Standardized SKU/model extraction")
        print("- ✅ Multi-factor confidence scoring")
        print("- ✅ Integrated advanced product matcher")
        print("- ✅ Configurable system architecture")
        print("- ✅ Performance optimization with caching")
        print("- ✅ Error handling and edge cases")
        print("- ✅ Batch processing capabilities")
        print("- ✅ Statistics and monitoring")
        
        print("\nNext Steps:")
        print("- Ready to proceed to Phase 2 (ML Integration)")
        print("- Consider fine-tuning confidence thresholds")
        print("- Expand brand alias database")
        print("- Add more SKU patterns for specific retailers")
        
    else:
        print("❌ SOME TESTS FAILED")
        print("❌ Phase 1 implementation needs attention")
        print(f"\nFailures: {len(result.failures)}")
        print(f"Errors: {len(result.errors)}")
        
        for test, error in result.failures + result.errors:
            print(f"- {test}: {error}")
    
    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_phase1_validation()
    exit(0 if success else 1)