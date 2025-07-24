#!/usr/bin/env python3
"""
Comprehensive Integration Tests for Phase 2 ML Components
Tests all ML matching components together to ensure they work correctly
"""

import sys
import os
import pytest
import time
import json
from pathlib import Path

# Add src to path for imports
project_root = os.path.dirname(os.path.dirname(__file__))
sys.path.insert(0, project_root)
sys.path.insert(0, os.path.join(project_root, 'src'))

# Import all Phase 2 components
try:
    from src.utils.fuzzy_matcher import FuzzyMatcher, FuzzyMatchResult
    from src.utils.semantic_similarity import SemanticSimilarity, SemanticResult
    from src.utils.training_dataset_generator import TrainingDatasetGenerator, TrainingExample
    from src.services.validation_pipeline import ValidationPipeline, ValidationResult
    from src.services.advanced_product_matcher import AdvancedProductMatcher
except ImportError as e:
    print(f"Import error: {e}")
    print("Trying alternative import paths...")
    from utils.fuzzy_matcher import FuzzyMatcher, FuzzyMatchResult
    from utils.semantic_similarity import SemanticSimilarity, SemanticResult
    from utils.training_dataset_generator import TrainingDatasetGenerator, TrainingExample
    from services.validation_pipeline import ValidationPipeline, ValidationResult
    from services.advanced_product_matcher import AdvancedProductMatcher

# Mock data for testing
MOCK_PRODUCTS = [
    {
        'id': 'test_001',
        'name': 'MITSUBISHI แอร์ติดผนัง รุ่น MSY-KP13VF 12000BTU',
        'brand': 'Mitsubishi',
        'category': 'Air Conditioner',
        'specifications': {'capacity': '12000BTU', 'type': 'Split'},
        'price': 25000
    },
    {
        'id': 'test_002', 
        'name': 'มิตซูบิชิ เครื่องปรับอากาศ MSY-KP13VF 12000 บีทียู',
        'brand': 'Mitsubishi',
        'category': 'Air Conditioner',
        'specifications': {'capacity': '12000BTU', 'type': 'Split'},
        'price': 25500
    },
    {
        'id': 'test_003',
        'name': 'Samsung ตู้เย็น RT29K5511S8 300L',
        'brand': 'Samsung', 
        'category': 'Refrigerator',
        'specifications': {'capacity': '300L', 'doors': '2'},
        'price': 15000
    },
    {
        'id': 'test_004',
        'name': 'ซัมซุง ตู้เย็น RT29K5511S8 300 ลิตร',
        'brand': 'Samsung',
        'category': 'Refrigerator', 
        'specifications': {'capacity': '300L', 'doors': '2'},
        'price': 15200
    },
    {
        'id': 'test_005',
        'name': 'LG Smart TV 55 นิ้ว รุ่น 55UN7300PTC',
        'brand': 'LG',
        'category': 'Television',
        'specifications': {'size': '55 inch', 'type': 'Smart TV'},
        'price': 18000
    }
]

def test_fuzzy_matcher_basic():
    """Test basic fuzzy matching functionality"""
    print("\n=== Testing Fuzzy Matcher ===")
    
    matcher = FuzzyMatcher()
    
    # Test Thai-English matching
    result = matcher.calculate_similarity(
        "MITSUBISHI แอร์ติดผนัง รุ่น MSY-KP13VF",
        "มิตซูบิชิ เครื่องปรับอากาศ MSY-KP13VF"
    )
    
    print(f"Thai-English fuzzy match:")
    print(f"  Similarity: {result.similarity:.3f}")
    print(f"  Confidence: {result.confidence:.3f}")
    print(f"  Method: {result.method}")
    
    # Verify result structure
    assert isinstance(result, FuzzyMatchResult)
    assert 0 <= result.similarity <= 1
    assert 0 <= result.confidence <= 1
    assert result.method == 'weighted_ensemble'
    assert 'individual_scores' in result.details
    
    # Test high similarity for similar products
    assert result.similarity > 0.7, f"Expected high similarity, got {result.similarity:.3f}"
    
    print("✅ Fuzzy matcher basic test passed")

