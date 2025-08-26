"""
Confidence scoring algorithms for product matching
Calculates weighted confidence scores based on multiple matching criteria
"""
import logging
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class MatchingCriteria(str, Enum):
    """Enumeration of matching criteria"""
    NAME_SIMILARITY = "name_similarity"
    BRAND_MATCH = "brand_match"
    SKU_SIMILARITY = "sku_similarity" 
    SPECIFICATION_MATCH = "specification_match"
    PRICE_PROXIMITY = "price_proximity"
    CATEGORY_MATCH = "category_match"
    RETAILER_DIVERSITY = "retailer_diversity"


@dataclass
class MatchingWeights:
    """Weight configuration for different matching criteria"""
    name_similarity: float = 0.35
    brand_match: float = 0.25
    sku_similarity: float = 0.15
    specification_match: float = 0.15
    price_proximity: float = 0.05
    category_match: float = 0.03
    retailer_diversity: float = 0.02
    
    def __post_init__(self):
        """Validate weights sum to 1.0"""
        total = (self.name_similarity + self.brand_match + self.sku_similarity + 
                self.specification_match + self.price_proximity + 
                self.category_match + self.retailer_diversity)
        
        if abs(total - 1.0) > 0.01:
            raise ValueError(f"Weights must sum to 1.0, got {total}")


@dataclass
class ScoreComponents:
    """Individual score components for transparency"""
    name_similarity: float = 0.0
    brand_match: float = 0.0
    sku_similarity: float = 0.0
    specification_match: float = 0.0
    price_proximity: float = 0.0
    category_match: float = 0.0
    retailer_diversity: float = 0.0
    
    def to_dict(self) -> Dict[str, float]:
        return {
            'name_similarity': self.name_similarity,
            'brand_match': self.brand_match,
            'sku_similarity': self.sku_similarity,
            'specification_match': self.specification_match,
            'price_proximity': self.price_proximity,
            'category_match': self.category_match,
            'retailer_diversity': self.retailer_diversity
        }


