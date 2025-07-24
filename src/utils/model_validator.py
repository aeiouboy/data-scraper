#!/usr/bin/env python3
"""
Model Number Validation System for Product Matching

This module provides comprehensive model number validation to prevent
false positive matches between different product models and series.
"""

import re
import logging
from typing import Optional, Tuple, List, Dict, Any, Set
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class ModelInfo:
    """Container for extracted model information."""
    full_model: Optional[str] = None
    series: Optional[str] = None
    variant: Optional[str] = None
    brand: Optional[str] = None
    features: List[str] = None
    
    def __post_init__(self):
        if self.features is None:
            self.features = []

class ModelValidator:
    """
    Validates model numbers for product matching.
    
    Prevents false positive matches between different product models,
    especially for technical products like air conditioners and electronics.
    """
    
    # Brand-specific model patterns
    BRAND_PATTERNS = {
        'CARRIER': {
            'patterns': [
                r'(\d{2}TV[A-Z]{2}\d{3}[A-Z]?)',  # 42TVDA028A, 38TVEA028A
                r'(\d{2}TS[A-Z]{2}\d{3}[A-Z]?)',  # 38TSAA018A
            ],
            'series_extractor': r'\d{2}(TV[A-Z]{2})\d{3}[A-Z]?',  # TVDA, TVEA
        },
        'DAIKIN': {
            'patterns': [
                r'(FT[A-Z]{1,2}\d{2}[A-Z]{2}\d[A-Z])',  # FTKZ24YV2S, FTM15PV2S
                r'(RT[A-Z]{1,2}\d{2}[A-Z]{2}\d[A-Z])',  # RT series
            ],
            'series_extractor': r'(FT[A-Z]{1,2})\d{2}[A-Z]{2}\d[A-Z]',  # FTK, FTM
        },
        'HAIER': {
            'patterns': [
                r'(HSU-\d{2}[A-Z]{4}\d{2}[A-Z]?)',  # HSU-24VRWA03T, HSU-13CQRD
                r'(HSU-\d{2}[A-Z]{3}\d{2})',        # HSU-24VRC03
            ],
            'series_extractor': r'HSU-\d{2}([A-Z]{3,4})\d{2}[A-Z]?',  # VRWA, CQRD
        },
        'COMFEE': {
            'patterns': [
                r'(CF-\d{2}[A-Z]{4}-[A-Z]\d)',  # CF-18VAGF-T2
            ],
            'series_extractor': r'CF-\d{2}([A-Z]{4})-[A-Z]\d',  # VAGF
        }
    }
    
    # Generic patterns for unknown brands
    GENERIC_PATTERNS = [
        r'([A-Z]{2,4}-?\d{2,4}[A-Z]{2,6}\d{0,3}[A-Z]?)',  # Generic alpha-numeric
        r'(\d{2}[A-Z]{3,5}\d{3}[A-Z]?)',                  # Numeric prefix
    ]
    
    # Features to extract from model names
    FEATURE_PATTERNS = {
        'wifi': r'Wi-?Fi',
        'inverter': r'Inverter?',
        'smart': r'Smart',
        'eco': r'Eco',
        'dual': r'Dual',
        'multi': r'Multi',
        'super': r'Super',
        'turbo': r'Turbo',
        'quiet': r'Quiet',
        'silent': r'Silent'
    }
    
    def __init__(self, strict_series_matching: bool = True):
        """
        Initialize model validator.
        
        Args:
            strict_series_matching: Whether to require exact series matching
        """
        self.strict_series_matching = strict_series_matching
        
    def extract_model_info(self, product_name: str, brand: Optional[str] = None) -> ModelInfo:
        """
        Extract comprehensive model information from product name.
        
        Args:
            product_name: Product name string
            brand: Optional brand hint for better extraction
            
        Returns:
            ModelInfo object with extracted information
        """
        if not product_name:
            return ModelInfo()
            
        # Clean up the product name
        cleaned_name = self._clean_product_name(product_name)
        
        # Auto-detect brand if not provided
        if not brand:
            brand = self._detect_brand(cleaned_name)
            
        # Extract model number based on brand
        full_model = self._extract_model_number(cleaned_name, brand)
        
        # Extract series from model
        series = self._extract_series(full_model, brand) if full_model else None
        
        # Extract variant info
        variant = self._extract_variant(full_model, brand) if full_model else None
        
        # Extract features
        features = self._extract_features(cleaned_name)
        
        model_info = ModelInfo(
            full_model=full_model,
            series=series,
            variant=variant,
            brand=brand,
            features=features
        )
        
        logger.debug(f"Extracted model info from '{product_name[:50]}...': {model_info}")
        return model_info
    
    def validate_model_match(self, product1: Dict[str, Any], product2: Dict[str, Any]) -> Tuple[bool, str, Dict[str, Any]]:
        """
        Validate if two products have compatible model numbers.
        
        Args:
            product1: First product dictionary
            product2: Second product dictionary
            
        Returns:
            Tuple of (is_valid, reason, details)
        """
        # Extract model info for both products
        model1 = self.extract_model_info(
            product1.get('name', ''), 
            product1.get('brand')
        )
        model2 = self.extract_model_info(
            product2.get('name', ''), 
            product2.get('brand')
        )
        
        details = {
            'model1': model1,
            'model2': model2,
            'strict_series_matching': self.strict_series_matching
        }
        
        # If no models found, cannot validate (allow match)
        if not model1.full_model and not model2.full_model:
            return True, "No model numbers found in either product", details
            
        # If only one has model, treat as warning but allow
        if not model1.full_model or not model2.full_model:
            missing_model = "product1" if not model1.full_model else "product2"
            return True, f"Model number missing from {missing_model} - allowing match", details
            
        # Different brands should not match (with exceptions)
        if model1.brand and model2.brand and model1.brand != model2.brand:
            return False, f"Different brands: {model1.brand} vs {model2.brand}", details
            
        # Exact model match (best case)
        if model1.full_model == model2.full_model:
            return True, f"Exact model match: {model1.full_model}", details
            
        # Series validation (critical for air conditioners)
        if self.strict_series_matching and model1.series and model2.series:
            if model1.series != model2.series:
                reason = f"Model series mismatch: {model1.series} vs {model2.series}"
                logger.info(f"Model validation failed: {reason}")
                return False, reason, details
                
        # Variant within same series (acceptable)
        if model1.series == model2.series and model1.series:
            reason = f"Same series, different variants: {model1.full_model} vs {model2.full_model}"
            logger.debug(f"Model validation passed: {reason}")
            return True, reason, details
            
        # Similar models (fuzzy matching)
        similarity = self._calculate_model_similarity(model1.full_model, model2.full_model)
        if similarity >= 0.8:  # 80% similarity threshold
            reason = f"Similar models ({similarity*100:.1f}% similarity): {model1.full_model} vs {model2.full_model}"
            return True, reason, details
            
        # Different models
        reason = f"Different models: {model1.full_model} vs {model2.full_model}"
        logger.info(f"Model validation failed: {reason}")
        return False, reason, details
    
    def _clean_product_name(self, name: str) -> str:
        """Clean product name for better model extraction."""
        # Remove common noise words
        noise_words = ['แอร์ผนัง', 'แอร์ติดผนัง', 'Air Conditioner', 'Inverter', 'Wi-Fi', 'BTU', 'บีทียู']
        cleaned = name
        for word in noise_words:
            cleaned = re.sub(rf'\b{re.escape(word)}\b', ' ', cleaned, flags=re.IGNORECASE)
        
        # Clean up whitespace
        cleaned = re.sub(r'\s+', ' ', cleaned).strip()
        return cleaned
    
    def _detect_brand(self, name: str) -> Optional[str]:
        """Auto-detect brand from product name."""
        name_upper = name.upper()
        for brand in self.BRAND_PATTERNS.keys():
            if brand in name_upper:
                return brand
        return None
    
    def _extract_model_number(self, name: str, brand: Optional[str]) -> Optional[str]:
        """Extract model number using brand-specific or generic patterns."""
        if brand and brand in self.BRAND_PATTERNS:
            patterns = self.BRAND_PATTERNS[brand]['patterns']
            for pattern in patterns:
                match = re.search(pattern, name, re.IGNORECASE)
                if match:
                    return match.group(1).upper()
                    
        # Try generic patterns
        for pattern in self.GENERIC_PATTERNS:
            match = re.search(pattern, name, re.IGNORECASE)
            if match:
                return match.group(1).upper()
                
        return None
    
    def _extract_series(self, model: str, brand: Optional[str]) -> Optional[str]:
        """Extract series identifier from model number."""
        if not model or not brand or brand not in self.BRAND_PATTERNS:
            return None
            
        series_pattern = self.BRAND_PATTERNS[brand].get('series_extractor')
        if series_pattern:
            match = re.search(series_pattern, model)
            if match:
                return match.group(1)
                
        return None
    
    def _extract_variant(self, model: str, brand: Optional[str]) -> Optional[str]:
        """Extract variant information from model number."""
        if not model:
            return None
            
        # For most brands, variant is the suffix after series
        if brand == 'CARRIER':
            # For CARRIER: 42TVDA028A -> variant is 028A
            match = re.search(r'TV[A-Z]{2}(\d{3}[A-Z]?)', model)
            return match.group(1) if match else None
        elif brand == 'DAIKIN':
            # For DAIKIN: FTKZ24YV2S -> variant is 24YV2S
            match = re.search(r'FT[A-Z]{1,2}(\d{2}[A-Z]{2}\d[A-Z])', model)
            return match.group(1) if match else None
        elif brand == 'HAIER':
            # For HAIER: HSU-24VRWA03T -> variant is 24...03T
            match = re.search(r'HSU-(\d{2}[A-Z]{3,4}\d{2}[A-Z]?)', model)
            return match.group(1) if match else None
            
        return None
    
    def _extract_features(self, name: str) -> List[str]:
        """Extract feature keywords from product name."""
        features = []
        for feature, pattern in self.FEATURE_PATTERNS.items():
            if re.search(pattern, name, re.IGNORECASE):
                features.append(feature)
        return features
    
    def _calculate_model_similarity(self, model1: str, model2: str) -> float:
        """Calculate similarity between two model numbers."""
        if not model1 or not model2:
            return 0.0
            
        # Simple character-based similarity
        len1, len2 = len(model1), len(model2)
        max_len = max(len1, len2)
        
        if max_len == 0:
            return 1.0
            
        # Count matching characters in same positions
        matches = sum(c1 == c2 for c1, c2 in zip(model1, model2))
        return matches / max_len
    
    def analyze_model_distribution(self, products: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Analyze model distribution across a list of products.
        
        Args:
            products: List of product dictionaries
            
        Returns:
            Analysis results with statistics and recommendations
        """
        model_info_list = []
        brands = {}
        series = {}
        
        for product in products:
            model_info = self.extract_model_info(product.get('name', ''), product.get('brand'))
            model_info_list.append(model_info)
            
            if model_info.brand:
                brands[model_info.brand] = brands.get(model_info.brand, 0) + 1
                
            if model_info.series:
                series_key = f"{model_info.brand}_{model_info.series}"
                series[series_key] = series.get(series_key, 0) + 1
                
        analysis = {
            'total_products': len(products),
            'products_with_models': len([m for m in model_info_list if m.full_model]),
            'unique_brands': len(brands),
            'unique_series': len(series),
            'brands': brands,
            'series': series,
            'recommendation': self._get_model_matching_recommendation(model_info_list)
        }
        
        return analysis
    
    def _get_model_matching_recommendation(self, model_info_list: List[ModelInfo]) -> str:
        """Generate recommendation based on model analysis."""
        models_with_data = [m for m in model_info_list if m.full_model]
        
        if len(models_with_data) < 2:
            return "Insufficient model data for analysis"
            
        # Check for series diversity
        series_set = {m.series for m in models_with_data if m.series}
        
        if len(series_set) <= 1:
            return "Models appear to be from same series - good for matching"
        elif len(series_set) <= 3:
            return "Moderate series diversity - review individual matches"
        else:
            return "High series diversity - likely contains false positive matches"


# Convenience functions
def validate_air_conditioner_models(product1: Dict[str, Any], product2: Dict[str, Any]) -> Tuple[bool, str]:
    """
    Quick model validation for air conditioners with strict series matching.
    
    Args:
        product1: First product
        product2: Second product
        
    Returns:
        Tuple of (is_valid, reason)
    """
    validator = ModelValidator(strict_series_matching=True)
    is_valid, reason, _ = validator.validate_model_match(product1, product2)
    return is_valid, reason

def extract_model_series(product_name: str, brand: Optional[str] = None) -> Optional[str]:
    """
    Extract model series from product name.
    
    Args:
        product_name: Product name
        brand: Optional brand hint
        
    Returns:
        Model series or None
    """
    validator = ModelValidator()
    model_info = validator.extract_model_info(product_name, brand)
    return model_info.series


if __name__ == "__main__":
    # Test the model validator
    validator = ModelValidator(strict_series_matching=True)
    
    # Test products
    test_products = [
        {'name': 'แอร์ผนัง CARRIER 42TVDA028A 25200 บีทียู อินเวอร์เตอร์', 'brand': 'CARRIER'},
        {'name': 'CARRIER Wi-Fi Inverter Air Conditioner (38TVEA028A42TVEA028A), 25,200 BTU', 'brand': 'CARRIER'},
        {'name': 'แอร์ผนัง DAIKIN FTKZ24YV2S 24200 บีทียู อินเวอร์เตอร์', 'brand': 'DAIKIN'},
        {'name': 'แอร์ติดผนัง Inverter 24,200 BTU Wi-Fi DAIKIN รุ่น FTKZ24YV2S', 'brand': 'DAIKIN'},
        {'name': 'แอร์ผนัง HAIER HSU-24VRWA03T 24000 บีทียู อินเวอร์เตอร์', 'brand': 'HAIER'},
        {'name': 'แอร์ติดผนัง Inveter 23,200 BTU HAIER รุ่น HSU-24VQRC03T', 'brand': 'HAIER'}
    ]
    
    print("Model Validator Test Results:")
    print("=" * 60)
    
    # Test model extraction
    for product in test_products:
        model_info = validator.extract_model_info(product['name'], product.get('brand'))
        print(f"Product: {product['name'][:50]}...")
        print(f"Model: {model_info.full_model}, Series: {model_info.series}, Brand: {model_info.brand}")
        print(f"Features: {model_info.features}")
        print()
    
    # Test matching validation
    print("Model Matching Validation Tests:")
    print("-" * 40)
    
    # Should pass (same model, same series)
    is_valid, reason, _ = validator.validate_model_match(test_products[2], test_products[3])
    print(f"DAIKIN FTKZ24YV2S vs FTKZ24YV2S: {is_valid} - {reason}")
    
    # Should fail (different series: TVDA vs TVEA)
    is_valid, reason, _ = validator.validate_model_match(test_products[0], test_products[1])
    print(f"CARRIER 42TVDA028A vs 38TVEA028A: {is_valid} - {reason}")
    
    # Should fail (different models: VRWA vs VQRC)
    is_valid, reason, _ = validator.validate_model_match(test_products[4], test_products[5])
    print(f"HAIER HSU-24VRWA03T vs HSU-24VQRC03T: {is_valid} - {reason}")
    
    # Analysis
    print("\nModel Distribution Analysis:")
    print("-" * 30)
    analysis = validator.analyze_model_distribution(test_products)
    print(f"Products with models: {analysis['products_with_models']}/{analysis['total_products']}")
    print(f"Brands: {analysis['brands']}")
    print(f"Series: {analysis['series']}")
    print(f"Recommendation: {analysis['recommendation']}")