def test_fuzzy_matcher_algorithms():
    """Test individual fuzzy matching algorithms"""
    print("\n=== Testing Individual Fuzzy Algorithms ===")
    
    matcher = FuzzyMatcher()
    
    text1 = "Samsung Smart TV 55 inch"
    text2 = "ซัมซุง สมาร์ททีวี 55 นิ้ว"
    
    # Test specific algorithms
    algorithms = ['levenshtein', 'jaro_winkler', 'cosine', 'jaccard']
    
    for algorithm in algorithms:
        result = matcher.calculate_similarity(text1, text2, methods=[algorithm])
        print(f"  {algorithm}: {result.similarity:.3f}")
        
        assert 0 <= result.similarity <= 1
        assert algorithm in result.details['individual_scores']
    
    print("✅ Individual fuzzy algorithms test passed")

def test_semantic_similarity_basic():
    """Test basic semantic similarity functionality"""
    print("\n=== Testing Semantic Similarity ===")
    
    semantic = SemanticSimilarity()
    
    # Test without training (lightweight mode)
    result = semantic.calculate_similarity(
        "Samsung Smart TV 55 นิ้ว",
        "ซัมซุง สมาร์ททีวี 55 inch"
    )
    
    print(f"Semantic similarity (lightweight):")
    print(f"  Similarity: {result.similarity:.3f}")
    print(f"  Method: {result.method}")
    print(f"  Features count: {len(result.features)}")
    
    # Verify result structure
    assert isinstance(result, SemanticResult)
    assert 0 <= result.similarity <= 1
    assert result.method == 'lightweight_token_overlap'
    assert isinstance(result.features, dict)
    
    print("✅ Semantic similarity basic test passed")

def test_semantic_similarity_trained():
    """Test semantic similarity with training"""
    print("\n=== Testing Trained Semantic Similarity ===")
    
    semantic = SemanticSimilarity()
    
    # Create training corpus
    training_corpus = [p['name'] for p in MOCK_PRODUCTS] * 5  # Duplicate for better training
    
    # Train the model
    print("Training semantic models...")
    semantic.train(training_corpus)
    
    # Test similarity after training
    result = semantic.calculate_similarity(
        "MITSUBISHI แอร์ติดผนัง รุ่น MSY-KP13VF",
        "มิตซูบิชิ เครื่องปรับอากาศ MSY-KP13VF"
    )
    
    print(f"Trained semantic similarity:")
    print(f"  Similarity: {result.similarity:.3f}")
    print(f"  Method: {result.method}")
    
    # Verify trained model results
    assert result.method == 'weighted_semantic'
    assert 'individual_similarities' in result.details
    assert semantic.is_trained == True
    
    # Test model persistence
    model_path = "/tmp/test_semantic_model.pkl"
    semantic.save_models(model_path)
    
    # Load in new instance
    semantic2 = SemanticSimilarity()
    semantic2.load_models(model_path)
    
    assert semantic2.is_trained == True
    
    # Clean up
    Path(model_path).unlink(missing_ok=True)
    
    print("✅ Trained semantic similarity test passed")

def test_training_dataset_generator():
    """Test training dataset generation"""
    print("\n=== Testing Training Dataset Generator ===")
    
    # Mock database client for testing
    class MockSupabaseClient:
        def __init__(self):
            self.client = self
            
        def table(self, table_name):
            return self
            
        def select(self, columns):
            return self
            
        def eq(self, column, value):
            return self
            
        def gte(self, column, value):
            return self
            
        def limit(self, count):
            return self
            
        def execute(self):
            # Return mock data based on what's expected
            mock_data = {
                'data': [
                    {
                        'product1_id': 'test_001',
                        'product2_id': 'test_002', 
                        'confidence': 0.9,
                        'is_verified': True,
                        'match_status': 'match'
                    }
                ]
            }
            return type('MockResponse', (), mock_data)()
    
    # Create generator with mock client
    generator = TrainingDatasetGenerator(MockSupabaseClient())
    
    # Test feature extraction
    features = generator._extract_fuzzy_features(MOCK_PRODUCTS[0], MOCK_PRODUCTS[1])
    
    print(f"Fuzzy features extracted: {len(features)}")
    print(f"  Sample features: {list(features.keys())[:3]}")
    
    assert isinstance(features, dict)
    assert len(features) > 0
    
    # Test semantic features
    semantic_features = generator._extract_semantic_features(MOCK_PRODUCTS[0], MOCK_PRODUCTS[1])
    
    print(f"Semantic features extracted: {len(semantic_features)}")
    
    assert isinstance(semantic_features, dict)
    assert len(semantic_features) > 0
    
    print("✅ Training dataset generator test passed")

