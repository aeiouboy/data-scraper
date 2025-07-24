"""
Automated Validation Pipeline for Product Matching
Validates matching accuracy, detects anomalies, and provides quality metrics
"""

import json
import logging
import statistics
from typing import Dict, List, Optional, Tuple, Any, Set
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from pathlib import Path
from collections import defaultdict, Counter
import pandas as pd

from src.services.supabase_service import SupabaseService as SupabaseClient
from src.services.advanced_product_matcher import AdvancedProductMatcher
from src.utils.fuzzy_matcher import FuzzyMatcher
from src.utils.semantic_similarity import SemanticSimilarity
from src.utils.training_dataset_generator import TrainingDatasetGenerator

logger = logging.getLogger(__name__)


@dataclass
class ValidationResult:
    """Result of validation process"""
    accuracy: float
    precision: float
    recall: float
    f1_score: float
    confidence_distribution: Dict[str, int]
    error_analysis: Dict[str, Any]
    recommendations: List[str]
    timestamp: str
    sample_size: int


@dataclass
class MatchValidation:
    """Individual match validation result"""
    product1_id: str
    product2_id: str
    predicted_match: bool
    actual_match: bool
    confidence: float
    is_correct: bool
    error_type: Optional[str]
    details: Dict[str, Any]


@dataclass
class QualityMetrics:
    """Quality metrics for matching system"""
    total_matches: int
    correct_matches: int
    false_positives: int
    false_negatives: int
    avg_confidence: float
    confidence_std: float
    processing_time: float
    memory_usage: float


