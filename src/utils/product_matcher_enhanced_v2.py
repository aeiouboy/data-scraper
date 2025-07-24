#!/usr/bin/env python3
"""
Enhanced Product Matcher v2 with Advanced Validation

This module provides comprehensive product matching with BTU validation,
model series validation, and category-specific rules to prevent false positives.
"""

import logging
import re
from typing import Dict, Any, List, Tuple, Optional, Set
from dataclasses import dataclass, field
from datetime import datetime

from .btu_validator import BTUValidator
from .model_validator import ModelValidator
from .category_matching_rules import CategoryMatchingEngine, MatchingStrictness
from .text_normalizer_enhanced import EnhancedTextNormalizer

logger = logging.getLogger(__name__)

@dataclass
class MatchResult:
    """Container for match results with detailed validation information."""
    confidence: float
    is_valid: bool
    reasons: List[str] = field(default_factory=list)
    rejection_reasons: List[str] = field(default_factory=list)
    validation_details: Dict[str, Any] = field(default_factory=dict)
    match_type: str = "unknown"
    category: str = "default"
    processing_time_ms: float = 0.0
    
    def add_reason(self, reason: str):
        """Add a positive matching reason."""
        self.reasons.append(reason)
        
    def add_rejection(self, reason: str):
        """Add a rejection reason."""
        self.rejection_reasons.append(reason)
        self.is_valid = False
        
    def add_validation_detail(self, key: str, value: Any):
        """Add validation detail."""
        self.validation_details[key] = value