def test_advanced_product_matcher():
    """Test the integrated advanced product matcher"""
    print("\n=== Testing Advanced Product Matcher ===")
    
    matcher = AdvancedProductMatcher()
    
    # Test matching between similar products
    result = matcher.match_products(MOCK_PRODUCTS[0], MOCK_PRODUCTS[1])
    
    print(f"Advanced matching result:")
    print(f"  Confidence: {result.confidence:.3f}")
    print(f"  Match factors: {list(result.details.keys())}")
    
    # Verify result structure
    assert hasattr(result, 'confidence')
    assert hasattr(result, 'details')
    assert 0 <= result.confidence <= 1
    
    # Test with different categories (should have lower confidence)
    different_result = matcher.match_products(MOCK_PRODUCTS[0], MOCK_PRODUCTS[2])
    
    print(f"Different category match confidence: {different_result.confidence:.3f}")
    
    # Different categories should have lower confidence
    assert different_result.confidence < result.confidence
    
    print("✅ Advanced product matcher test passed")

def test_validation_pipeline():
    """Test the validation pipeline"""
    print("\n=== Testing Validation Pipeline ===")
    
    # Mock database for validation pipeline
    class MockValidationClient:
        def __init__(self):
            self.client = self
            
        def table(self, table_name):
            return self
            
        def select(self, columns):
            return self
            
        def eq(self, column, value):
            return self
            
        def gte(self, column, value):
            return self
            
        def limit(self, count):
            return self
            
        def insert(self, data):
            return self
            
        def order(self, column, **kwargs):
            return self
            
        def execute(self):
            # Return empty data to trigger synthetic generation
            return type('MockResponse', (), {'data': []})()
    
    # Create pipeline with mock client
    pipeline = ValidationPipeline(MockValidationClient())
    
    # Run validation with small sample
    print("Running validation test...")
    result = pipeline.run_validation(sample_size=10, validation_type='comprehensive')
    
    print(f"Validation results:")
    print(f"  Accuracy: {result.accuracy:.3f}")
    print(f"  Precision: {result.precision:.3f}")
    print(f"  Recall: {result.recall:.3f}")
    print(f"  F1 Score: {result.f1_score:.3f}")
    print(f"  Sample size: {result.sample_size}")
    
    # Verify result structure
    assert isinstance(result, ValidationResult)
    assert 0 <= result.accuracy <= 1
    assert 0 <= result.precision <= 1
    assert 0 <= result.recall <= 1
    assert 0 <= result.f1_score <= 1
    assert result.sample_size > 0
    assert isinstance(result.recommendations, list)
    
    print("✅ Validation pipeline test passed")

def test_end_to_end_integration():
    """Test complete end-to-end integration"""
    print("\n=== Testing End-to-End Integration ===")
    
    # Test complete workflow
    print("1. Testing fuzzy matching...")
    fuzzy_matcher = FuzzyMatcher()
    fuzzy_result = fuzzy_matcher.calculate_similarity(
        MOCK_PRODUCTS[0]['name'], 
        MOCK_PRODUCTS[1]['name']
    )
    
    print("2. Testing semantic similarity...")
    semantic = SemanticSimilarity()
    semantic_result = semantic.calculate_similarity(
        MOCK_PRODUCTS[0]['name'], 
        MOCK_PRODUCTS[1]['name']
    )
    
    print("3. Testing advanced matching...")
    advanced_matcher = AdvancedProductMatcher()
    advanced_result = advanced_matcher.match_products(
        MOCK_PRODUCTS[0], 
        MOCK_PRODUCTS[1]
    )
    
    print("4. Testing training data generation...")
    generator = TrainingDatasetGenerator()
    basic_features = generator._extract_basic_features(
        MOCK_PRODUCTS[0], 
        MOCK_PRODUCTS[1]
    )
    
    print(f"End-to-end results:")
    print(f"  Fuzzy similarity: {fuzzy_result.similarity:.3f}")
    print(f"  Semantic similarity: {semantic_result.similarity:.3f}")
    print(f"  Advanced confidence: {advanced_result.confidence:.3f}")
    print(f"  Training features: {len(basic_features)}")
    
    # Verify all components work together
    assert fuzzy_result.similarity > 0
    assert semantic_result.similarity > 0
    assert advanced_result.confidence > 0
    assert len(basic_features) > 0
    
    print("✅ End-to-end integration test passed")

