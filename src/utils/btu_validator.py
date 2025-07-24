#!/usr/bin/env python3
"""
BTU Validation System for Product Matching

This module provides comprehensive BTU validation for air conditioners
to prevent false positive matches between products with different capacities.
"""

import re
import logging
from typing import Optional, Tuple, List, Dict, Any

logger = logging.getLogger(__name__)

class BTUValidator:
    """
    Validates BTU values for air conditioner product matching.
    
    Prevents false positive matches between air conditioners with
    significantly different BTU ratings.
    """
    
    # BTU extraction patterns for both English and Thai
    BTU_PATTERNS = [
        # English patterns
        r'(\d{1,2}[,.]?\d{3})\s*BTU',  # 24,200 BTU, 24.200 BTU
        r'(\d{4,5})\s*BTU',            # 24200 BTU
        
        # Thai patterns  
        r'(\d{1,2}[,.]?\d{3})\s*บีทียู',  # 24,200 บีทียู
        r'(\d{4,5})\s*บีทียู',            # 24200 บีทียู
        
        # Mixed patterns in product descriptions
        r'(\d{1,2}[,.]?\d{3})\s*(?:BTU|บีทียู)',
        r'(\d{4,5})\s*(?:BTU|บีทียู)',
    ]
    
    # Standard BTU ranges for air conditioners
    STANDARD_BTU_RANGES = {
        'small': (6000, 12000),      # Small rooms
        'medium': (12001, 18000),    # Medium rooms  
        'large': (18001, 24000),     # Large rooms
        'extra_large': (24001, 36000) # Extra large rooms
    }
    
    def __init__(self, tolerance: float = 0.05):
        """
        Initialize BTU validator.
        
        Args:
            tolerance: Maximum allowed BTU difference as percentage (default 5%)
        """
        self.tolerance = tolerance
        
    def extract_btu(self, text: str) -> Optional[int]:
        """
        Extract BTU value from product name or description.
        
        Args:
            text: Product name or description text
            
        Returns:
            BTU value as integer, or None if not found
        """
        if not text:
            return None
            
        text_upper = text.upper()
        
        for pattern in self.BTU_PATTERNS:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                btu_str = match.group(1).replace(',', '').replace('.', '')
                try:
                    btu_value = int(btu_str)
                    
                    # Validate BTU range (reasonable for air conditioners)
                    if 5000 <= btu_value <= 50000:
                        logger.debug(f"Extracted BTU: {btu_value} from '{text[:50]}...'")
                        return btu_value
                    else:
                        logger.warning(f"BTU value {btu_value} outside valid range (5000-50000)")
                        
                except ValueError:
                    logger.warning(f"Could not parse BTU value: {btu_str}")
                    continue
                    
        logger.debug(f"No BTU found in: '{text[:50]}...'")
        return None
    
    def validate_btu_match(self, product1: Dict[str, Any], product2: Dict[str, Any]) -> Tuple[bool, str, Dict[str, Any]]:
        """
        Validate if two products have compatible BTU values.
        
        Args:
            product1: First product dictionary with 'name' field
            product2: Second product dictionary with 'name' field
            
        Returns:
            Tuple of (is_valid, reason, details)
        """
        # Extract BTU values
        btu1 = self.extract_btu(product1.get('name', ''))
        btu2 = self.extract_btu(product2.get('name', ''))
        
        details = {
            'btu1': btu1,
            'btu2': btu2,
            'tolerance_used': self.tolerance,
            'variance_percentage': None,
            'category1': product1.get('category', 'unknown'),
            'category2': product2.get('category', 'unknown')
        }
        
        # If both products don't have BTU values, cannot validate
        if btu1 is None and btu2 is None:
            return True, "No BTU values found in either product", details
            
        # If only one has BTU, treat as incompatible for air conditioners
        if btu1 is None or btu2 is None:
            missing_btu = "product1" if btu1 is None else "product2"
            return False, f"BTU missing from {missing_btu}", details
            
        # Calculate variance
        min_btu = min(btu1, btu2)
        max_btu = max(btu1, btu2)
        variance = (max_btu - min_btu) / min_btu if min_btu > 0 else 0
        details['variance_percentage'] = variance * 100
        
        # Check if variance exceeds tolerance
        if variance > self.tolerance:
            reason = f"BTU mismatch: {btu1} vs {btu2} ({variance*100:.1f}% difference, max {self.tolerance*100:.1f}%)"
            logger.info(f"BTU validation failed: {reason}")
            return False, reason, details
            
        # Valid match
        reason = f"BTU match valid: {btu1} vs {btu2} ({variance*100:.1f}% difference)"
        logger.debug(f"BTU validation passed: {reason}")
        return True, reason, details
    
    def get_btu_category(self, btu: int) -> str:
        """
        Categorize BTU value into standard ranges.
        
        Args:
            btu: BTU value
            
        Returns:
            Category name (small, medium, large, extra_large)
        """
        for category, (min_btu, max_btu) in self.STANDARD_BTU_RANGES.items():
            if min_btu <= btu <= max_btu:
                return category
        return 'unknown'
    
    def validate_category_compatibility(self, btu1: int, btu2: int) -> bool:
        """
        Check if two BTU values are in compatible categories.
        
        Args:
            btu1: First BTU value
            btu2: Second BTU value
            
        Returns:
            True if categories are compatible
        """
        cat1 = self.get_btu_category(btu1)
        cat2 = self.get_btu_category(btu2)
        
        # Same category is always compatible
        if cat1 == cat2:
            return True
            
        # Adjacent categories might be compatible with strict validation
        adjacent_pairs = [
            ('small', 'medium'),
            ('medium', 'large'),
            ('large', 'extra_large')
        ]
        
        for pair in adjacent_pairs:
            if (cat1, cat2) in [pair, pair[::-1]]:
                # Use stricter tolerance for adjacent categories
                variance = abs(btu1 - btu2) / min(btu1, btu2)
                return variance <= self.tolerance / 2  # Half tolerance for adjacent
                
        return False
    
    def analyze_btu_distribution(self, products: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Analyze BTU distribution across a list of products.
        
        Args:
            products: List of product dictionaries
            
        Returns:
            Analysis results with statistics and recommendations
        """
        btu_values = []
        categories = {}
        
        for product in products:
            btu = self.extract_btu(product.get('name', ''))
            if btu:
                btu_values.append(btu)
                category = self.get_btu_category(btu)
                categories[category] = categories.get(category, 0) + 1
                
        if not btu_values:
            return {
                'total_products': len(products),
                'products_with_btu': 0,
                'analysis': 'No BTU values found'
            }
            
        analysis = {
            'total_products': len(products),
            'products_with_btu': len(btu_values),
            'min_btu': min(btu_values),
            'max_btu': max(btu_values),
            'avg_btu': sum(btu_values) / len(btu_values),
            'btu_variance': (max(btu_values) - min(btu_values)) / min(btu_values) * 100,
            'categories': categories,
            'recommendation': self._get_matching_recommendation(btu_values)
        }
        
        return analysis
    
    def _get_matching_recommendation(self, btu_values: List[int]) -> str:
        """
        Provide recommendation based on BTU distribution.
        
        Args:
            btu_values: List of BTU values
            
        Returns:
            Recommendation string
        """
        if len(btu_values) < 2:
            return "Insufficient data for recommendation"
            
        min_btu = min(btu_values)
        max_btu = max(btu_values)
        variance = (max_btu - min_btu) / min_btu * 100
        
        if variance <= self.tolerance * 100:
            return "BTU values are compatible for matching"
        elif variance <= 30:
            return "BTU values have moderate variance - review individual matches"
        else:
            return "BTU values have high variance - likely false positive matches"


# Convenience functions for direct use
def validate_air_conditioner_match(product1: Dict[str, Any], product2: Dict[str, Any], 
                                  tolerance: float = 0.05) -> Tuple[bool, str]:
    """
    Quick validation for air conditioner BTU compatibility.
    
    Args:
        product1: First product
        product2: Second product  
        tolerance: BTU tolerance (default 5%)
        
    Returns:
        Tuple of (is_valid, reason)
    """
    validator = BTUValidator(tolerance=tolerance)
    is_valid, reason, _ = validator.validate_btu_match(product1, product2)
    return is_valid, reason

def extract_product_btu(product_name: str) -> Optional[int]:
    """
    Extract BTU from product name.
    
    Args:
        product_name: Product name string
        
    Returns:
        BTU value or None
    """
    validator = BTUValidator()
    return validator.extract_btu(product_name)


if __name__ == "__main__":
    # Test the BTU validator
    validator = BTUValidator(tolerance=0.05)
    
    # Test cases
    test_products = [
        {'name': 'แอร์ผนัง DAIKIN FTKZ24YV2S 24200 บีทียู อินเวอร์เตอร์', 'category': 'air_conditioner'},
        {'name': 'แอร์ติดผนัง Inverter 24,200 BTU Wi-Fi DAIKIN รุ่น FTKZ24YV2S', 'category': 'air_conditioner'},
        {'name': 'แอร์ผนัง CARRIER 42TVAB013ABI 12200 บีทียู อินเวอร์เตอร์', 'category': 'air_conditioner'},
        {'name': 'CARRIER Wi-Fi Inverter Air Conditioner (38TVEA028A42TVEA028A), 25,200 BTU', 'category': 'air_conditioner'}
    ]
    
    print("BTU Validator Test Results:")
    print("=" * 50)
    
    # Test BTU extraction
    for product in test_products:
        btu = validator.extract_btu(product['name'])
        print(f"Product: {product['name'][:50]}...")
        print(f"BTU: {btu}")
        print()
    
    # Test matching validation
    print("Matching Validation Tests:")
    print("-" * 30)
    
    # Should pass (same BTU)
    is_valid, reason, details = validator.validate_btu_match(test_products[0], test_products[1])
    print(f"DAIKIN 24,200 vs DAIKIN 24,200: {is_valid} - {reason}")
    
    # Should fail (different BTU)
    is_valid, reason, details = validator.validate_btu_match(test_products[0], test_products[2])
    print(f"DAIKIN 24,200 vs CARRIER 12,200: {is_valid} - {reason}")
    
    # Should fail (51% variance)
    is_valid, reason, details = validator.validate_btu_match(test_products[2], test_products[3])
    print(f"CARRIER 12,200 vs CARRIER 25,200: {is_valid} - {reason}")