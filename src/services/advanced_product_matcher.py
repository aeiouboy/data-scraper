"""
Advanced Product Matcher
Integrates all Phase 1 improvements for enhanced product matching accuracy
"""

import logging
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
import time

from src.utils.text_normalizer_enhanced import EnhancedTextNormalizer
from src.utils.brand_alias_manager import BrandAliasManager
from src.utils.sku_extractor import SkuExtractor
from src.utils.confidence_calculator import ConfidenceCalculator, ConfidenceResult
from src.config.text_normalization_config import DEFAULT_CONFIG

logger = logging.getLogger(__name__)


@dataclass
class ProductMatchResult:
    """Result of product matching with detailed information"""
    product1: Dict
    product2: Dict
    confidence: float
    confidence_result: ConfidenceResult
    match_quality: str
    processing_time: float
    metadata: Dict[str, Any]


class AdvancedProductMatcher:
    """
    Advanced product matching system integrating all Phase 1 improvements:
    - Enhanced Thai text normalization
    - Brand alias management
    - Advanced SKU extraction
    - Multi-factor confidence scoring
    """
    
    def __init__(self, config: Optional[Dict] = None):
        """Initialize advanced product matcher with configuration"""
        self.config = config or DEFAULT_CONFIG
        
        # Initialize components
        self.text_normalizer = EnhancedTextNormalizer(self.config)
        self.brand_manager = BrandAliasManager()
        self.sku_extractor = SkuExtractor()
        self.confidence_calculator = ConfidenceCalculator(self.config)
        
        # Matching statistics
        self.stats = {
            'total_matches': 0,
            'successful_matches': 0,
            'processing_time': 0.0,
            'error_count': 0
        }
        
        logger.info("Advanced Product Matcher initialized")
    
    def match_products(self, product1: Dict, product2: Dict, 
                      context: Optional[Dict] = None) -> ProductMatchResult:
        """
        Match two products using advanced algorithms
        
        Args:
            product1: First product dictionary
            product2: Second product dictionary
            context: Optional context for matching
            
        Returns:
            ProductMatchResult with confidence and details
        """
        start_time = time.time()
        
        try:
            # Enrich products with extracted information
            enriched_product1 = self._enrich_product(product1)
            enriched_product2 = self._enrich_product(product2)
            
            # Calculate confidence using all factors
            confidence_result = self.confidence_calculator.calculate_confidence(
                enriched_product1, enriched_product2, context
            )
            
            # Determine match quality
            match_quality = self._determine_match_quality(confidence_result)
            
            # Calculate processing time
            processing_time = time.time() - start_time
            
            # Update statistics
            self._update_stats(confidence_result.overall_confidence, processing_time)
            
            # Create result
            result = ProductMatchResult(
                product1=enriched_product1,
                product2=enriched_product2,
                confidence=confidence_result.overall_confidence,
                confidence_result=confidence_result,
                match_quality=match_quality,
                processing_time=processing_time,
                metadata={
                    'matcher_version': '1.0.0',
                    'config_version': self.config.get('version', '1.0'),
                    'timestamp': time.time()
                }
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Error matching products: {e}")
            self.stats['error_count'] += 1
            
            # Return error result
            return ProductMatchResult(
                product1=product1,
                product2=product2,
                confidence=0.0,
                confidence_result=None,
                match_quality='error',
                processing_time=time.time() - start_time,
                metadata={'error': str(e)}
            )
    
    def match_product_against_list(self, target_product: Dict, 
                                 product_list: List[Dict],
                                 context: Optional[Dict] = None,
                                 top_k: int = 10) -> List[ProductMatchResult]:
        """
        Match a product against a list of products
        
        Args:
            target_product: Product to match against
            product_list: List of products to search
            context: Optional context for matching
            top_k: Number of top matches to return
            
        Returns:
            List of ProductMatchResult sorted by confidence
        """
        results = []
        
        for product in product_list:
            try:
                result = self.match_products(target_product, product, context)
                results.append(result)
            except Exception as e:
                logger.warning(f"Error matching product {product.get('id', 'unknown')}: {e}")
                continue
        
        # Sort by confidence and return top k
        results.sort(key=lambda x: x.confidence, reverse=True)
        return results[:top_k]
    
    def batch_match_products(self, product_pairs: List[Tuple[Dict, Dict]],
                           context: Optional[Dict] = None) -> List[ProductMatchResult]:
        """
        Match multiple product pairs in batch
        
        Args:
            product_pairs: List of (product1, product2) tuples
            context: Optional context for matching
            
        Returns:
            List of ProductMatchResult for each pair
        """
        results = []
        
        for product1, product2 in product_pairs:
            try:
                result = self.match_products(product1, product2, context)
                results.append(result)
            except Exception as e:
                logger.warning(f"Error in batch matching: {e}")
                continue
        
        return results
    
    def _enrich_product(self, product: Dict) -> Dict:
        """
        Enrich product with extracted information
        
        Args:
            product: Product dictionary
            
        Returns:
            Enriched product dictionary
        """
        enriched = product.copy()
        
        # Extract and normalize product name
        name = product.get('name', '')
        if name:
            enriched['normalized_name'] = self.text_normalizer.normalize(name)
            enriched['name_tokens'] = enriched['normalized_name'].split()
        
        # Extract and normalize brand
        brand = product.get('brand', '')
        if brand:
            enriched['normalized_brand'] = self.brand_manager.normalize_brand(brand)
            enriched['brand_aliases'] = self.brand_manager.get_brand_aliases(brand)
        
        # Extract SKU/model number
        sku_match = self.sku_extractor.extract_sku(name)
        if sku_match:
            enriched['extracted_sku'] = sku_match.sku
            enriched['sku_confidence'] = sku_match.confidence
            enriched['sku_normalized'] = sku_match.normalized
        
        # Extract specifications
        specs = self.text_normalizer.extract_specifications(name)
        if specs:
            enriched['extracted_specifications'] = specs
            # Merge with existing specifications
            if 'specifications' in enriched:
                enriched['specifications'].update(specs)
            else:
                enriched['specifications'] = specs
        
        # Find brand in text
        brand_matches = self.brand_manager.find_brand_in_text(name)
        if brand_matches:
            enriched['detected_brands'] = brand_matches
            # Use highest confidence brand if no brand specified
            if not brand and brand_matches:
                enriched['inferred_brand'] = brand_matches[0][0]
        
        return enriched
    
    def _determine_match_quality(self, confidence_result: ConfidenceResult) -> str:
        """
        Determine match quality based on confidence result
        
        Args:
            confidence_result: ConfidenceResult object
            
        Returns:
            Match quality string
        """
        if not confidence_result:
            return 'error'
        
        confidence = confidence_result.overall_confidence
        
        if confidence >= 0.95:
            return 'excellent'
        elif confidence >= 0.85:
            return 'very_good'
        elif confidence >= 0.75:
            return 'good'
        elif confidence >= 0.65:
            return 'fair'
        elif confidence >= 0.50:
            return 'poor'
        else:
            return 'very_poor'
    
    def _update_stats(self, confidence: float, processing_time: float):
        """Update matching statistics"""
        self.stats['total_matches'] += 1
        self.stats['processing_time'] += processing_time
        
        if confidence >= self.config['thresholds']['min_confidence']:
            self.stats['successful_matches'] += 1
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get matching statistics"""
        stats = self.stats.copy()
        
        if stats['total_matches'] > 0:
            stats['success_rate'] = stats['successful_matches'] / stats['total_matches']
            stats['avg_processing_time'] = stats['processing_time'] / stats['total_matches']
        else:
            stats['success_rate'] = 0.0
            stats['avg_processing_time'] = 0.0
        
        # Add component statistics
        stats['component_stats'] = {
            'text_normalizer': self.text_normalizer.get_cache_stats(),
            'brand_manager': self.brand_manager.get_brand_statistics(),
            'sku_extractor': self.sku_extractor.get_pattern_statistics()
        }
        
        return stats
    
    def clear_caches(self):
        """Clear all component caches"""
        self.text_normalizer.clear_cache()
        logger.info("All caches cleared")
    
    def validate_configuration(self) -> List[str]:
        """Validate configuration and return issues"""
        issues = []
        
        # Validate text normalization config
        if not self.config.get('brand_mappings'):
            issues.append("No brand mappings configured")
        
        if not self.config.get('model_patterns'):
            issues.append("No model patterns configured")
        
        # Validate brand manager
        brand_issues = self.brand_manager.validate_brand_mappings()
        issues.extend(brand_issues)
        
        # Validate thresholds
        thresholds = self.config.get('thresholds', {})
        if thresholds.get('min_confidence', 0) < 0 or thresholds.get('min_confidence', 0) > 1:
            issues.append("Invalid minimum confidence threshold")
        
        return issues
    
    def export_configuration(self, file_path: str):
        """Export current configuration to file"""
        try:
            import json
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=2, ensure_ascii=False)
            logger.info(f"Configuration exported to {file_path}")
        except Exception as e:
            logger.error(f"Error exporting configuration: {e}")
    
    def optimize_for_retailer(self, retailer: str):
        """Optimize matching for specific retailer"""
        retailer_configs = {
            'homepro': {
                'sku_patterns': [
                    r'\b(HP[0-9]{6,8})\b',
                    r'\b([A-Z]{2,3}[-]?[0-9]{4,6}[-]?[A-Z]{0,2})\b'
                ],
                'confidence_adjustment': 0.05
            },
            'thaiwatsadu': {
                'sku_patterns': [
                    r'\b(TWD[0-9]{6,8})\b',
                    r'\b([A-Z]{3}[-]?[0-9]{3,4}[-]?[A-Z]{1,2})\b'
                ],
                'confidence_adjustment': 0.05
            }
        }
        
        if retailer in retailer_configs:
            config = retailer_configs[retailer]
            
            # Add retailer-specific SKU patterns
            for pattern in config['sku_patterns']:
                self.sku_extractor.add_custom_pattern(pattern, f"{retailer}_specific")
            
            logger.info(f"Optimized for retailer: {retailer}")
    
    def analyze_match_failure(self, product1: Dict, product2: Dict) -> Dict[str, Any]:
        """
        Analyze why two products failed to match
        
        Args:
            product1: First product
            product2: Second product
            
        Returns:
            Analysis of match failure
        """
        result = self.match_products(product1, product2)
        
        analysis = {
            'overall_confidence': result.confidence,
            'match_quality': result.match_quality,
            'failure_reasons': [],
            'improvement_suggestions': []
        }
        
        if result.confidence_result:
            # Analyze each factor
            for factor in result.confidence_result.factors:
                if factor.score < 0.5:
                    analysis['failure_reasons'].append({
                        'factor': factor.name,
                        'score': factor.score,
                        'details': factor.details
                    })
        
        # Generate improvement suggestions
        if result.confidence < 0.5:
            analysis['improvement_suggestions'].append("Consider manual review")
        
        if any(f.name == 'brand_match' and f.score < 0.3 for f in result.confidence_result.factors):
            analysis['improvement_suggestions'].append("Check brand alias mappings")
        
        if any(f.name == 'sku_match' and f.score < 0.3 for f in result.confidence_result.factors):
            analysis['improvement_suggestions'].append("Verify SKU extraction patterns")
        
        return analysis


# Example usage and testing
if __name__ == "__main__":
    # Initialize advanced matcher
    matcher = AdvancedProductMatcher()
    
    # Test products
    test_products = [
        {
            'id': 1,
            'name': 'MITSUBISHI แอร์ติดผนัง รุ่น MSY-KP13VF 12000BTU',
            'brand': 'MITSUBISHI',
            'price': 15000,
            'category': 'air-conditioner',
            'retailer': 'homepro'
        },
        {
            'id': 2,
            'name': 'มิตซูบิชิ เครื่องปรับอากาศ MSY-KP13VF 12,000 บีทียู',
            'brand': 'มิตซูบิชิ',
            'price': 15500,
            'category': 'air-conditioner',
            'retailer': 'thaiwatsadu'
        },
        {
            'id': 3,
            'name': 'Samsung ตู้เย็น RT29K5511S8 300 ลิตร',
            'brand': 'Samsung',
            'price': 12000,
            'category': 'refrigerator',
            'retailer': 'homepro'
        },
        {
            'id': 4,
            'name': 'ซัมซุง ตู้เย็น RT29K5511S8 300L',
            'brand': 'ซัมซุง',
            'price': 12200,
            'category': 'refrigerator',
            'retailer': 'globalhouse'
        }
    ]
    
    print("Advanced Product Matcher Test:")
    print("=" * 60)
    
    # Test individual matches
    print("\nIndividual Product Matches:")
    print("-" * 40)
    
    test_pairs = [
        (test_products[0], test_products[1]),  # Same AC, different retailers
        (test_products[2], test_products[3]),  # Same fridge, different retailers
        (test_products[0], test_products[2]),  # Different products
    ]
    
    for i, (product1, product2) in enumerate(test_pairs, 1):
        print(f"\nTest {i}:")
        print(f"  Product 1: {product1['name']}")
        print(f"  Product 2: {product2['name']}")
        
        result = matcher.match_products(product1, product2)
        
        print(f"  Confidence: {result.confidence:.3f}")
        print(f"  Match Quality: {result.match_quality}")
        print(f"  Processing Time: {result.processing_time:.3f}s")
        
        if result.confidence_result:
            print(f"  Recommendation: {result.confidence_result.recommendation}")
            
            # Show top factors
            sorted_factors = sorted(
                result.confidence_result.factors, 
                key=lambda f: f.score * f.weight, 
                reverse=True
            )
            print(f"  Top Factors:")
            for factor in sorted_factors[:3]:
                weighted_score = factor.score * factor.weight
                print(f"    {factor.name}: {factor.score:.3f} × {factor.weight:.3f} = {weighted_score:.3f}")
    
    # Test batch matching
    print(f"\n\nBatch Matching Test:")
    print("-" * 40)
    
    batch_results = matcher.batch_match_products(test_pairs)
    
    print(f"Processed {len(batch_results)} pairs")
    avg_confidence = sum(r.confidence for r in batch_results) / len(batch_results)
    print(f"Average confidence: {avg_confidence:.3f}")
    
    # Test matching against list
    print(f"\n\nMatch Against List Test:")
    print("-" * 40)
    
    target_product = test_products[0]
    search_results = matcher.match_product_against_list(
        target_product, 
        test_products[1:], 
        top_k=3
    )
    
    print(f"Target: {target_product['name']}")
    print(f"Found {len(search_results)} matches:")
    
    for i, result in enumerate(search_results, 1):
        print(f"  {i}. {result.product2['name']}")
        print(f"     Confidence: {result.confidence:.3f}")
        print(f"     Quality: {result.match_quality}")
    
    # Show statistics
    print(f"\n\nMatcher Statistics:")
    print("-" * 40)
    
    stats = matcher.get_statistics()
    print(f"Total matches: {stats['total_matches']}")
    print(f"Successful matches: {stats['successful_matches']}")
    print(f"Success rate: {stats['success_rate']:.3f}")
    print(f"Average processing time: {stats['avg_processing_time']:.3f}s")
    print(f"Error count: {stats['error_count']}")
    
    # Component statistics
    print(f"\nComponent Statistics:")
    for component, component_stats in stats['component_stats'].items():
        print(f"  {component}: {component_stats}")
    
    # Test configuration validation
    print(f"\n\nConfiguration Validation:")
    print("-" * 40)
    
    issues = matcher.validate_configuration()
    if issues:
        print("Issues found:")
        for issue in issues:
            print(f"  - {issue}")
    else:
        print("Configuration is valid")
    
    # Test match failure analysis
    print(f"\n\nMatch Failure Analysis:")
    print("-" * 40)
    
    failure_analysis = matcher.analyze_match_failure(test_products[0], test_products[2])
    print(f"Confidence: {failure_analysis['overall_confidence']:.3f}")
    print(f"Quality: {failure_analysis['match_quality']}")
    
    if failure_analysis['failure_reasons']:
        print("Failure reasons:")
        for reason in failure_analysis['failure_reasons']:
            print(f"  - {reason['factor']}: {reason['score']:.3f}")
    
    if failure_analysis['improvement_suggestions']:
        print("Improvement suggestions:")
        for suggestion in failure_analysis['improvement_suggestions']:
            print(f"  - {suggestion}")