class EnhancedProductMatcher:
    """
    Enhanced product matcher with comprehensive validation system.
    
    Features:
    - BTU validation for air conditioners (5% tolerance)
    - Model series validation to prevent false positives
    - Category-specific matching rules and thresholds
    - Configurable strictness levels
    - Detailed validation reporting
    """
    
    def __init__(self, strictness: MatchingStrictness = MatchingStrictness.STRICT):
        """
        Initialize the enhanced product matcher.
        
        Args:
            strictness: Default strictness level for matching
        """
        self.strictness = strictness
        self.btu_validator = BTUValidator(tolerance=0.05)  # 5% BTU tolerance
        self.model_validator = ModelValidator(strict_series_matching=True)
        self.category_engine = CategoryMatchingEngine()
        self.text_normalizer = self._get_text_normalizer()
        
        # Performance tracking
        self.match_stats = {
            'total_matches': 0,
            'valid_matches': 0,
            'rejected_matches': 0,
            'false_positives_prevented': 0
        }
        
    def match_products(self, product1: Dict[str, Any], product2: Dict[str, Any]) -> MatchResult:
        """
        Match two products with comprehensive validation.
        
        Args:
            product1: First product dictionary
            product2: Second product dictionary
            
        Returns:
            MatchResult with confidence score and validation details
        """
        start_time = datetime.now()
        
        # Initialize result
        result = MatchResult(
            confidence=0.0,
            is_valid=True,
            category=self.category_engine.get_normalized_category(product1.get('category', ''))
        )
        
        try:
            # Phase 1: Category validation (early exit for incompatible categories)
            cat_valid, cat_reason, cat_details = self.category_engine.validate_category_match(product1, product2)
            result.add_validation_detail('category_validation', cat_details)
            
            if not cat_valid:
                result.add_rejection(f"Category validation failed: {cat_reason}")
                result.match_type = "category_mismatch"
                self._finalize_result(result, start_time)
                return result
                
            # Phase 2: Apply category-specific validations
            validations_valid, validations_reason, validations_details = self.category_engine.apply_category_validations(product1, product2)
            result.add_validation_detail('category_validations', validations_details)
            
            if not validations_valid:
                result.add_rejection(f"Category-specific validation failed: {validations_reason}")
                result.match_type = "validation_failure"
                self.match_stats['false_positives_prevented'] += 1
                self._finalize_result(result, start_time)
                return result
                
            # Phase 3: Calculate base confidence using traditional methods
            base_confidence = self._calculate_base_confidence(product1, product2)
            result.confidence = base_confidence
            result.add_validation_detail('base_confidence', base_confidence)
            
            # Phase 4: Apply category-specific confidence adjustments
            adjusted_confidence, confidence_details = self.category_engine.calculate_category_confidence(
                product1, product2, base_confidence
            )
            result.confidence = adjusted_confidence
            result.add_validation_detail('confidence_adjustments', confidence_details)
            
            # Phase 5: Final confidence threshold check
            category_rules = self.category_engine.get_category_rules(result.category)
            if result.confidence < category_rules.minimum_confidence:
                result.add_rejection(
                    f"Confidence {result.confidence:.3f} below category threshold {category_rules.minimum_confidence}"
                )
                result.match_type = "low_confidence"
                self._finalize_result(result, start_time)
                return result
                
            # Phase 6: Success - determine match type and add reasons
            result.match_type = self._determine_match_type(product1, product2, result)
            self._add_positive_reasons(product1, product2, result)
            
            result.add_reason(f"Passed all {result.category} validations")
            result.add_reason(f"Confidence {result.confidence:.3f} meets threshold {category_rules.minimum_confidence}")
            
        except Exception as e:
            logger.error(f"Error in product matching: {str(e)}")
            result.add_rejection(f"Matching error: {str(e)}")
            result.match_type = "error"
            
        self._finalize_result(result, start_time)
        return result
    
    def batch_match_products(self, products: List[Dict[str, Any]]) -> List[Tuple[int, int, MatchResult]]:
        """
        Match multiple products in batch with optimizations.
        
        Args:
            products: List of product dictionaries
            
        Returns:
            List of (index1, index2, MatchResult) tuples for valid matches
        """
        matches = []
        total_pairs = (len(products) * (len(products) - 1)) // 2
        
        logger.info(f"Starting batch matching of {len(products)} products ({total_pairs} pairs)")
        
        for i in range(len(products)):
            for j in range(i + 1, len(products)):
                result = self.match_products(products[i], products[j])
                
                if result.is_valid:
                    matches.append((i, j, result))
                    
        logger.info(f"Batch matching complete: {len(matches)} valid matches from {total_pairs} pairs")
        return matches
    
    def _calculate_base_confidence(self, product1: Dict[str, Any], product2: Dict[str, Any]) -> float:
        """
        Calculate base confidence using traditional matching methods.
        
        Args:
            product1: First product
            product2: Second product
            
        Returns:
            Base confidence score (0.0 to 1.0)
        """
        # Get category rules for weighting
        category = self.category_engine.get_normalized_category(product1.get('category', ''))
        rules = self.category_engine.get_category_rules(category)
        
        # Component scores
        scores = {}
        
        # 1. Name similarity
        name1 = self.text_normalizer.normalize_product_name(product1.get('name', ''))
        name2 = self.text_normalizer.normalize_product_name(product2.get('name', ''))
        scores['name'] = self._calculate_name_similarity(name1, name2)
        
        # 2. Brand similarity
        brand1 = product1.get('brand', '').lower().strip()
        brand2 = product2.get('brand', '').lower().strip()
        scores['brand'] = 1.0 if brand1 == brand2 and brand1 else 0.0
        
        # 3. Specifications similarity
        scores['specs'] = self._calculate_spec_similarity(product1, product2)
        
        # 4. Category-specific features
        if category == 'air_conditioner':
            scores['btu'] = self._calculate_btu_similarity(product1, product2)
            scores['model'] = self._calculate_model_similarity(product1, product2)
        
        # Calculate weighted average
        total_weight = 0
        weighted_sum = 0
        
        # Apply category-specific weights
        weights = {
            'name': rules.name_weight,
            'brand': rules.brand_weight,
            'specs': rules.spec_weight,
            'btu': 0.3 if category == 'air_conditioner' else 0.0,
            'model': 0.2 if category == 'air_conditioner' else 0.0
        }
        
        for component, score in scores.items():
            weight = weights.get(component, 0.0)
            if weight > 0:
                weighted_sum += score * weight
                total_weight += weight
                
        base_confidence = weighted_sum / total_weight if total_weight > 0 else 0.0
        
        logger.debug(f"Base confidence calculation: {scores} -> {base_confidence:.3f}")
        return base_confidence
    
    def _calculate_name_similarity(self, name1: str, name2: str) -> float:
        """Calculate similarity between normalized product names."""
        if not name1 or not name2:
            return 0.0
            
        # Token-based similarity
        tokens1 = set(name1.split())
        tokens2 = set(name2.split())
        
        if not tokens1 or not tokens2:
            return 0.0
            
        intersection = tokens1.intersection(tokens2)
        union = tokens1.union(tokens2)
        
        jaccard_similarity = len(intersection) / len(union)
        
        # Character-based similarity for fine-tuning
        char_similarity = self._calculate_character_similarity(name1, name2)
        
        # Combine both methods
        return 0.7 * jaccard_similarity + 0.3 * char_similarity
    
    def _calculate_character_similarity(self, str1: str, str2: str) -> float:
        """Calculate character-level similarity using Levenshtein-like approach."""
        if not str1 or not str2:
            return 0.0
            
        max_len = max(len(str1), len(str2))
        if max_len == 0:
            return 1.0
            
        # Simple character matching
        matches = sum(c1 == c2 for c1, c2 in zip(str1, str2))
        return matches / max_len
    
    def _calculate_spec_similarity(self, product1: Dict[str, Any], product2: Dict[str, Any]) -> float:
        """Calculate similarity between product specifications."""
        specs1 = product1.get('specifications', {})
        specs2 = product2.get('specifications', {})
        
        if not specs1 or not specs2:
            return 0.5  # Neutral score if specs missing
            
        # Compare common specification fields
        common_keys = set(specs1.keys()).intersection(set(specs2.keys()))
        
        if not common_keys:
            return 0.5
            
        matches = 0
        for key in common_keys:
            val1 = str(specs1[key]).lower().strip()
            val2 = str(specs2[key]).lower().strip()
            if val1 == val2:
                matches += 1
                
        return matches / len(common_keys)
    
    def _calculate_btu_similarity(self, product1: Dict[str, Any], product2: Dict[str, Any]) -> float:
        """Calculate BTU-based similarity for air conditioners."""
        btu1 = self.btu_validator.extract_btu(product1.get('name', ''))
        btu2 = self.btu_validator.extract_btu(product2.get('name', ''))
        
        if not btu1 or not btu2:
            return 0.0
            
        # Calculate variance
        variance = abs(btu1 - btu2) / max(btu1, btu2)
        
        # Convert to similarity (inverse of variance)
        if variance <= 0.05:  # 5% tolerance
            return 1.0
        elif variance <= 0.1:  # 10% tolerance
            return 0.8
        elif variance <= 0.2:  # 20% tolerance
            return 0.5
        else:
            return 0.0
    
    def _calculate_model_similarity(self, product1: Dict[str, Any], product2: Dict[str, Any]) -> float:
        """Calculate model-based similarity."""
        model1 = self.model_validator.extract_model_info(product1.get('name', ''), product1.get('brand'))
        model2 = self.model_validator.extract_model_info(product2.get('name', ''), product2.get('brand'))
        
        if not model1.full_model or not model2.full_model:
            return 0.5  # Neutral if no models found
            
        # Exact model match
        if model1.full_model == model2.full_model:
            return 1.0
            
        # Same series
        if model1.series == model2.series and model1.series:
            return 0.8
            
        # Different series from same brand
        if model1.brand == model2.brand and model1.brand:
            return 0.3
            
        return 0.0
    
    def _determine_match_type(self, product1: Dict[str, Any], product2: Dict[str, Any], result: MatchResult) -> str:
        """Determine the type of match based on validation results."""
        validations = result.validation_details.get('category_validations', {}).get('validations', {})
        
        # Check for exact matches
        if 'model_match' in validations:
            model_result = validations['model_match']
            if model_result.get('is_valid') and 'exact model match' in model_result.get('reason', '').lower():
                return "exact_model_match"
                
        if 'btu_match' in validations:
            btu_result = validations['btu_match']
            if btu_result.get('is_valid'):
                btu_details = btu_result.get('details', {})
                if btu_details.get('variance_percentage', 100) < 2:
                    return "exact_btu_match"
                    
        # Check for series matches
        if result.category == 'air_conditioner':
            return "air_conditioner_match"
        elif result.category == 'electronics':
            return "electronics_match"
        else:
            return "standard_match"
    
    def _add_positive_reasons(self, product1: Dict[str, Any], product2: Dict[str, Any], result: MatchResult):
        """Add specific reasons why the match was successful."""
        validations = result.validation_details.get('category_validations', {}).get('validations', {})
        
        for validation_name, validation_result in validations.items():
            if validation_result.get('is_valid'):
                reason = validation_result.get('reason', f"{validation_name} passed")
                result.add_reason(reason)
                
        # Add confidence-based reasons
        confidence_adjustments = result.validation_details.get('confidence_adjustments', {}).get('adjustments', {})
        for adjustment_name, adjustment_details in confidence_adjustments.items():
            if adjustment_details.get('applied'):
                reason = adjustment_details.get('reason', f"{adjustment_name} applied")
                result.add_reason(reason)
    
    def _finalize_result(self, result: MatchResult, start_time: datetime):
        """Finalize match result with timing and statistics."""
        end_time = datetime.now()
        result.processing_time_ms = (end_time - start_time).total_seconds() * 1000
        
        # Update statistics
        self.match_stats['total_matches'] += 1
        if result.is_valid:
            self.match_stats['valid_matches'] += 1
        else:
            self.match_stats['rejected_matches'] += 1
            
        logger.debug(f"Match result: {result.match_type}, confidence: {result.confidence:.3f}, "
                    f"valid: {result.is_valid}, time: {result.processing_time_ms:.1f}ms")
    
    def _get_text_normalizer(self):
        """Get text normalizer instance (fallback if not available)."""
        try:
            return EnhancedTextNormalizer()
        except ImportError:
            logger.warning("EnhancedTextNormalizer not available, using basic normalization")
            return BasicTextNormalizer()
    
    def get_match_statistics(self) -> Dict[str, Any]:
        """Get matching performance statistics."""
        total = self.match_stats['total_matches']
        return {
            **self.match_stats,
            'success_rate': self.match_stats['valid_matches'] / total if total > 0 else 0.0,
            'rejection_rate': self.match_stats['rejected_matches'] / total if total > 0 else 0.0,
            'false_positive_prevention_rate': self.match_stats['false_positives_prevented'] / total if total > 0 else 0.0
        }
    
    def reset_statistics(self):
        """Reset matching statistics."""
        self.match_stats = {
            'total_matches': 0,
            'valid_matches': 0,
            'rejected_matches': 0,
            'false_positives_prevented': 0
        }