class ValidationPipeline:
    """Automated validation pipeline for product matching"""
    
    def __init__(self, db_client: Optional[SupabaseClient] = None):
        """Initialize validation pipeline"""
        self.db = db_client or SupabaseClient()
        self.matcher = AdvancedProductMatcher()
        self.fuzzy_matcher = FuzzyMatcher()
        self.semantic_similarity = SemanticSimilarity()
        self.dataset_generator = TrainingDatasetGenerator(self.db)
        
        # Validation thresholds
        self.thresholds = {
            'min_accuracy': 0.85,
            'min_precision': 0.80,
            'min_recall': 0.75,
            'max_false_positive_rate': 0.15,
            'min_confidence_threshold': 0.7,
            'max_processing_time': 5.0,  # seconds per match
        }
        
        # Error categories
        self.error_categories = {
            'brand_mismatch': 'Different brands incorrectly matched',
            'category_mismatch': 'Different product categories matched',
            'specification_error': 'Specifications don\'t align properly',
            'price_anomaly': 'Price difference exceeds reasonable range',
            'false_positive': 'Non-matching products marked as matches',
            'false_negative': 'Matching products not detected',
            'low_confidence': 'Match with confidence below threshold',
            'processing_timeout': 'Match processing exceeded time limit'
        }
        
        # Quality metrics storage
        self.metrics_history = []
        
    def run_validation(self, sample_size: int = 1000, 
                      validation_type: str = 'comprehensive') -> ValidationResult:
        """
        Run comprehensive validation of matching system
        
        Args:
            sample_size: Number of product pairs to validate
            validation_type: Type of validation ('comprehensive', 'quick', 'cross_validation')
            
        Returns:
            ValidationResult with detailed metrics
        """
        logger.info(f"Starting {validation_type} validation with {sample_size} samples")
        
        # Generate validation dataset
        validation_data = self._generate_validation_dataset(sample_size, validation_type)
        
        # Run validation tests
        validation_results = self._run_validation_tests(validation_data)
        
        # Analyze results
        accuracy_metrics = self._calculate_accuracy_metrics(validation_results)
        error_analysis = self._analyze_errors(validation_results)
        recommendations = self._generate_recommendations(accuracy_metrics, error_analysis)
        
        # Create confidence distribution
        confidence_dist = self._analyze_confidence_distribution(validation_results)
        
        result = ValidationResult(
            accuracy=accuracy_metrics['accuracy'],
            precision=accuracy_metrics['precision'],
            recall=accuracy_metrics['recall'],
            f1_score=accuracy_metrics['f1_score'],
            confidence_distribution=confidence_dist,
            error_analysis=error_analysis,
            recommendations=recommendations,
            timestamp=datetime.now().isoformat(),
            sample_size=len(validation_results)
        )
        
        # Store validation result
        self._store_validation_result(result)
        
        logger.info(f"Validation completed: Accuracy={result.accuracy:.3f}, F1={result.f1_score:.3f}")
        return result
    
    def _generate_validation_dataset(self, size: int, validation_type: str) -> List[Dict]:
        """Generate validation dataset with known ground truth"""
        logger.info(f"Generating validation dataset ({validation_type}, size={size})")
        
        if validation_type == 'comprehensive':
            # Use existing matches and generate negative examples
            positive_examples = self._get_verified_matches(size // 2)
            negative_examples = self._generate_negative_examples(size // 2)
            return positive_examples + negative_examples
            
        elif validation_type == 'quick':
            # Use smaller subset with high-confidence matches
            return self._get_verified_matches(size, min_confidence=0.9)
            
        elif validation_type == 'cross_validation':
            # Use different time periods for validation
            return self._get_temporal_validation_set(size)
            
        else:
            raise ValueError(f"Unknown validation type: {validation_type}")
    
    def _get_verified_matches(self, count: int, min_confidence: float = 0.0) -> List[Dict]:
        """Get verified product matches from database"""
        try:
            # Query verified matches from database
            response = self.db.client.table('product_matches').select(
                'product1_id, product2_id, confidence, is_verified, match_status'
            ).eq('is_verified', True).gte('confidence', min_confidence).limit(count).execute()
            
            matches = []
            for row in response.data:
                # Get product details
                product1 = self._get_product_details(row['product1_id'])
                product2 = self._get_product_details(row['product2_id'])
                
                if product1 and product2:
                    matches.append({
                        'product1': product1,
                        'product2': product2,
                        'ground_truth': row['match_status'] == 'match',
                        'confidence': row['confidence'],
                        'source': 'verified_match'
                    })
            
            logger.info(f"Retrieved {len(matches)} verified matches")
            return matches
            
        except Exception as e:
            logger.error(f"Error getting verified matches: {e}")
            return self._generate_synthetic_validation_data(count)
    
    def _generate_negative_examples(self, count: int) -> List[Dict]:
        """Generate negative examples (non-matching products)"""
        try:
            # Get products from different categories/brands
            response = self.db.client.table('products').select(
                'id, name, brand, category, specifications, price'
            ).limit(count * 3).execute()
            
            products = response.data
            negative_examples = []
            
            # Pair products from different categories or brands
            used_pairs = set()
            
            for i in range(len(products)):
                if len(negative_examples) >= count:
                    break
                    
                for j in range(i + 1, len(products)):
                    if len(negative_examples) >= count:
                        break
                    
                    product1 = products[i]
                    product2 = products[j]
                    
                    # Ensure they're different enough to be negative examples
                    if (product1['category'] != product2['category'] or 
                        product1['brand'] != product2['brand']):
                        
                        pair_key = tuple(sorted([product1['id'], product2['id']]))
                        if pair_key not in used_pairs:
                            negative_examples.append({
                                'product1': product1,
                                'product2': product2,
                                'ground_truth': False,
                                'confidence': 0.0,
                                'source': 'generated_negative'
                            })
                            used_pairs.add(pair_key)
            
            logger.info(f"Generated {len(negative_examples)} negative examples")
            return negative_examples
            
        except Exception as e:
            logger.error(f"Error generating negative examples: {e}")
            return []
    
    def _generate_synthetic_validation_data(self, count: int) -> List[Dict]:
        """Generate synthetic validation data for testing"""
        synthetic_data = []
        
        # Create synthetic product pairs
        for i in range(count):
            if i % 2 == 0:  # Positive example
                product1 = {
                    'id': f'test_p1_{i}',
                    'name': 'Samsung Smart TV 55 นิ้ว',
                    'brand': 'Samsung',
                    'category': 'Television',
                    'specifications': {'size': '55 inch', 'type': 'Smart TV'},
                    'price': 25000
                }
                product2 = {
                    'id': f'test_p2_{i}',
                    'name': 'ซัมซุง สมาร์ททีวี 55 inch',
                    'brand': 'Samsung',
                    'category': 'Television', 
                    'specifications': {'size': '55 inch', 'type': 'Smart TV'},
                    'price': 25500
                }
                ground_truth = True
            else:  # Negative example
                product1 = {
                    'id': f'test_p1_{i}',
                    'name': 'Samsung ตู้เย็น 300L',
                    'brand': 'Samsung',
                    'category': 'Refrigerator',
                    'specifications': {'capacity': '300L', 'doors': '2'},
                    'price': 15000
                }
                product2 = {
                    'id': f'test_p2_{i}',
                    'name': 'LG แอร์ 18000 BTU',
                    'brand': 'LG',
                    'category': 'Air Conditioner',
                    'specifications': {'capacity': '18000 BTU', 'type': 'Split'},
                    'price': 22000
                }
                ground_truth = False
            
            synthetic_data.append({
                'product1': product1,
                'product2': product2,
                'ground_truth': ground_truth,
                'confidence': 0.8 if ground_truth else 0.2,
                'source': 'synthetic'
            })
        
        logger.info(f"Generated {len(synthetic_data)} synthetic validation examples")
        return synthetic_data
    
    def _get_temporal_validation_set(self, count: int) -> List[Dict]:
        """Get validation set from different time periods"""
        try:
            # Get matches from different time periods
            week_ago = (datetime.now() - timedelta(days=7)).isoformat()
            
            response = self.db.client.table('product_matches').select(
                'product1_id, product2_id, confidence, match_status, created_at'
            ).gte('created_at', week_ago).limit(count).execute()
            
            matches = []
            for row in response.data:
                product1 = self._get_product_details(row['product1_id'])
                product2 = self._get_product_details(row['product2_id'])
                
                if product1 and product2:
                    matches.append({
                        'product1': product1,
                        'product2': product2,
                        'ground_truth': row['match_status'] == 'match',
                        'confidence': row['confidence'],
                        'source': 'temporal_validation'
                    })
            
            return matches
            
        except Exception as e:
            logger.error(f"Error getting temporal validation set: {e}")
            return self._generate_synthetic_validation_data(count)
    
    def _get_product_details(self, product_id: str) -> Optional[Dict]:
        """Get product details from database"""
        try:
            response = self.db.client.table('products').select(
                'id, name, brand, category, specifications, price'
            ).eq('id', product_id).execute()
            
            if response.data:
                return response.data[0]
            return None
            
        except Exception as e:
            logger.error(f"Error getting product details for {product_id}: {e}")
            return None
    
    def _run_validation_tests(self, validation_data: List[Dict]) -> List[MatchValidation]:
        """Run validation tests on dataset"""
        logger.info(f"Running validation tests on {len(validation_data)} examples")
        
        results = []
        
        for i, example in enumerate(validation_data):
            try:
                # Run matching
                start_time = datetime.now()
                match_result = self.matcher.match_products(
                    example['product1'], 
                    example['product2']
                )
                processing_time = (datetime.now() - start_time).total_seconds()
                
                # Determine predicted match
                predicted_match = match_result.confidence >= self.thresholds['min_confidence_threshold']
                actual_match = example['ground_truth']
                
                # Classify result
                is_correct = predicted_match == actual_match
                error_type = None
                
                if not is_correct:
                    if predicted_match and not actual_match:
                        error_type = 'false_positive'
                    elif not predicted_match and actual_match:
                        error_type = 'false_negative'
                
                # Additional error analysis
                if error_type is None and processing_time > self.thresholds['max_processing_time']:
                    error_type = 'processing_timeout'
                elif match_result.confidence < self.thresholds['min_confidence_threshold']:
                    error_type = 'low_confidence'
                
                results.append(MatchValidation(
                    product1_id=example['product1']['id'],
                    product2_id=example['product2']['id'],
                    predicted_match=predicted_match,
                    actual_match=actual_match,
                    confidence=match_result.confidence,
                    is_correct=is_correct,
                    error_type=error_type,
                    details={
                        'processing_time': processing_time,
                        'match_details': match_result.details,
                        'source': example['source']
                    }
                ))
                
                if (i + 1) % 100 == 0:
                    logger.info(f"Processed {i + 1}/{len(validation_data)} validation examples")
                    
            except Exception as e:
                logger.error(f"Error processing validation example {i}: {e}")
                continue
        
        logger.info(f"Completed validation testing: {len(results)} results")
        return results
    
    def _calculate_accuracy_metrics(self, results: List[MatchValidation]) -> Dict[str, float]:
        """Calculate accuracy metrics from validation results"""
        if not results:
            return {'accuracy': 0.0, 'precision': 0.0, 'recall': 0.0, 'f1_score': 0.0}
        
        # Count outcomes
        true_positives = sum(1 for r in results if r.predicted_match and r.actual_match)
        false_positives = sum(1 for r in results if r.predicted_match and not r.actual_match)
        true_negatives = sum(1 for r in results if not r.predicted_match and not r.actual_match)
        false_negatives = sum(1 for r in results if not r.predicted_match and r.actual_match)
        
        # Calculate metrics
        total = len(results)
        accuracy = (true_positives + true_negatives) / total if total > 0 else 0
        
        precision = true_positives / (true_positives + false_positives) if (true_positives + false_positives) > 0 else 0
        recall = true_positives / (true_positives + false_negatives) if (true_positives + false_negatives) > 0 else 0
        
        f1_score = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0
        
        return {
            'accuracy': accuracy,
            'precision': precision,
            'recall': recall,
            'f1_score': f1_score,
            'true_positives': true_positives,
            'false_positives': false_positives,
            'true_negatives': true_negatives,
            'false_negatives': false_negatives
        }
    
    def _analyze_errors(self, results: List[MatchValidation]) -> Dict[str, Any]:
        """Analyze errors and patterns in validation results"""
        error_analysis = {
            'error_distribution': Counter(),
            'confidence_by_error': defaultdict(list),
            'processing_time_stats': {},
            'common_error_patterns': []
        }
        
        # Collect error statistics
        processing_times = []
        for result in results:
            if result.error_type:
                error_analysis['error_distribution'][result.error_type] += 1
                error_analysis['confidence_by_error'][result.error_type].append(result.confidence)
            
            processing_times.append(result.details.get('processing_time', 0))
        
        # Processing time statistics
        if processing_times:
            error_analysis['processing_time_stats'] = {
                'mean': statistics.mean(processing_times),
                'median': statistics.median(processing_times),
                'std': statistics.stdev(processing_times) if len(processing_times) > 1 else 0,
                'max': max(processing_times),
                'min': min(processing_times)
            }
        
        # Analyze confidence distributions by error type
        for error_type, confidences in error_analysis['confidence_by_error'].items():
            if confidences:
                error_analysis['confidence_by_error'][error_type] = {
                    'mean': statistics.mean(confidences),
                    'std': statistics.stdev(confidences) if len(confidences) > 1 else 0,
                    'count': len(confidences)
                }
        
        # Identify common error patterns
        error_analysis['common_error_patterns'] = self._identify_error_patterns(results)
        
        return error_analysis
    
    def _identify_error_patterns(self, results: List[MatchValidation]) -> List[Dict]:
        """Identify common patterns in matching errors"""
        patterns = []
        
        # Group errors by type
        error_groups = defaultdict(list)
        for result in results:
            if result.error_type:
                error_groups[result.error_type].append(result)
        
        for error_type, error_results in error_groups.items():
            if len(error_results) >= 5:  # Only analyze patterns with sufficient data
                pattern = {
                    'error_type': error_type,
                    'count': len(error_results),
                    'avg_confidence': statistics.mean([r.confidence for r in error_results]),
                    'description': self.error_categories.get(error_type, 'Unknown error type')
                }
                patterns.append(pattern)
        
        return patterns
    
    def _analyze_confidence_distribution(self, results: List[MatchValidation]) -> Dict[str, int]:
        """Analyze distribution of confidence scores"""
        distribution = {
            'very_high': 0,  # 0.9+
            'high': 0,       # 0.8-0.89
            'medium': 0,     # 0.6-0.79
            'low': 0,        # 0.4-0.59
            'very_low': 0    # <0.4
        }
        
        for result in results:
            confidence = result.confidence
            if confidence >= 0.9:
                distribution['very_high'] += 1
            elif confidence >= 0.8:
                distribution['high'] += 1
            elif confidence >= 0.6:
                distribution['medium'] += 1
            elif confidence >= 0.4:
                distribution['low'] += 1
            else:
                distribution['very_low'] += 1
        
        return distribution
    
    def _generate_recommendations(self, metrics: Dict[str, float], 
                                error_analysis: Dict[str, Any]) -> List[str]:
        """Generate recommendations based on validation results"""
        recommendations = []
        
        # Accuracy-based recommendations
        if metrics['accuracy'] < self.thresholds['min_accuracy']:
            recommendations.append(f"Overall accuracy ({metrics['accuracy']:.3f}) below threshold ({self.thresholds['min_accuracy']}) - Consider tuning matching algorithms")
        
        if metrics['precision'] < self.thresholds['min_precision']:
            recommendations.append(f"Precision ({metrics['precision']:.3f}) below threshold - Too many false positives, increase confidence threshold")
        
        if metrics['recall'] < self.thresholds['min_recall']:
            recommendations.append(f"Recall ({metrics['recall']:.3f}) below threshold - Missing true matches, consider relaxing matching criteria")
        
        # Error pattern recommendations
        error_dist = error_analysis['error_distribution']
        
        if error_dist['false_positive'] > len(error_dist) * 0.2:
            recommendations.append("High false positive rate - Review brand and category matching logic")
        
        if error_dist['false_negative'] > len(error_dist) * 0.2:
            recommendations.append("High false negative rate - Consider improving text normalization and similarity scoring")
        
        if error_dist['low_confidence'] > len(error_dist) * 0.15:
            recommendations.append("Many low confidence matches - Review confidence calculation weights")
        
        # Performance recommendations
        proc_time = error_analysis.get('processing_time_stats', {})
        if proc_time.get('mean', 0) > self.thresholds['max_processing_time']:
            recommendations.append(f"Average processing time ({proc_time['mean']:.2f}s) exceeds threshold - Consider performance optimization")
        
        if not recommendations:
            recommendations.append("Validation results meet all quality thresholds - System performing well")
        
        return recommendations
    
    def _store_validation_result(self, result: ValidationResult):
        """Store validation result for historical tracking"""
        try:
            # Store in database
            validation_data = {
                'timestamp': result.timestamp,
                'accuracy': result.accuracy,
                'precision': result.precision,
                'recall': result.recall,
                'f1_score': result.f1_score,
                'sample_size': result.sample_size,
                'confidence_distribution': json.dumps(result.confidence_distribution),
                'error_analysis': json.dumps(result.error_analysis),
                'recommendations': json.dumps(result.recommendations)
            }
            
            response = self.db.client.table('validation_results').insert(validation_data).execute()
            logger.info(f"Stored validation result with ID: {response.data[0]['id']}")
            
        except Exception as e:
            logger.error(f"Error storing validation result: {e}")
            # Fallback: save to file
            self._save_validation_to_file(result)
    
    def _save_validation_to_file(self, result: ValidationResult):
        """Save validation result to file as backup"""
        try:
            results_dir = Path("validation_results")
            results_dir.mkdir(exist_ok=True)
            
            filename = f"validation_{result.timestamp.replace(':', '-')}.json"
            filepath = results_dir / filename
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(asdict(result), f, indent=2, ensure_ascii=False)
            
            logger.info(f"Saved validation result to {filepath}")
            
        except Exception as e:
            logger.error(f"Error saving validation result to file: {e}")
    
    def get_validation_history(self, days: int = 30) -> List[ValidationResult]:
        """Get validation history from the last N days"""
        try:
            since_date = (datetime.now() - timedelta(days=days)).isoformat()
            
            response = self.db.client.table('validation_results').select(
                '*'
            ).gte('timestamp', since_date).order('timestamp', desc=True).execute()
            
            history = []
            for row in response.data:
                result = ValidationResult(
                    accuracy=row['accuracy'],
                    precision=row['precision'],
                    recall=row['recall'],
                    f1_score=row['f1_score'],
                    confidence_distribution=json.loads(row['confidence_distribution']),
                    error_analysis=json.loads(row['error_analysis']),
                    recommendations=json.loads(row['recommendations']),
                    timestamp=row['timestamp'],
                    sample_size=row['sample_size']
                )
                history.append(result)
            
            return history
            
        except Exception as e:
            logger.error(f"Error getting validation history: {e}")
            return []
    
    def run_continuous_validation(self, interval_hours: int = 24, sample_size: int = 500):
        """Run continuous validation at specified intervals"""
        logger.info(f"Starting continuous validation (every {interval_hours} hours)")
        
        import schedule
        import time
        
        def validation_job():
            try:
                result = self.run_validation(sample_size, 'quick')
                
                # Check if validation meets thresholds
                if (result.accuracy < self.thresholds['min_accuracy'] or 
                    result.precision < self.thresholds['min_precision'] or 
                    result.f1_score < 0.8):
                    
                    logger.warning(f"Validation alert: Quality metrics below threshold")
                    logger.warning(f"Accuracy: {result.accuracy:.3f}, Precision: {result.precision:.3f}, F1: {result.f1_score:.3f}")
                    
                    # Could trigger alerts/notifications here
                    
            except Exception as e:
                logger.error(f"Error in continuous validation: {e}")
        
        # Schedule validation
        schedule.every(interval_hours).hours.do(validation_job)
        
        # Run initial validation
        validation_job()
        
        # Keep running
        while True:
            schedule.run_pending()
            time.sleep(3600)  # Check every hour


# Example usage and testing
if __name__ == "__main__":
    # Initialize validation pipeline
    pipeline = ValidationPipeline()
    
    print("Running Automated Validation Pipeline...")
    print("=" * 60)
    
    # Run comprehensive validation
    result = pipeline.run_validation(sample_size=100, validation_type='comprehensive')
    
    print(f"\nValidation Results:")
    print(f"  Accuracy: {result.accuracy:.3f}")
    print(f"  Precision: {result.precision:.3f}")
    print(f"  Recall: {result.recall:.3f}")
    print(f"  F1 Score: {result.f1_score:.3f}")
    print(f"  Sample Size: {result.sample_size}")
    
    print(f"\nConfidence Distribution:")
    for level, count in result.confidence_distribution.items():
        print(f"  {level}: {count}")
    
    print(f"\nRecommendations:")
    for i, rec in enumerate(result.recommendations, 1):
        print(f"  {i}. {rec}")
    
    print(f"\nError Analysis:")
    error_dist = result.error_analysis.get('error_distribution', {})
    for error_type, count in error_dist.items():
        print(f"  {error_type}: {count}")
    
    # Test quick validation
    print(f"\n\nRunning Quick Validation...")
    print("=" * 60)
    
    quick_result = pipeline.run_validation(sample_size=50, validation_type='quick')
    
    print(f"Quick Validation - Accuracy: {quick_result.accuracy:.3f}, F1: {quick_result.f1_score:.3f}")
    
    # Get validation history
    print(f"\n\nValidation History (Last 7 days):")
    print("=" * 60)
    
    history = pipeline.get_validation_history(days=7)
    
    if history:
        print(f"Found {len(history)} validation runs:")
        for i, hist_result in enumerate(history[:5], 1):  # Show last 5
            print(f"  {i}. {hist_result.timestamp[:10]} - Accuracy: {hist_result.accuracy:.3f}")
    else:
        print("No validation history found")
    
    print("\nValidation pipeline testing completed")