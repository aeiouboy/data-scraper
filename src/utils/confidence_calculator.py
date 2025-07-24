"""
Enhanced Confidence Scoring System
Multi-factor confidence calculation for product matching
"""

import re
import math
import logging
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from enum import Enum

from src.config.text_normalization_config import (
    CONFIDENCE_WEIGHTS, MATCHING_THRESHOLDS, SPEC_TOLERANCES
)

logger = logging.getLogger(__name__)


class MatchType(Enum):
    """Types of matches for confidence calculation"""
    EXACT = "exact"
    FUZZY = "fuzzy"
    PARTIAL = "partial"
    SEMANTIC = "semantic"
    NONE = "none"


@dataclass
class MatchFactor:
    """Individual matching factor with score and weight"""
    name: str
    score: float
    weight: float
    match_type: MatchType
    details: Dict[str, Any]


@dataclass
class ConfidenceResult:
    """Complete confidence calculation result"""
    overall_confidence: float
    factors: List[MatchFactor]
    breakdown: Dict[str, float]
    metadata: Dict[str, Any]
    threshold_met: bool
    recommendation: str


class ConfidenceCalculator:
    """Enhanced confidence scoring system"""
    
    def __init__(self, config: Optional[Dict] = None):
        """Initialize confidence calculator with configuration"""
        self.config = config or {}
        self.weights = self.config.get('weights', CONFIDENCE_WEIGHTS)
        self.thresholds = self.config.get('thresholds', MATCHING_THRESHOLDS)
        self.spec_tolerances = self.config.get('spec_tolerances', SPEC_TOLERANCES)
        
        # Initialize scoring components
        self.scoring_components = {
            'name_similarity': self._calculate_name_similarity,
            'brand_match': self._calculate_brand_match,
            'sku_match': self._calculate_sku_match,
            'spec_match': self._calculate_spec_match,
            'price_match': self._calculate_price_match,
            'category_match': self._calculate_category_match,
            'retailer_consistency': self._calculate_retailer_consistency,
            'context_match': self._calculate_context_match
        }
    
    def calculate_confidence(self, product1: Dict, product2: Dict, 
                           context: Optional[Dict] = None) -> ConfidenceResult:
        """Calculate overall confidence score for product match"""
        factors = []
        breakdown = {}
        metadata = {
            'product1_id': product1.get('id'),
            'product2_id': product2.get('id'),
            'calculation_method': 'enhanced_weighted'
        }
        
        # Calculate each factor
        for factor_name, calculator in self.scoring_components.items():
            try:
                factor = calculator(product1, product2, context)
                factors.append(factor)
                breakdown[factor_name] = factor.score * factor.weight
            except Exception as e:
                logger.warning(f"Error calculating {factor_name}: {e}")
                # Add zero-score factor for failed calculations
                factor = MatchFactor(
                    name=factor_name,
                    score=0.0,
                    weight=self.weights.get(factor_name, 0.0),
                    match_type=MatchType.NONE,
                    details={'error': str(e)}
                )
                factors.append(factor)
                breakdown[factor_name] = 0.0
        
        # Calculate weighted average
        total_weighted_score = sum(breakdown.values())
        total_weight = sum(f.weight for f in factors)
        
        if total_weight > 0:
            overall_confidence = total_weighted_score / total_weight
        else:
            overall_confidence = 0.0
        
        # Apply bonuses and penalties
        overall_confidence = self._apply_bonuses_penalties(
            overall_confidence, factors, product1, product2
        )
        
        # Ensure confidence is within bounds
        overall_confidence = max(0.0, min(1.0, overall_confidence))
        
        # Determine if threshold is met
        threshold_met = overall_confidence >= self.thresholds['min_confidence']
        
        # Generate recommendation
        recommendation = self._generate_recommendation(overall_confidence, factors)
        
        return ConfidenceResult(
            overall_confidence=overall_confidence,
            factors=factors,
            breakdown=breakdown,
            metadata=metadata,
            threshold_met=threshold_met,
            recommendation=recommendation
        )
    
    def _calculate_name_similarity(self, product1: Dict, product2: Dict, 
                                 context: Optional[Dict] = None) -> MatchFactor:
        """Calculate name similarity factor"""
        name1 = product1.get('name', '')
        name2 = product2.get('name', '')
        
        if not name1 or not name2:
            return MatchFactor(
                name='name_similarity',
                score=0.0,
                weight=self.weights.get('name_similarity', 0.4),
                match_type=MatchType.NONE,
                details={'reason': 'Missing name data'}
            )
        
        # Calculate various similarity metrics
        exact_match = 1.0 if name1.lower() == name2.lower() else 0.0
        token_similarity = self._token_similarity(name1, name2)
        char_similarity = self._character_similarity(name1, name2)
        semantic_similarity = self._semantic_similarity(name1, name2)
        
        # Combine similarities with weights
        combined_score = (
            exact_match * 0.4 +
            token_similarity * 0.3 +
            char_similarity * 0.2 +
            semantic_similarity * 0.1
        )
        
        # Determine match type
        if exact_match > 0:
            match_type = MatchType.EXACT
        elif combined_score > 0.8:
            match_type = MatchType.FUZZY
        elif combined_score > 0.5:
            match_type = MatchType.PARTIAL
        elif combined_score > 0.2:
            match_type = MatchType.SEMANTIC
        else:
            match_type = MatchType.NONE
        
        return MatchFactor(
            name='name_similarity',
            score=combined_score,
            weight=self.weights.get('name_similarity', 0.4),
            match_type=match_type,
            details={
                'exact_match': exact_match,
                'token_similarity': token_similarity,
                'char_similarity': char_similarity,
                'semantic_similarity': semantic_similarity,
                'name1_length': len(name1),
                'name2_length': len(name2)
            }
        )
    
    def _calculate_brand_match(self, product1: Dict, product2: Dict, 
                             context: Optional[Dict] = None) -> MatchFactor:
        """Calculate brand match factor"""
        brand1 = product1.get('brand', '')
        brand2 = product2.get('brand', '')
        
        if not brand1 or not brand2:
            return MatchFactor(
                name='brand_match',
                score=0.0,
                weight=self.weights.get('brand_match', 0.3),
                match_type=MatchType.NONE,
                details={'reason': 'Missing brand data'}
            )
        
        # Normalize brands
        norm_brand1 = self._normalize_brand(brand1)
        norm_brand2 = self._normalize_brand(brand2)
        
        # Calculate match score
        if norm_brand1 == norm_brand2:
            score = 1.0
            match_type = MatchType.EXACT
        elif self._are_brand_aliases(norm_brand1, norm_brand2):
            score = 0.9
            match_type = MatchType.FUZZY
        else:
            # Calculate similarity for potential aliases
            similarity = self._character_similarity(norm_brand1, norm_brand2)
            if similarity > 0.7:
                score = similarity * 0.8
                match_type = MatchType.PARTIAL
            else:
                score = 0.0
                match_type = MatchType.NONE
        
        return MatchFactor(
            name='brand_match',
            score=score,
            weight=self.weights.get('brand_match', 0.3),
            match_type=match_type,
            details={
                'brand1': brand1,
                'brand2': brand2,
                'normalized_brand1': norm_brand1,
                'normalized_brand2': norm_brand2,
                'similarity': similarity if 'similarity' in locals() else 1.0
            }
        )
    
    def _calculate_sku_match(self, product1: Dict, product2: Dict, 
                           context: Optional[Dict] = None) -> MatchFactor:
        """Calculate SKU match factor"""
        sku1 = product1.get('sku') or product1.get('model_number', '')
        sku2 = product2.get('sku') or product2.get('model_number', '')
        
        if not sku1 or not sku2:
            return MatchFactor(
                name='sku_match',
                score=0.0,
                weight=self.weights.get('sku_match', 0.25),
                match_type=MatchType.NONE,
                details={'reason': 'Missing SKU data'}
            )
        
        # Normalize SKUs
        norm_sku1 = self._normalize_sku(sku1)
        norm_sku2 = self._normalize_sku(sku2)
        
        # Calculate match score
        if norm_sku1 == norm_sku2:
            score = 1.0
            match_type = MatchType.EXACT
        elif self._are_sku_variants(norm_sku1, norm_sku2):
            score = 0.85
            match_type = MatchType.FUZZY
        elif self._partial_sku_match(norm_sku1, norm_sku2):
            score = 0.7
            match_type = MatchType.PARTIAL
        else:
            score = 0.0
            match_type = MatchType.NONE
        
        return MatchFactor(
            name='sku_match',
            score=score,
            weight=self.weights.get('sku_match', 0.25),
            match_type=match_type,
            details={
                'sku1': sku1,
                'sku2': sku2,
                'normalized_sku1': norm_sku1,
                'normalized_sku2': norm_sku2,
                'length_diff': abs(len(norm_sku1) - len(norm_sku2))
            }
        )
    
    def _calculate_spec_match(self, product1: Dict, product2: Dict, 
                            context: Optional[Dict] = None) -> MatchFactor:
        """Calculate specification match factor"""
        specs1 = product1.get('specifications', {})
        specs2 = product2.get('specifications', {})
        
        if not specs1 or not specs2:
            return MatchFactor(
                name='spec_match',
                score=0.0,
                weight=self.weights.get('spec_match', 0.2),
                match_type=MatchType.NONE,
                details={'reason': 'Missing specification data'}
            )
        
        # Find common specifications
        common_specs = set(specs1.keys()) & set(specs2.keys())
        
        if not common_specs:
            return MatchFactor(
                name='spec_match',
                score=0.0,
                weight=self.weights.get('spec_match', 0.2),
                match_type=MatchType.NONE,
                details={'reason': 'No common specifications'}
            )
        
        # Calculate match score for each specification
        spec_scores = {}
        total_score = 0.0
        
        for spec in common_specs:
            spec_score = self._compare_specification(
                spec, specs1[spec], specs2[spec]
            )
            spec_scores[spec] = spec_score
            total_score += spec_score
        
        # Average score
        average_score = total_score / len(common_specs)
        
        # Determine match type
        if average_score >= 0.9:
            match_type = MatchType.EXACT
        elif average_score >= 0.7:
            match_type = MatchType.FUZZY
        elif average_score >= 0.5:
            match_type = MatchType.PARTIAL
        else:
            match_type = MatchType.NONE
        
        return MatchFactor(
            name='spec_match',
            score=average_score,
            weight=self.weights.get('spec_match', 0.2),
            match_type=match_type,
            details={
                'common_specs': list(common_specs),
                'spec_scores': spec_scores,
                'total_specs_1': len(specs1),
                'total_specs_2': len(specs2),
                'match_count': len(common_specs)
            }
        )
    
    def _calculate_price_match(self, product1: Dict, product2: Dict, 
                             context: Optional[Dict] = None) -> MatchFactor:
        """Calculate price match factor"""
        price1 = product1.get('price')
        price2 = product2.get('price')
        
        if not price1 or not price2:
            return MatchFactor(
                name='price_match',
                score=0.0,
                weight=self.weights.get('price_match', 0.1),
                match_type=MatchType.NONE,
                details={'reason': 'Missing price data'}
            )
        
        # Convert to float if needed
        try:
            price1 = float(price1)
            price2 = float(price2)
        except (ValueError, TypeError):
            return MatchFactor(
                name='price_match',
                score=0.0,
                weight=self.weights.get('price_match', 0.1),
                match_type=MatchType.NONE,
                details={'reason': 'Invalid price data'}
            )
        
        # Calculate price difference percentage
        avg_price = (price1 + price2) / 2
        price_diff = abs(price1 - price2)
        price_diff_pct = price_diff / avg_price if avg_price > 0 else 1.0
        
        # Calculate score based on tolerance
        tolerance = self.thresholds.get('price_tolerance', 0.20)
        
        if price_diff_pct <= tolerance:
            score = 1.0 - (price_diff_pct / tolerance) * 0.5
            match_type = MatchType.FUZZY if price_diff_pct > 0.05 else MatchType.EXACT
        else:
            score = max(0.0, 1.0 - (price_diff_pct / tolerance))
            match_type = MatchType.PARTIAL if score > 0.3 else MatchType.NONE
        
        return MatchFactor(
            name='price_match',
            score=score,
            weight=self.weights.get('price_match', 0.1),
            match_type=match_type,
            details={
                'price1': price1,
                'price2': price2,
                'price_diff': price_diff,
                'price_diff_pct': price_diff_pct,
                'tolerance': tolerance,
                'within_tolerance': price_diff_pct <= tolerance
            }
        )
    
    def _calculate_category_match(self, product1: Dict, product2: Dict, 
                                context: Optional[Dict] = None) -> MatchFactor:
        """Calculate category match factor"""
        category1 = product1.get('category', '')
        category2 = product2.get('category', '')
        
        if not category1 or not category2:
            return MatchFactor(
                name='category_match',
                score=0.0,
                weight=self.weights.get('category_match', 0.1),
                match_type=MatchType.NONE,
                details={'reason': 'Missing category data'}
            )
        
        # Normalize categories
        norm_cat1 = self._normalize_category(category1)
        norm_cat2 = self._normalize_category(category2)
        
        # Calculate match score
        if norm_cat1 == norm_cat2:
            score = 1.0
            match_type = MatchType.EXACT
        elif self._are_related_categories(norm_cat1, norm_cat2):
            score = 0.7
            match_type = MatchType.FUZZY
        else:
            score = 0.0
            match_type = MatchType.NONE
        
        return MatchFactor(
            name='category_match',
            score=score,
            weight=self.weights.get('category_match', 0.1),
            match_type=match_type,
            details={
                'category1': category1,
                'category2': category2,
                'normalized_category1': norm_cat1,
                'normalized_category2': norm_cat2
            }
        )
    
    def _calculate_retailer_consistency(self, product1: Dict, product2: Dict, 
                                      context: Optional[Dict] = None) -> MatchFactor:
        """Calculate retailer consistency factor"""
        retailer1 = product1.get('retailer', '')
        retailer2 = product2.get('retailer', '')
        
        if not retailer1 or not retailer2:
            return MatchFactor(
                name='retailer_consistency',
                score=0.5,  # Neutral score for missing data
                weight=self.weights.get('retailer_consistency', 0.05),
                match_type=MatchType.NONE,
                details={'reason': 'Missing retailer data'}
            )
        
        # Different retailers is expected for price comparison
        if retailer1 != retailer2:
            score = 1.0  # Good for price comparison
            match_type = MatchType.EXACT
        else:
            score = 0.3  # Same retailer might be duplicate
            match_type = MatchType.PARTIAL
        
        return MatchFactor(
            name='retailer_consistency',
            score=score,
            weight=self.weights.get('retailer_consistency', 0.05),
            match_type=match_type,
            details={
                'retailer1': retailer1,
                'retailer2': retailer2,
                'different_retailers': retailer1 != retailer2
            }
        )
    
    def _calculate_context_match(self, product1: Dict, product2: Dict, 
                               context: Optional[Dict] = None) -> MatchFactor:
        """Calculate context match factor"""
        if not context:
            return MatchFactor(
                name='context_match',
                score=0.5,  # Neutral score
                weight=self.weights.get('context_match', 0.05),
                match_type=MatchType.NONE,
                details={'reason': 'No context provided'}
            )
        
        # Context factors
        score = 0.5
        details = {}
        
        # Search query context
        if 'search_query' in context:
            query = context['search_query'].lower()
            name1 = product1.get('name', '').lower()
            name2 = product2.get('name', '').lower()
            
            query_relevance1 = self._calculate_query_relevance(query, name1)
            query_relevance2 = self._calculate_query_relevance(query, name2)
            
            if query_relevance1 > 0.5 and query_relevance2 > 0.5:
                score += 0.3
            
            details['query_relevance'] = {
                'product1': query_relevance1,
                'product2': query_relevance2
            }
        
        # User behavior context
        if 'user_preferences' in context:
            prefs = context['user_preferences']
            # Add preference-based scoring logic here
            details['user_preferences'] = prefs
        
        match_type = MatchType.FUZZY if score > 0.6 else MatchType.PARTIAL
        
        return MatchFactor(
            name='context_match',
            score=score,
            weight=self.weights.get('context_match', 0.05),
            match_type=match_type,
            details=details
        )
    
    def _apply_bonuses_penalties(self, base_confidence: float, factors: List[MatchFactor], 
                               product1: Dict, product2: Dict) -> float:
        """Apply bonuses and penalties to base confidence"""
        adjusted_confidence = base_confidence
        
        # SKU match bonus
        sku_factor = next((f for f in factors if f.name == 'sku_match'), None)
        if sku_factor and sku_factor.score >= 0.9:
            adjusted_confidence += 0.1
        
        # Exact name match bonus
        name_factor = next((f for f in factors if f.name == 'name_similarity'), None)
        if name_factor and name_factor.match_type == MatchType.EXACT:
            adjusted_confidence += 0.05
        
        # Brand mismatch penalty
        brand_factor = next((f for f in factors if f.name == 'brand_match'), None)
        if brand_factor and brand_factor.score < 0.1:
            adjusted_confidence -= 0.15
        
        # Price outlier penalty
        price_factor = next((f for f in factors if f.name == 'price_match'), None)
        if price_factor and price_factor.score < 0.1:
            adjusted_confidence -= 0.1
        
        # Multiple high-confidence factors bonus
        high_confidence_count = sum(1 for f in factors if f.score >= 0.8)
        if high_confidence_count >= 3:
            adjusted_confidence += 0.05
        
        return adjusted_confidence
    
    def _generate_recommendation(self, confidence: float, factors: List[MatchFactor]) -> str:
        """Generate matching recommendation based on confidence and factors"""
        if confidence >= 0.9:
            return "Strong match - Highly likely to be the same product"
        elif confidence >= 0.7:
            return "Good match - Likely to be the same product"
        elif confidence >= 0.5:
            return "Moderate match - Possible same product, review recommended"
        elif confidence >= 0.3:
            return "Weak match - Unlikely to be the same product"
        else:
            return "No match - Different products"
    
    # Utility methods
    def _token_similarity(self, text1: str, text2: str) -> float:
        """Calculate token-based similarity"""
        tokens1 = set(text1.lower().split())
        tokens2 = set(text2.lower().split())
        
        if not tokens1 or not tokens2:
            return 0.0
        
        intersection = tokens1 & tokens2
        union = tokens1 | tokens2
        
        return len(intersection) / len(union)
    
    def _character_similarity(self, text1: str, text2: str) -> float:
        """Calculate character-based similarity"""
        if not text1 or not text2:
            return 0.0
        
        # Simple character-level similarity
        chars1 = set(text1.lower())
        chars2 = set(text2.lower())
        
        intersection = chars1 & chars2
        union = chars1 | chars2
        
        return len(intersection) / len(union) if union else 0.0
    
    def _semantic_similarity(self, text1: str, text2: str) -> float:
        """Calculate semantic similarity (placeholder for advanced NLP)"""
        # This is a placeholder - in production, use advanced NLP models
        return self._token_similarity(text1, text2) * 0.8
    
    def _normalize_brand(self, brand: str) -> str:
        """Normalize brand name"""
        return brand.lower().strip()
    
    def _are_brand_aliases(self, brand1: str, brand2: str) -> bool:
        """Check if brands are aliases"""
        # Placeholder - use BrandAliasManager in production
        return brand1 == brand2
    
    def _normalize_sku(self, sku: str) -> str:
        """Normalize SKU"""
        return sku.upper().replace('-', '').replace(' ', '').replace('/', '')
    
    def _are_sku_variants(self, sku1: str, sku2: str) -> bool:
        """Check if SKUs are variants"""
        if len(sku1) >= 6 and len(sku2) >= 6:
            base1 = re.sub(r'[A-Z]*\d*$', '', sku1)
            base2 = re.sub(r'[A-Z]*\d*$', '', sku2)
            return base1 == base2 and len(base1) >= 4
        return False
    
    def _partial_sku_match(self, sku1: str, sku2: str) -> bool:
        """Check for partial SKU match"""
        if len(sku1) >= 6 and len(sku2) >= 6:
            return sku1 in sku2 or sku2 in sku1
        return False
    
    def _compare_specification(self, spec_name: str, value1: Any, value2: Any) -> float:
        """Compare two specification values"""
        if value1 == value2:
            return 1.0
        
        # Try numeric comparison with tolerance
        try:
            num1 = float(value1)
            num2 = float(value2)
            
            tolerance = self.spec_tolerances.get(spec_name, 0.05)
            diff = abs(num1 - num2)
            avg = (num1 + num2) / 2
            
            if avg > 0:
                diff_pct = diff / avg
                return max(0.0, 1.0 - (diff_pct / tolerance))
            else:
                return 1.0 if diff == 0 else 0.0
        
        except (ValueError, TypeError):
            # String comparison
            return self._character_similarity(str(value1), str(value2))
    
    def _normalize_category(self, category: str) -> str:
        """Normalize category name"""
        return category.lower().strip()
    
    def _are_related_categories(self, cat1: str, cat2: str) -> bool:
        """Check if categories are related"""
        # Placeholder - implement category hierarchy logic
        return cat1 == cat2
    
    def _calculate_query_relevance(self, query: str, text: str) -> float:
        """Calculate relevance to search query"""
        return self._token_similarity(query, text)