class ConfidenceScorer:
    """Confidence scoring system for product matches"""
    
    def __init__(self, weights: Optional[MatchingWeights] = None):
        self.weights = weights or MatchingWeights()
        
    def calculate_confidence(
        self,
        scores: ScoreComponents,
        adjustments: Optional[Dict[str, float]] = None
    ) -> Tuple[float, Dict[str, Any]]:
        """
        Calculate weighted confidence score
        
        Args:
            scores: Individual score components
            adjustments: Optional score adjustments
        
        Returns:
            Tuple of (confidence_score, calculation_metadata)
        """
        try:
            # Calculate base weighted score
            weighted_score = (
                scores.name_similarity * self.weights.name_similarity +
                scores.brand_match * self.weights.brand_match +
                scores.sku_similarity * self.weights.sku_similarity +
                scores.specification_match * self.weights.specification_match +
                scores.price_proximity * self.weights.price_proximity +
                scores.category_match * self.weights.category_match +
                scores.retailer_diversity * self.weights.retailer_diversity
            )
            
            # Apply adjustments if provided
            final_score = weighted_score
            adjustment_total = 0.0
            
            if adjustments:
                for adjustment_name, adjustment_value in adjustments.items():
                    final_score += adjustment_value
                    adjustment_total += adjustment_value
            
            # Clamp to [0, 1] range
            final_score = max(0.0, min(1.0, final_score))
            
            # Create metadata for transparency
            metadata = {
                'base_scores': scores.to_dict(),
                'weights': {
                    'name_similarity': self.weights.name_similarity,
                    'brand_match': self.weights.brand_match,
                    'sku_similarity': self.weights.sku_similarity,
                    'specification_match': self.weights.specification_match,
                    'price_proximity': self.weights.price_proximity,
                    'category_match': self.weights.category_match,
                    'retailer_diversity': self.weights.retailer_diversity
                },
                'weighted_score': weighted_score,
                'adjustments': adjustments or {},
                'adjustment_total': adjustment_total,
                'final_score': final_score,
                'calculation_method': 'weighted_sum_with_adjustments'
            }
            
            return final_score, metadata
            
        except Exception as e:
            logger.error(f"Error calculating confidence score: {e}")
            return 0.0, {'error': str(e)}
    
    def calculate_name_similarity_score(
        self,
        name1: str,
        name2: str,
        normalized_name1: str,
        normalized_name2: str,
        similarity_ratio: float,
        token_match_ratio: float
    ) -> float:
        """
        Calculate name similarity score with multiple factors
        
        Args:
            name1, name2: Original names
            normalized_name1, normalized_name2: Normalized versions
            similarity_ratio: String similarity ratio (0-1)
            token_match_ratio: Token matching ratio (0-1)
        
        Returns:
            Combined name similarity score (0-1)
        """
        try:
            # Base similarity score
            base_score = similarity_ratio
            
            # Bonus for exact match after normalization
            if normalized_name1.lower() == normalized_name2.lower():
                base_score = 1.0
            
            # Bonus for high token overlap
            token_bonus = token_match_ratio * 0.2
            
            # Penalty for significant length difference
            len1, len2 = len(normalized_name1), len(normalized_name2)
            length_ratio = min(len1, len2) / max(len1, len2) if max(len1, len2) > 0 else 0
            length_penalty = (1.0 - length_ratio) * 0.1
            
            # Combine factors
            final_score = base_score + token_bonus - length_penalty
            
            return max(0.0, min(1.0, final_score))
            
        except Exception as e:
            logger.error(f"Error calculating name similarity score: {e}")
            return 0.0
    
    def calculate_brand_match_score(
        self,
        brand1: Optional[str],
        brand2: Optional[str],
        brand_aliases1: List[str],
        brand_aliases2: List[str]
    ) -> float:
        """
        Calculate brand matching score
        
        Args:
            brand1, brand2: Brand names
            brand_aliases1, brand_aliases2: Known brand aliases
        
        Returns:
            Brand match score (0-1)
        """
        try:
            if not brand1 or not brand2:
                return 0.0
            
            # Exact match
            if brand1.lower().strip() == brand2.lower().strip():
                return 1.0
            
            # Check aliases
            all_aliases1 = [brand1.lower().strip()] + [alias.lower().strip() for alias in brand_aliases1]
            all_aliases2 = [brand2.lower().strip()] + [alias.lower().strip() for alias in brand_aliases2]
            
            for alias1 in all_aliases1:
                if alias1 in all_aliases2:
                    return 0.9  # High score for alias match
            
            # Partial similarity for similar brand names
            from difflib import SequenceMatcher
            similarity = SequenceMatcher(None, brand1.lower(), brand2.lower()).ratio()
            
            if similarity > 0.8:
                return similarity * 0.7  # Moderate score for similar names
            
            return 0.0
            
        except Exception as e:
            logger.error(f"Error calculating brand match score: {e}")
            return 0.0
    
    def calculate_sku_similarity_score(
        self,
        sku1: Optional[str],
        sku2: Optional[str],
        patterns1: List[str],
        patterns2: List[str]
    ) -> float:
        """
        Calculate SKU similarity score
        
        Args:
            sku1, sku2: SKU values
            patterns1, patterns2: Extracted SKU patterns
        
        Returns:
            SKU similarity score (0-1)
        """
        try:
            if not sku1 or not sku2:
                return 0.0
            
            # Exact match
            if sku1.lower().strip() == sku2.lower().strip():
                return 1.0
            
            # Pattern matching
            common_patterns = set(patterns1) & set(patterns2)
            if common_patterns:
                pattern_ratio = len(common_patterns) / max(len(patterns1), len(patterns2))
                return min(0.9, pattern_ratio)
            
            # Substring matching
            shorter, longer = (sku1, sku2) if len(sku1) < len(sku2) else (sku2, sku1)
            if shorter.lower() in longer.lower():
                return 0.6
            
            return 0.0
            
        except Exception as e:
            logger.error(f"Error calculating SKU similarity score: {e}")
            return 0.0
    
    def calculate_specification_match_score(
        self,
        specs1: Dict[str, Any],
        specs2: Dict[str, Any],
        critical_specs: Optional[List[str]] = None
    ) -> float:
        """
        Calculate specification matching score
        
        Args:
            specs1, specs2: Specification dictionaries
            critical_specs: List of critical specification keys
        
        Returns:
            Specification match score (0-1)
        """
        try:
            if not specs1 or not specs2:
                return 0.0
            
            critical_specs = critical_specs or ['model', 'size', 'capacity', 'power', 'voltage']
            
            common_keys = set(specs1.keys()) & set(specs2.keys())
            if not common_keys:
                return 0.0
            
            matches = 0
            critical_matches = 0
            critical_total = 0
            
            for key in common_keys:
                val1, val2 = str(specs1[key]).lower(), str(specs2[key]).lower()
                
                if val1 == val2:
                    matches += 1
                    if key in critical_specs:
                        critical_matches += 1
                
                if key in critical_specs:
                    critical_total += 1
            
            # Base score from overall matches
            base_score = matches / len(common_keys)
            
            # Bonus for critical spec matches
            if critical_total > 0:
                critical_bonus = (critical_matches / critical_total) * 0.3
                base_score += critical_bonus
            
            return min(1.0, base_score)
            
        except Exception as e:
            logger.error(f"Error calculating specification match score: {e}")
            return 0.0
    
    def calculate_price_proximity_score(
        self,
        price1: Optional[float],
        price2: Optional[float],
        tolerance_percent: float = 0.2
    ) -> float:
        """
        Calculate price proximity score
        
        Args:
            price1, price2: Product prices
            tolerance_percent: Acceptable price difference as percentage
        
        Returns:
            Price proximity score (0-1)
        """
        try:
            if not price1 or not price2 or price1 <= 0 or price2 <= 0:
                return 0.0
            
            # Calculate percentage difference
            avg_price = (price1 + price2) / 2
            price_diff = abs(price1 - price2)
            diff_percent = price_diff / avg_price
            
            if diff_percent <= tolerance_percent:
                # Linear decay within tolerance
                return 1.0 - (diff_percent / tolerance_percent)
            
            return 0.0
            
        except Exception as e:
            logger.error(f"Error calculating price proximity score: {e}")
            return 0.0
    
    def get_confidence_category(self, score: float) -> str:
        """
        Categorize confidence score
        
        Args:
            score: Confidence score (0-1)
        
        Returns:
            Confidence category string
        """
        if score >= 0.9:
            return "very_high"
        elif score >= 0.8:
            return "high"
        elif score >= 0.7:
            return "medium_high"
        elif score >= 0.6:
            return "medium"
        elif score >= 0.5:
            return "medium_low"
        elif score >= 0.3:
            return "low"
        else:
            return "very_low"