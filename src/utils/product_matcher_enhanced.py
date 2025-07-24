"""
Enhanced Product Matcher with improved Thai-English matching for price comparison
"""
import re
import logging
from typing import Dict, List, Tuple, Optional, Set
from dataclasses import dataclass
from collections import defaultdict
import math
from decimal import Decimal

from src.utils.text_normalizer_enhanced import EnhancedTextNormalizer

logger = logging.getLogger(__name__)

@dataclass
class MatchResult:
    """Enhanced match result with detailed scoring"""
    confidence: float
    match_type: str  # 'exact', 'high', 'medium', 'low'
    details: Dict[str, float]
    matched_fields: List[str]
    warnings: List[str]

class EnhancedProductMatcher:
    """Enhanced product matcher with better Thai-English support"""
    
    def __init__(self):
        self.normalizer = EnhancedTextNormalizer()
        
        # Weights for different matching components
        self.weights = {
            'sku': 0.35,      # SKU/Model number match
            'brand': 0.25,    # Brand match
            'name': 0.20,     # Name similarity
            'specs': 0.15,    # Specification match
            'category': 0.05  # Category match
        }
        
        # Thresholds for match types
        self.thresholds = {
            'exact': 0.95,
            'high': 0.80,
            'medium': 0.65,
            'low': 0.50
        }
        
        # Specification tolerances
        self.spec_tolerances = {
            'size': 0.01,      # 1% tolerance for sizes
            'capacity': 0.02,  # 2% tolerance for capacity
            'power': 0.05,     # 5% tolerance for power ratings
            'weight': 0.03,    # 3% tolerance for weight
        }
    
    def match_products(
        self,
        product1: Dict[str, any],
        product2: Dict[str, any]
    ) -> MatchResult:
        """
        Match two products with enhanced Thai-English support
        
        Args:
            product1: First product dict with keys: name, brand, sku, specs, category, price
            product2: Second product dict with same keys
            
        Returns:
            MatchResult with confidence score and details
        """
        scores = {}
        matched_fields = []
        warnings = []
        
        # 1. SKU/Model matching (highest priority)
        sku_score = self._match_sku(
            product1.get('sku', ''),
            product2.get('sku', ''),
            product1.get('name', ''),
            product2.get('name', '')
        )
        scores['sku'] = sku_score
        if sku_score > 0.8:
            matched_fields.append('sku')
        
        # 2. Brand matching
        brand_score = self._match_brand(
            product1.get('brand', ''),
            product2.get('brand', ''),
            product1.get('name', ''),
            product2.get('name', '')
        )
        scores['brand'] = brand_score
        if brand_score > 0.8:
            matched_fields.append('brand')
        
        # 3. Name similarity
        name_score = self._match_names(
            product1.get('name', ''),
            product2.get('name', '')
        )
        scores['name'] = name_score
        if name_score > 0.7:
            matched_fields.append('name')
        
        # 4. Specification matching
        spec_score, spec_details = self._match_specifications(
            product1.get('specs', {}),
            product2.get('specs', {}),
            product1.get('name', ''),
            product2.get('name', '')
        )
        scores['specs'] = spec_score
        if spec_score > 0.7:
            matched_fields.append('specifications')
        
        # 5. Category matching
        category_score = self._match_category(
            product1.get('category', ''),
            product2.get('category', '')
        )
        scores['category'] = category_score
        if category_score > 0.8:
            matched_fields.append('category')
        
        # Calculate weighted confidence
        confidence = sum(
            scores.get(field, 0) * weight
            for field, weight in self.weights.items()
        )
        
        # Price consistency check
        price_check = self._check_price_consistency(
            product1.get('price'),
            product2.get('price')
        )
        if not price_check['consistent']:
            warnings.append(price_check['warning'])
            # Reduce confidence if prices are very different
            if price_check['variance'] > 0.5:
                confidence *= 0.8
        
        # Determine match type
        match_type = 'none'
        for type_name, threshold in sorted(self.thresholds.items(), key=lambda x: -x[1]):
            if confidence >= threshold:
                match_type = type_name
                break
        
        # Add detailed information
        details = {
            'sku_score': scores['sku'],
            'brand_score': scores['brand'],
            'name_score': scores['name'],
            'spec_score': scores['specs'],
            'category_score': scores['category'],
            'spec_details': spec_details,
            'price_variance': price_check['variance'],
            'weighted_confidence': confidence
        }
        
        return MatchResult(
            confidence=confidence,
            match_type=match_type,
            details=details,
            matched_fields=matched_fields,
            warnings=warnings
        )
    
    def _match_sku(self, sku1: str, sku2: str, name1: str, name2: str) -> float:
        """Match SKU/Model numbers with Thai-English support"""
        # Direct SKU match
        if sku1 and sku2:
            if sku1.lower() == sku2.lower():
                return 1.0
            
            # Check if one is substring of other (common with variations)
            if sku1.lower() in sku2.lower() or sku2.lower() in sku1.lower():
                return 0.9
        
        # Extract model numbers from names
        specs1 = self.normalizer.extract_specifications(name1)
        specs2 = self.normalizer.extract_specifications(name2)
        
        model1 = specs1.get('model', sku1)
        model2 = specs2.get('model', sku2)
        
        if model1 and model2:
            # Normalize models
            model1_norm = re.sub(r'[^a-z0-9]', '', model1.lower())
            model2_norm = re.sub(r'[^a-z0-9]', '', model2.lower())
            
            if model1_norm == model2_norm:
                return 0.95
            
            # Partial match
            if model1_norm in model2_norm or model2_norm in model1_norm:
                return 0.85
            
            # Check similarity
            similarity = self._calculate_string_similarity(model1_norm, model2_norm)
            if similarity > 0.8:
                return similarity * 0.9
        
        return 0.0
    
    def _match_brand(self, brand1: str, brand2: str, name1: str, name2: str) -> float:
        """Match brands with Thai-English normalization"""
        # Try to extract brands if not provided
        if not brand1:
            brand1 = self.normalizer.extract_brand(name1) or ''
        if not brand2:
            brand2 = self.normalizer.extract_brand(name2) or ''
        
        # Normalize brands
        brand1_norm = self.normalizer.normalize(brand1)
        brand2_norm = self.normalizer.normalize(brand2)
        
        if brand1_norm and brand2_norm:
            if brand1_norm == brand2_norm:
                return 1.0
            
            # Check if brands are similar (typos, variations)
            similarity = self._calculate_string_similarity(brand1_norm, brand2_norm)
            if similarity > 0.85:
                return similarity
        
        # Check if brand appears in the other product's name
        if brand1_norm and brand1_norm in self.normalizer.normalize(name2):
            return 0.8
        if brand2_norm and brand2_norm in self.normalizer.normalize(name1):
            return 0.8
        
        return 0.0
    
    def _match_names(self, name1: str, name2: str) -> float:
        """Match product names with enhanced Thai-English support"""
        # Normalize names
        norm1 = self.normalizer.normalize(name1)
        norm2 = self.normalizer.normalize(name2)
        
        # Extract tokens
        tokens1 = set(self.normalizer.extract_tokens(name1))
        tokens2 = set(self.normalizer.extract_tokens(name2))
        
        if not tokens1 or not tokens2:
            return 0.0
        
        # Calculate multiple similarity metrics
        
        # 1. Jaccard similarity
        intersection = tokens1.intersection(tokens2)
        union = tokens1.union(tokens2)
        jaccard = len(intersection) / len(union) if union else 0
        
        # 2. Overlap coefficient (good for different length names)
        overlap = len(intersection) / min(len(tokens1), len(tokens2)) if tokens1 and tokens2 else 0
        
        # 3. Important token matches
        important_tokens = self._extract_important_tokens(tokens1.union(tokens2))
        important_matches = len(intersection.intersection(important_tokens))
        important_score = important_matches / len(important_tokens) if important_tokens else 0
        
        # 4. Sequence similarity (order matters)
        sequence_score = self._calculate_sequence_similarity(
            list(tokens1), list(tokens2)
        )
        
        # Weighted combination
        final_score = (
            jaccard * 0.3 +
            overlap * 0.3 +
            important_score * 0.25 +
            sequence_score * 0.15
        )
        
        return min(1.0, final_score)
    
    def _match_specifications(
        self,
        specs1: Dict[str, any],
        specs2: Dict[str, any],
        name1: str,
        name2: str
    ) -> Tuple[float, Dict[str, any]]:
        """Match specifications with tolerance handling"""
        # Extract specs from names if not provided
        if not specs1:
            specs1 = self.normalizer.extract_specifications(name1)
        if not specs2:
            specs2 = self.normalizer.extract_specifications(name2)
        
        if not specs1 and not specs2:
            return 0.5, {}  # No specs to compare
        
        matched_specs = {}
        total_score = 0
        spec_count = 0
        
        # Compare each specification
        for spec_name in set(specs1.keys()).union(specs2.keys()):
            val1 = specs1.get(spec_name)
            val2 = specs2.get(spec_name)
            
            if val1 is None or val2 is None:
                continue
            
            spec_count += 1
            
            # Numeric specifications
            if isinstance(val1, (int, float)) and isinstance(val2, (int, float)):
                tolerance = self.spec_tolerances.get(spec_name, 0.05)
                if abs(val1 - val2) <= val1 * tolerance:
                    score = 1.0 - (abs(val1 - val2) / (val1 * tolerance))
                    total_score += score
                    matched_specs[spec_name] = {
                        'match': True,
                        'score': score,
                        'values': [val1, val2]
                    }
                else:
                    matched_specs[spec_name] = {
                        'match': False,
                        'score': 0,
                        'values': [val1, val2]
                    }
            # String specifications
            else:
                val1_str = str(val1).lower()
                val2_str = str(val2).lower()
                if val1_str == val2_str:
                    total_score += 1.0
                    matched_specs[spec_name] = {
                        'match': True,
                        'score': 1.0,
                        'values': [val1, val2]
                    }
                else:
                    similarity = self._calculate_string_similarity(val1_str, val2_str)
                    total_score += similarity
                    matched_specs[spec_name] = {
                        'match': similarity > 0.8,
                        'score': similarity,
                        'values': [val1, val2]
                    }
        
        final_score = total_score / spec_count if spec_count > 0 else 0.5
        
        return final_score, matched_specs
    
    def _match_category(self, cat1: str, cat2: str) -> float:
        """Match categories with normalization"""
        if not cat1 or not cat2:
            return 0.5  # Unknown categories
        
        # Normalize categories
        cat1_norm = self.normalizer.normalize(cat1)
        cat2_norm = self.normalizer.normalize(cat2)
        
        if cat1_norm == cat2_norm:
            return 1.0
        
        # Check if one category is substring of another (hierarchical categories)
        if cat1_norm in cat2_norm or cat2_norm in cat1_norm:
            return 0.8
        
        # Token-based similarity
        tokens1 = set(self.normalizer.extract_tokens(cat1))
        tokens2 = set(self.normalizer.extract_tokens(cat2))
        
        if tokens1 and tokens2:
            jaccard = len(tokens1.intersection(tokens2)) / len(tokens1.union(tokens2))
            return jaccard
        
        return 0.0
    
    def _check_price_consistency(self, price1: any, price2: any) -> Dict[str, any]:
        """Check if prices are consistent"""
        result = {
            'consistent': True,
            'variance': 0.0,
            'warning': ''
        }
        
        try:
            p1 = float(price1) if price1 else 0
            p2 = float(price2) if price2 else 0
            
            if p1 > 0 and p2 > 0:
                # Calculate coefficient of variation
                mean_price = (p1 + p2) / 2
                variance = abs(p1 - p2) / mean_price
                
                result['variance'] = variance
                
                if variance > 0.3:  # More than 30% difference
                    result['consistent'] = False
                    result['warning'] = f"Large price difference: {variance:.1%}"
                elif variance > 0.2:  # 20-30% difference
                    result['warning'] = f"Moderate price difference: {variance:.1%}"
            
        except (ValueError, TypeError):
            result['warning'] = "Could not compare prices"
        
        return result
    
    def _calculate_string_similarity(self, s1: str, s2: str) -> float:
        """Calculate string similarity using edit distance"""
        if not s1 or not s2:
            return 0.0
        
        if s1 == s2:
            return 1.0
        
        # Levenshtein distance normalized by max length
        distance = self._levenshtein_distance(s1, s2)
        max_len = max(len(s1), len(s2))
        
        return 1.0 - (distance / max_len)
    
    def _levenshtein_distance(self, s1: str, s2: str) -> int:
        """Calculate Levenshtein distance between two strings"""
        if len(s1) < len(s2):
            return self._levenshtein_distance(s2, s1)
        
        if len(s2) == 0:
            return len(s1)
        
        previous_row = range(len(s2) + 1)
        for i, c1 in enumerate(s1):
            current_row = [i + 1]
            for j, c2 in enumerate(s2):
                insertions = previous_row[j + 1] + 1
                deletions = current_row[j] + 1
                substitutions = previous_row[j] + (c1 != c2)
                current_row.append(min(insertions, deletions, substitutions))
            previous_row = current_row
        
        return previous_row[-1]
    
    def _extract_important_tokens(self, tokens: Set[str]) -> Set[str]:
        """Extract important tokens (brand names, model numbers, key specs)"""
        important = set()
        
        for token in tokens:
            # Model numbers (contains digits)
            if any(c.isdigit() for c in token):
                important.add(token)
            # Brand names (in our brand list)
            elif token in self.normalizer.brand_mappings.values():
                important.add(token)
            # Size/capacity indicators
            elif any(unit in token for unit in ['inch', 'btu', 'liter', 'ton', 'hp']):
                important.add(token)
            # Key features
            elif token in ['inverter', 'smart', 'digital', 'automatic', 'eco']:
                important.add(token)
        
        return important
    
    def _calculate_sequence_similarity(self, seq1: List[str], seq2: List[str]) -> float:
        """Calculate similarity considering token order"""
        if not seq1 or not seq2:
            return 0.0
        
        # Find longest common subsequence
        lcs_length = self._longest_common_subsequence(seq1, seq2)
        
        # Normalize by average length
        avg_len = (len(seq1) + len(seq2)) / 2
        
        return lcs_length / avg_len if avg_len > 0 else 0.0
    
    def _longest_common_subsequence(self, seq1: List[str], seq2: List[str]) -> int:
        """Find the length of longest common subsequence"""
        m, n = len(seq1), len(seq2)
        dp = [[0] * (n + 1) for _ in range(m + 1)]
        
        for i in range(1, m + 1):
            for j in range(1, n + 1):
                if seq1[i-1] == seq2[j-1]:
                    dp[i][j] = dp[i-1][j-1] + 1
                else:
                    dp[i][j] = max(dp[i-1][j], dp[i][j-1])
        
        return dp[m][n]
    
    def find_best_matches(
        self,
        product: Dict[str, any],
        candidates: List[Dict[str, any]],
        min_confidence: float = 0.5,
        max_results: int = 10
    ) -> List[Tuple[Dict[str, any], MatchResult]]:
        """
        Find best matches for a product from a list of candidates
        
        Returns:
            List of (candidate, match_result) tuples sorted by confidence
        """
        matches = []
        
        for candidate in candidates:
            # Skip same product
            if product.get('id') == candidate.get('id'):
                continue
            
            # Skip same retailer unless specifically allowed
            if product.get('retailer_code') == candidate.get('retailer_code'):
                continue
            
            result = self.match_products(product, candidate)
            
            if result.confidence >= min_confidence:
                matches.append((candidate, result))
        
        # Sort by confidence
        matches.sort(key=lambda x: x[1].confidence, reverse=True)
        
        return matches[:max_results]