# Example usage and testing
if __name__ == "__main__":
    # Initialize confidence calculator
    calculator = ConfidenceCalculator()
    
    # Test products
    product1 = {
        'id': 1,
        'name': 'MITSUBISHI Air Conditioner MSY-KP13VF 12000BTU',
        'brand': 'MITSUBISHI',
        'sku': 'MSY-KP13VF',
        'price': 15000,
        'category': 'air-conditioner',
        'retailer': 'homepro',
        'specifications': {
            'capacity_btu': 12000,
            'voltage_v': 220,
            'frequency_hz': 50
        }
    }
    
    product2 = {
        'id': 2,
        'name': 'มิตซูบิชิ เครื่องปรับอากาศ MSY-KP13VF 12,000 บีทียู',
        'brand': 'มิตซูบิชิ',
        'sku': 'MSYKP13VF',
        'price': 15500,
        'category': 'air-conditioner',
        'retailer': 'thaiwatsadu',
        'specifications': {
            'capacity_btu': 12000,
            'voltage_v': 220,
            'frequency_hz': 50
        }
    }
    
    # Test context
    context = {
        'search_query': 'mitsubishi air conditioner 12000 btu',
        'user_preferences': {
            'brand_preference': 'mitsubishi',
            'price_range': [10000, 20000]
        }
    }
    
    print("Confidence Calculation Test:")
    print("=" * 60)
    
    # Calculate confidence
    result = calculator.calculate_confidence(product1, product2, context)
    
    print(f"Overall Confidence: {result.overall_confidence:.3f}")
    print(f"Threshold Met: {result.threshold_met}")
    print(f"Recommendation: {result.recommendation}")
    print()
    
    print("Factor Breakdown:")
    print("-" * 40)
    
    for factor in result.factors:
        print(f"{factor.name}:")
        print(f"  Score: {factor.score:.3f}")
        print(f"  Weight: {factor.weight:.3f}")
        print(f"  Weighted Score: {factor.score * factor.weight:.3f}")
        print(f"  Match Type: {factor.match_type.value}")
        print(f"  Details: {factor.details}")
        print()
    
    print("Weighted Breakdown:")
    print("-" * 40)
    
    for factor_name, weighted_score in result.breakdown.items():
        print(f"{factor_name}: {weighted_score:.3f}")
    
    print(f"\nTotal Weighted Score: {sum(result.breakdown.values()):.3f}")
    print(f"Total Weight: {sum(f.weight for f in result.factors):.3f}")
    
    # Test with different products
    print("\n" + "=" * 60)
    print("Testing with Different Products:")
    
    product3 = {
        'id': 3,
        'name': 'Samsung Refrigerator RT29K5511S8 300L',
        'brand': 'Samsung',
        'sku': 'RT29K5511S8',
        'price': 12000,
        'category': 'refrigerator',
        'retailer': 'homepro',
        'specifications': {
            'volume_liters': 300,
            'doors': 2,
            'energy_rating': 5
        }
    }
    
    result2 = calculator.calculate_confidence(product1, product3, context)
    
    print(f"Overall Confidence: {result2.overall_confidence:.3f}")
    print(f"Threshold Met: {result2.threshold_met}")
    print(f"Recommendation: {result2.recommendation}")
    
    # Show top factors
    print("\nTop Factors:")
    sorted_factors = sorted(result2.factors, key=lambda f: f.score * f.weight, reverse=True)
    for factor in sorted_factors[:3]:
        print(f"  {factor.name}: {factor.score:.3f} × {factor.weight:.3f} = {factor.score * factor.weight:.3f}")