#!/usr/bin/env python3
"""
Category-Specific Matching Rules for Product Validation

This module provides category-specific validation rules and thresholds
to ensure accurate product matching based on product type characteristics.
"""

import logging
from typing import Dict, Any, Tuple, List, Optional, Set
from dataclasses import dataclass
from enum import Enum

from .btu_validator import BTUValidator, validate_air_conditioner_match
from .model_validator import ModelValidator, validate_air_conditioner_models

logger = logging.getLogger(__name__)

class MatchingStrictness(Enum):
    """Matching strictness levels."""
    VERY_STRICT = "very_strict"
    STRICT = "strict"
    MODERATE = "moderate"
    LENIENT = "lenient"

@dataclass
class CategoryRules:
    """Rules and thresholds for a specific product category."""
    minimum_confidence: float
    btu_tolerance: Optional[float] = None
    model_exact_match: bool = False
    brand_weight: float = 0.5
    spec_weight: float = 0.5
    name_weight: float = 0.4
    strictness: MatchingStrictness = MatchingStrictness.MODERATE
    required_validations: List[str] = None
    forbidden_mismatches: List[str] = None
    
    def __post_init__(self):
        if self.required_validations is None:
            self.required_validations = []
        if self.forbidden_mismatches is None:
            self.forbidden_mismatches = []