class BasicTextNormalizer:
    """Basic text normalizer fallback."""
    
    def normalize_product_name(self, name: str) -> str:
        """Basic normalization."""
        if not name:
            return ""
            
        # Remove common noise
        normalized = re.sub(r'[^\w\s]', ' ', name)
        normalized = re.sub(r'\s+', ' ', normalized)
        return normalized.lower().strip()


# Convenience functions for backward compatibility
def match_products_enhanced(product1: Dict[str, Any], product2: Dict[str, Any], 
                           strictness: MatchingStrictness = MatchingStrictness.STRICT) -> MatchResult:
    """
    Enhanced product matching with comprehensive validation.
    
    Args:
        product1: First product dictionary
        product2: Second product dictionary
        strictness: Matching strictness level
        
    Returns:
        MatchResult with detailed validation information
    """
    matcher = EnhancedProductMatcher(strictness=strictness)
    return matcher.match_products(product1, product2)

def validate_product_match(product1: Dict[str, Any], product2: Dict[str, Any]) -> Tuple[bool, str, float]:
    """
    Simple validation function for existing code compatibility.
    
    Args:
        product1: First product
        product2: Second product
        
    Returns:
        Tuple of (is_valid, reason, confidence)
    """
    result = match_products_enhanced(product1, product2)
    main_reason = result.rejection_reasons[0] if result.rejection_reasons else (
        result.reasons[0] if result.reasons else "No specific reason"
    )
    return result.is_valid, main_reason, result.confidence