def test_performance_benchmarks():
    """Test performance of all components"""
    print("\n=== Testing Performance Benchmarks ===")
    
    # Performance targets
    targets = {
        'fuzzy_matching': 0.1,  # seconds per match
        'semantic_similarity': 0.05,  # seconds per match
        'advanced_matching': 0.2,  # seconds per match
    }
    
    # Test fuzzy matching performance
    fuzzy_matcher = FuzzyMatcher()
    start_time = time.time()
    for i in range(10):
        fuzzy_matcher.calculate_similarity(
            MOCK_PRODUCTS[0]['name'], 
            MOCK_PRODUCTS[1]['name']
        )
    fuzzy_time = (time.time() - start_time) / 10
    
    # Test semantic similarity performance
    semantic = SemanticSimilarity()
    start_time = time.time()
    for i in range(10):
        semantic.calculate_similarity(
            MOCK_PRODUCTS[0]['name'], 
            MOCK_PRODUCTS[1]['name']
        )
    semantic_time = (time.time() - start_time) / 10
    
    # Test advanced matching performance
    advanced_matcher = AdvancedProductMatcher()
    start_time = time.time()
    for i in range(10):
        advanced_matcher.match_products(
            MOCK_PRODUCTS[0], 
            MOCK_PRODUCTS[1]
        )
    advanced_time = (time.time() - start_time) / 10
    
    print(f"Performance results:")
    print(f"  Fuzzy matching: {fuzzy_time:.4f}s (target: {targets['fuzzy_matching']:.3f}s)")
    print(f"  Semantic similarity: {semantic_time:.4f}s (target: {targets['semantic_similarity']:.3f}s)")
    print(f"  Advanced matching: {advanced_time:.4f}s (target: {targets['advanced_matching']:.3f}s)")
    
    # Check if performance meets targets
    performance_ok = True
    if fuzzy_time > targets['fuzzy_matching']:
        print(f"  ⚠️  Fuzzy matching slower than target")
        performance_ok = False
    if semantic_time > targets['semantic_similarity']:
        print(f"  ⚠️  Semantic similarity slower than target")
        performance_ok = False
    if advanced_time > targets['advanced_matching']:
        print(f"  ⚠️  Advanced matching slower than target")
        performance_ok = False
    
    if performance_ok:
        print("✅ All performance benchmarks met")
    else:
        print("⚠️  Some performance targets not met - consider optimization")

def run_all_tests():
    """Run all Phase 2 integration tests"""
    print("🧪 Starting Phase 2 ML Integration Tests")
    print("=" * 60)
    
    test_functions = [
        test_fuzzy_matcher_basic,
        test_fuzzy_matcher_algorithms,
        test_semantic_similarity_basic,
        test_semantic_similarity_trained,
        test_training_dataset_generator,
        test_advanced_product_matcher,
        test_validation_pipeline,
        test_end_to_end_integration,
        test_performance_benchmarks
    ]
    
    passed = 0
    failed = 0
    
    for test_func in test_functions:
        try:
            test_func()
            passed += 1
        except Exception as e:
            print(f"❌ {test_func.__name__} FAILED: {e}")
            failed += 1
    
    print("\n" + "=" * 60)
    print(f"🧪 Phase 2 Test Results: {passed} passed, {failed} failed")
    
    if failed == 0:
        print("🎉 All Phase 2 components working correctly!")
        print("✅ Ready to proceed to Phase 3: Performance Optimization")
    else:
        print("⚠️  Some tests failed - please review and fix before proceeding")
    
    return failed == 0

if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)