class CategoryMatchingEngine:
    """
    Engine for applying category-specific matching rules and validations.
    """
    
    # Category-specific rules configuration
    CATEGORY_RULES = {
        'air_conditioner': CategoryRules(
            minimum_confidence=0.90,
            btu_tolerance=0.05,  # 5% BTU tolerance
            model_exact_match=True,
            brand_weight=0.3,
            spec_weight=0.7,
            name_weight=0.4,
            strictness=MatchingStrictness.VERY_STRICT,
            required_validations=['btu_match', 'model_series_match'],
            forbidden_mismatches=['btu_mismatch', 'model_series_mismatch', 'category_mismatch']
        ),
        
        'electronics': CategoryRules(
            minimum_confidence=0.85,
            model_exact_match=True,
            brand_weight=0.4,
            spec_weight=0.6,
            name_weight=0.5,
            strictness=MatchingStrictness.STRICT,
            required_validations=['model_match'],
            forbidden_mismatches=['model_series_mismatch', 'category_mismatch']
        ),
        
        'appliances': CategoryRules(
            minimum_confidence=0.80,
            brand_weight=0.4,
            spec_weight=0.5,
            name_weight=0.5,
            strictness=MatchingStrictness.STRICT,
            required_validations=['brand_match'],
            forbidden_mismatches=['category_mismatch']
        ),
        
        'tools': CategoryRules(
            minimum_confidence=0.75,
            brand_weight=0.3,
            spec_weight=0.4,
            name_weight=0.6,
            strictness=MatchingStrictness.MODERATE,
            required_validations=['brand_match'],
            forbidden_mismatches=['category_mismatch']
        ),
        
        'furniture': CategoryRules(
            minimum_confidence=0.70,
            brand_weight=0.2,
            spec_weight=0.3,
            name_weight=0.7,
            strictness=MatchingStrictness.LENIENT,
            required_validations=[],
            forbidden_mismatches=['category_mismatch']
        ),
        
        'default': CategoryRules(
            minimum_confidence=0.70,
            brand_weight=0.5,
            spec_weight=0.5,
            name_weight=0.5,
            strictness=MatchingStrictness.MODERATE,
            required_validations=[],
            forbidden_mismatches=['category_mismatch']
        )
    }
    
    # Category mappings for normalization
    CATEGORY_MAPPINGS = {
        'air_conditioner': ['air_conditioner', 'air-conditioner', 'ac', 'aircon'],
        'electronics': ['electronics', 'electronic', 'gadget', 'device'],
        'appliances': ['appliances', 'appliance', 'home_appliance'],
        'tools': ['tools', 'tool', 'power_tools', 'hand_tools'],
        'furniture': ['furniture', 'home_furniture', 'office_furniture'],
        'television': ['television', 'tv', 'smart_tv']  # Often misclassified air conditioners
    }
    
    def __init__(self):
        """Initialize the category matching engine."""
        self.btu_validator = BTUValidator()
        self.model_validator = ModelValidator(strict_series_matching=True)
        
    def get_normalized_category(self, category: str) -> str:
        """
        Normalize category name to standard form.
        
        Args:
            category: Raw category string
            
        Returns:
            Normalized category name
        """
        if not category:
            return 'default'
            
        category_lower = category.lower().strip()
        
        for normalized_cat, variations in self.CATEGORY_MAPPINGS.items():
            if category_lower in variations:
                return normalized_cat
                
        return 'default'
    
    def get_category_rules(self, category: str) -> CategoryRules:
        """
        Get matching rules for a specific category.
        
        Args:
            category: Product category
            
        Returns:
            CategoryRules object
        """
        normalized_cat = self.get_normalized_category(category)
        return self.CATEGORY_RULES.get(normalized_cat, self.CATEGORY_RULES['default'])
    
    def validate_category_match(self, product1: Dict[str, Any], product2: Dict[str, Any]) -> Tuple[bool, str, Dict[str, Any]]:
        """
        Validate if two products can be matched based on their categories.
        
        Args:
            product1: First product dictionary
            product2: Second product dictionary
            
        Returns:
            Tuple of (is_valid, reason, details)
        """
        cat1 = self.get_normalized_category(product1.get('category', ''))
        cat2 = self.get_normalized_category(product2.get('category', ''))
        
        details = {
            'category1': cat1,
            'category2': cat2,
            'original_cat1': product1.get('category'),
            'original_cat2': product2.get('category')
        }
        
        # Special case: Handle misclassified air conditioners in 'television' category
        if self._is_misclassified_air_conditioner(product1) or self._is_misclassified_air_conditioner(product2):
            logger.warning("Detected possible misclassified air conditioner in television category")
            # Treat as air conditioner for validation
            cat1 = 'air_conditioner' if self._is_misclassified_air_conditioner(product1) else cat1
            cat2 = 'air_conditioner' if self._is_misclassified_air_conditioner(product2) else cat2
            details['corrected_cat1'] = cat1
            details['corrected_cat2'] = cat2
        
        # Categories must match for strict validation
        if cat1 != cat2:
            # Some categories are compatible
            if self._are_compatible_categories(cat1, cat2):
                return True, f"Compatible categories: {cat1} and {cat2}", details
            else:
                return False, f"Incompatible categories: {cat1} vs {cat2}", details
                
        return True, f"Same category: {cat1}", details
    
    def apply_category_validations(self, product1: Dict[str, Any], product2: Dict[str, Any]) -> Tuple[bool, str, Dict[str, Any]]:
        """
        Apply category-specific validation rules.
        
        Args:
            product1: First product dictionary
            product2: Second product dictionary
            
        Returns:
            Tuple of (is_valid, reason, validation_details)
        """
        # First validate category compatibility
        cat_valid, cat_reason, cat_details = self.validate_category_match(product1, product2)
        if not cat_valid:
            return False, cat_reason, {'category_validation': cat_details}
            
        # Get the primary category for rule selection
        category = cat_details.get('corrected_cat1', cat_details['category1'])
        rules = self.get_category_rules(category)
        
        validation_results = {
            'category': category,
            'rules_applied': rules,
            'validations': {},
            'category_validation': cat_details
        }
        
        # Apply required validations based on category
        for validation in rules.required_validations:
            is_valid, reason, details = self._apply_specific_validation(
                validation, product1, product2, rules
            )
            
            validation_results['validations'][validation] = {
                'is_valid': is_valid,
                'reason': reason,
                'details': details
            }
            
            if not is_valid:
                logger.info(f"Category validation failed: {validation} - {reason}")
                return False, f"{validation}: {reason}", validation_results
                
        # Check for forbidden mismatches
        for forbidden in rules.forbidden_mismatches:
            is_violation, reason, details = self._check_forbidden_mismatch(
                forbidden, product1, product2, rules
            )
            
            if is_violation:
                validation_results['validations'][f"forbidden_{forbidden}"] = {
                    'is_violation': True,
                    'reason': reason,
                    'details': details
                }
                logger.info(f"Forbidden mismatch detected: {forbidden} - {reason}")
                return False, f"Forbidden {forbidden}: {reason}", validation_results
                
        return True, f"All category validations passed for {category}", validation_results
    
    def calculate_category_confidence(self, product1: Dict[str, Any], product2: Dict[str, Any], 
                                    base_confidence: float) -> Tuple[float, Dict[str, Any]]:
        """
        Calculate category-adjusted confidence score.
        
        Args:
            product1: First product dictionary
            product2: Second product dictionary
            base_confidence: Base confidence score from matching algorithm
            
        Returns:
            Tuple of (adjusted_confidence, adjustment_details)
        """
        category = self.get_normalized_category(product1.get('category', ''))
        rules = self.get_category_rules(category)
        
        adjustments = {
            'base_confidence': base_confidence,
            'category': category,
            'rules': rules,
            'adjustments': {}
        }
        
        adjusted_confidence = base_confidence
        
        # Apply category-specific minimum threshold
        if adjusted_confidence < rules.minimum_confidence:
            adjustments['adjustments']['minimum_threshold'] = {
                'applied': True,
                'threshold': rules.minimum_confidence,
                'original': adjusted_confidence,
                'result': 0.0
            }
            return 0.0, adjustments
            
        # BTU matching bonus for air conditioners
        if category == 'air_conditioner':
            btu_valid, btu_reason, btu_details = self.btu_validator.validate_btu_match(product1, product2)
            if btu_valid and btu_details.get('variance_percentage', 100) < 2:  # < 2% variance
                bonus = 0.05  # 5% bonus for very close BTU match
                adjusted_confidence = min(1.0, adjusted_confidence + bonus)
                adjustments['adjustments']['btu_bonus'] = {
                    'applied': True,
                    'bonus': bonus,
                    'reason': 'Very close BTU match (<2% variance)'
                }
                
        # Model matching bonus for technical products
        if category in ['air_conditioner', 'electronics']:
            model_valid, model_reason, model_details = self.model_validator.validate_model_match(product1, product2)
            if model_valid and 'exact model match' in model_reason.lower():
                bonus = 0.03  # 3% bonus for exact model match
                adjusted_confidence = min(1.0, adjusted_confidence + bonus)
                adjustments['adjustments']['model_bonus'] = {
                    'applied': True,
                    'bonus': bonus,
                    'reason': 'Exact model number match'
                }
                
        adjustments['final_confidence'] = adjusted_confidence
        return adjusted_confidence, adjustments
    
    def _apply_specific_validation(self, validation: str, product1: Dict[str, Any], 
                                 product2: Dict[str, Any], rules: CategoryRules) -> Tuple[bool, str, Dict[str, Any]]:
        """Apply a specific validation rule."""
        if validation == 'btu_match':
            return self.btu_validator.validate_btu_match(product1, product2)
            
        elif validation == 'model_series_match':
            is_valid, reason, details = self.model_validator.validate_model_match(product1, product2)
            # For series match, we specifically check series compatibility
            if not is_valid and 'series mismatch' in reason.lower():
                return False, reason, details
            return True, reason, details
            
        elif validation == 'model_match':
            return self.model_validator.validate_model_match(product1, product2)
            
        elif validation == 'brand_match':
            brand1 = product1.get('brand', '').lower().strip()
            brand2 = product2.get('brand', '').lower().strip()
            if brand1 and brand2 and brand1 != brand2:
                return False, f"Brand mismatch: {brand1} vs {brand2}", {'brand1': brand1, 'brand2': brand2}
            return True, "Brand match valid", {'brand1': brand1, 'brand2': brand2}
            
        else:
            logger.warning(f"Unknown validation: {validation}")
            return True, f"Unknown validation {validation} - skipped", {}
    
    def _check_forbidden_mismatch(self, forbidden: str, product1: Dict[str, Any], 
                                product2: Dict[str, Any], rules: CategoryRules) -> Tuple[bool, str, Dict[str, Any]]:
        """Check for a forbidden mismatch."""
        if forbidden == 'btu_mismatch':
            is_valid, reason, details = self.btu_validator.validate_btu_match(product1, product2)
            if not is_valid:
                return True, reason, details
                
        elif forbidden == 'model_series_mismatch':
            is_valid, reason, details = self.model_validator.validate_model_match(product1, product2)
            if not is_valid and 'series mismatch' in reason.lower():
                return True, reason, details
                
        elif forbidden == 'category_mismatch':
            cat_valid, cat_reason, cat_details = self.validate_category_match(product1, product2)
            if not cat_valid:
                return True, cat_reason, cat_details
                
        return False, "No forbidden mismatch detected", {}
    
    def _is_misclassified_air_conditioner(self, product: Dict[str, Any]) -> bool:
        """Check if a product is an air conditioner misclassified as television."""
        category = product.get('category', '').lower()
        name = product.get('name', '').lower()
        
        # If categorized as television but has air conditioner indicators
        if 'television' in category or 'tv' in category:
            ac_indicators = ['แอร์', 'air conditioner', 'inverter', 'btu', 'บีทียู', 'carrier', 'daikin', 'haier']
            return any(indicator in name for indicator in ac_indicators)
            
        return False
    
    def _are_compatible_categories(self, cat1: str, cat2: str) -> bool:
        """Check if two categories are compatible for matching."""
        compatible_pairs = {
            ('electronics', 'appliances'),
            ('appliances', 'electronics'),
            ('tools', 'appliances'),
            ('appliances', 'tools')
        }
        
        return (cat1, cat2) in compatible_pairs
    
    def get_matching_recommendation(self, products: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Analyze products and provide matching recommendations.
        
        Args:
            products: List of product dictionaries
            
        Returns:
            Analysis and recommendations
        """
        categories = {}
        total_products = len(products)
        
        for product in products:
            category = self.get_normalized_category(product.get('category', ''))
            categories[category] = categories.get(category, 0) + 1
            
        # Analyze category distribution
        dominant_category = max(categories.items(), key=lambda x: x[1])[0] if categories else 'default'
        category_diversity = len(categories)
        
        # Get rules for dominant category
        rules = self.get_category_rules(dominant_category)
        
        recommendation = {
            'total_products': total_products,
            'categories': categories,
            'dominant_category': dominant_category,
            'category_diversity': category_diversity,
            'recommended_rules': rules,
            'analysis': self._generate_matching_analysis(categories, dominant_category, rules)
        }
        
        return recommendation
    
    def _generate_matching_analysis(self, categories: Dict[str, int], 
                                  dominant_category: str, rules: CategoryRules) -> str:
        """Generate textual analysis of matching situation."""
        total = sum(categories.values())
        dominant_percentage = (categories.get(dominant_category, 0) / total) * 100
        
        if len(categories) == 1:
            return f"All products are {dominant_category} - use {rules.strictness.value} matching rules"
        elif dominant_percentage >= 80:
            return f"Mostly {dominant_category} ({dominant_percentage:.1f}%) - apply {rules.strictness.value} rules with category validation"
        elif len(categories) <= 3:
            return "Moderate category diversity - use category-specific validation for each pair"
        else:
            return "High category diversity - implement strict category matching to prevent false positives"


# Convenience functions
def validate_products_by_category(product1: Dict[str, Any], product2: Dict[str, Any]) -> Tuple[bool, str]:
    """
    Quick category-based validation for two products.
    
    Args:
        product1: First product
        product2: Second product
        
    Returns:
        Tuple of (is_valid, reason)
    """
    engine = CategoryMatchingEngine()
    is_valid, reason, _ = engine.apply_category_validations(product1, product2)
    return is_valid, reason

def get_category_confidence_threshold(category: str) -> float:
    """
    Get minimum confidence threshold for a category.
    
    Args:
        category: Product category
        
    Returns:
        Minimum confidence threshold
    """
    engine = CategoryMatchingEngine()
    rules = engine.get_category_rules(category)
    return rules.minimum_confidence


if __name__ == "__main__":
    # Test the category matching engine
    engine = CategoryMatchingEngine()
    
    # Test products
    test_products = [
        {
            'name': 'แอร์ผนัง CARRIER 42TVDA028A 25200 บีทียู อินเวอร์เตอร์',
            'brand': 'CARRIER',
            'category': 'air_conditioner'
        },
        {
            'name': 'CARRIER Wi-Fi Inverter Air Conditioner (38TVEA028A42TVEA028A), 25,200 BTU',
            'brand': 'CARRIER',
            'category': 'air_conditioner'
        },
        {
            'name': 'แอร์ผนัง DAIKIN FTKZ24YV2S 24200 บีทียู อินเวอร์เตอร์',
            'brand': 'DAIKIN',
            'category': 'air_conditioner'
        },
        {
            'name': 'อุปกรณ์ซัพพอร์ต ฟูทูโร่ พยุงข้อเท้า ไซส์ L',
            'brand': 'FUTURO',
            'category': 'medical_equipment'
        }
    ]
    
    print("Category Matching Engine Test Results:")
    print("=" * 60)
    
    # Test category validation
    print("Category Validation Tests:")
    print("-" * 40)
    
    # Should pass (same category, same series would need BTU check)
    is_valid, reason, details = engine.apply_category_validations(test_products[0], test_products[2])
    print(f"CARRIER vs DAIKIN (both air_conditioner): {is_valid}")
    print(f"Reason: {reason}")
    print()
    
    # Should fail (different categories)
    is_valid, reason, details = engine.apply_category_validations(test_products[0], test_products[3])
    print(f"CARRIER air conditioner vs FUTURO ankle support: {is_valid}")
    print(f"Reason: {reason}")
    print()
    
    # Should fail (different model series)
    is_valid, reason, details = engine.apply_category_validations(test_products[0], test_products[1])
    print(f"CARRIER TVDA vs TVEA series: {is_valid}")
    print(f"Reason: {reason}")
    print()
    
    # Test recommendation system
    print("Matching Recommendations:")
    print("-" * 30)
    recommendation = engine.get_matching_recommendation(test_products)
    print(f"Dominant category: {recommendation['dominant_category']}")
    print(f"Category distribution: {recommendation['categories']}")
    print(f"Analysis: {recommendation['analysis']}")
    print()
    
    # Test confidence adjustment
    print("Confidence Adjustment Test:")
    print("-" * 30)
    base_confidence = 0.85
    adjusted_conf, adjustments = engine.calculate_category_confidence(
        test_products[0], test_products[2], base_confidence
    )
    print(f"Base confidence: {base_confidence}")
    print(f"Adjusted confidence: {adjusted_conf}")
    print(f"Category: {adjustments['category']}")
    print(f"Minimum threshold: {adjustments['rules'].minimum_confidence}")