if __name__ == "__main__":
    # Test the enhanced product matcher
    matcher = EnhancedProductMatcher(strictness=MatchingStrictness.STRICT)
    
    # Test products
    test_products = [
        {
            'name': 'แอร์ผนัง DAIKIN FTKZ24YV2S 24200 บีทียู อินเวอร์เตอร์',
            'brand': 'DAIKIN',
            'category': 'air_conditioner',
            'specifications': {'btu': '24200', 'inverter': True}
        },
        {
            'name': 'แอร์ติดผนัง Inverter 24,200 BTU Wi-Fi DAIKIN รุ่น FTKZ24YV2S',
            'brand': 'DAIKIN',
            'category': 'air_conditioner',
            'specifications': {'btu': '24200', 'wifi': True}
        },
        {
            'name': 'แอร์ผนัง CARRIER 42TVAB013ABI 12200 บีทียู อินเวอร์เตอร์',
            'brand': 'CARRIER',
            'category': 'air_conditioner',
            'specifications': {'btu': '12200'}
        },
        {
            'name': 'CARRIER Wi-Fi Inverter Air Conditioner (38TVEA028A42TVEA028A), 25,200 BTU',
            'brand': 'CARRIER',
            'category': 'air_conditioner',
            'specifications': {'btu': '25200'}
        },
        {
            'name': 'อุปกรณ์ซัพพอร์ต ฟูทูโร่ พยุงข้อเท้า ไซส์ L',
            'brand': 'FUTURO',
            'category': 'medical_equipment',
            'specifications': {'size': 'L'}
        }
    ]
    
    print("Enhanced Product Matcher Test Results:")
    print("=" * 60)
    
    # Test cases
    test_cases = [
        (0, 1, "DAIKIN same model, same BTU"),
        (0, 2, "DAIKIN vs CARRIER, different BTU"),
        (2, 3, "CARRIER different series, different BTU"),
        (0, 4, "Air conditioner vs medical equipment"),
    ]
    
    for idx1, idx2, description in test_cases:
        print(f"\nTest: {description}")
        print("-" * 40)
        
        result = matcher.match_products(test_products[idx1], test_products[idx2])
        
        print(f"Valid: {result.is_valid}")
        print(f"Confidence: {result.confidence:.3f}")
        print(f"Match Type: {result.match_type}")
        print(f"Category: {result.category}")
        print(f"Processing Time: {result.processing_time_ms:.1f}ms")
        
        if result.reasons:
            print("Reasons:")
            for reason in result.reasons[:3]:  # Show first 3 reasons
                print(f"  + {reason}")
                
        if result.rejection_reasons:
            print("Rejections:")
            for rejection in result.rejection_reasons[:3]:  # Show first 3 rejections
                print(f"  - {rejection}")
    
    # Show statistics
    print(f"\nMatcher Statistics:")
    print("=" * 30)
    stats = matcher.get_match_statistics()
    for key, value in stats.items():
        if isinstance(value, float):
            print(f"{key}: {value:.3f}")
        else:
            print(f"{key}: {value}")