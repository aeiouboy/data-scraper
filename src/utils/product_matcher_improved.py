"""
Improved Product Matcher with enhanced capacity/BTU validation
Prevents false positives when products have significantly different capacities
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
    match_type: str  # 'exact', 'high', 'medium', 'low', 'none'
    details: Dict[str, float]
    matched_fields: List[str]
    warnings: List[str]
    rejection_reasons: List[str]

class ImprovedProductMatcher:
    """Improved product matcher with enhanced capacity validation"""
    
    def __init__(self):
        self.normalizer = EnhancedTextNormalizer()
        
        # Weights for different matching components
        self.weights = {
            'sku': 0.40,      # Increased SKU weight - most important
            'brand': 0.25,    # Brand match
            'name': 0.15,     # Reduced name weight to prevent false positives
            'specs': 0.15,    # Specification match
            'category': 0.05  # Category match
        }
        
        # Stricter thresholds to prevent false positives
        self.thresholds = {
            'exact': 0.98,    # Near perfect match required
            'high': 0.85,     # High confidence threshold raised
            'medium': 0.70,   # Medium threshold raised  
            'low': 0.60,      # Low threshold raised
            'minimum': 0.50   # Minimum to even consider
        }
        
        # Enhanced specification tolerances by category
        self.spec_tolerances = {
            # Air conditioners - strict BTU tolerance
            'air-conditioner': {
                'btu': 0.05,       # Only 5% BTU tolerance for AC units
                'power': 0.05,     # 5% power tolerance
                'capacity': 0.05,  # 5% capacity tolerance
                'voltage': 0.01,   # 1% voltage tolerance
                'size': 0.10,      # 10% size tolerance
            },
            # Refrigerators - strict capacity tolerance
            'refrigerator': {
                'capacity': 0.08,  # 8% capacity tolerance
                'volume': 0.08,    # 8% volume tolerance
                'power': 0.10,     # 10% power tolerance
                'size': 0.10,      # 10% size tolerance
            },
            # Default tolerances for other categories
            'default': {
                'size': 0.10,      # 10% tolerance for sizes
                'capacity': 0.10,  # 10% tolerance for capacity
                'power': 0.15,     # 15% tolerance for power ratings
                'weight': 0.10,    # 10% tolerance for weight
                'voltage': 0.05,   # 5% tolerance for voltage
            }
        }
        
        # Critical specification mismatches that should prevent matching
        self.critical_specs = {
            'air-conditioner': ['btu', 'power', 'capacity', 'type'],
            'refrigerator': ['capacity', 'volume', 'type'],
            'washing-machine': ['capacity', 'type'],
            'television': ['size', 'resolution'],
        }
        
        # BTU extraction patterns (more comprehensive)
        self.btu_patterns = [
            r'(\d+(?:,\d+)?)\s*(?:btu|บีทียู|BTU)',
            r'(\d+(?:,\d+)?)\s*(?:บีทียู/ชม\.?|BTU/HR?)',
            r'(\d+(?:,\d+)?)\s*(?:บีทียู/ชั่วโมง)',
        ]
        
        # Model extraction patterns (enhanced)
        self.model_patterns = [
            r'\b([A-Z]{2,6}\d{2,6}[A-Z0-9\-]*)\b',  # Standard model codes
            r'\b(รุ่น\s*([A-Z0-9\-]+))',             # Thai "model" prefix
            r'\b(model\s*([A-Z0-9\-]+))',            # English "model" prefix
        ]
        
        # DAIKIN-specific model pattern
        self.daikin_model_pattern = re.compile(r'\b(F[A-Z]{2,3}\d{2}[A-Z0-9]{2,5})\b', re.IGNORECASE)
    
    def match_products(
        self,
        product1: Dict[str, any],
        product2: Dict[str, any],
        category: str = 'default'
    ) -> MatchResult:
        """
        Match two products with enhanced validation
        
        Args:
            product1: First product dict
            product2: Second product dict  
            category: Product category for category-specific rules
            
        Returns:
            MatchResult with confidence score and details
        """
        scores = {}
        matched_fields = []
        warnings = []
        rejection_reasons = []
        
        # Early rejection checks
        early_rejection = self._check_early_rejection(product1, product2, category)
        if early_rejection:
            return MatchResult(
                confidence=0.0,
                match_type='none',
                details={'early_rejection': True},
                matched_fields=[],
                warnings=[],
                rejection_reasons=early_rejection
            )
        
        # 1. SKU/Model matching (highest priority)
        sku_score = self._match_sku_enhanced(
            product1.get('sku', ''),
            product2.get('sku', ''),
            product1.get('name', ''),
            product2.get('name', ''),
            category
        )
        scores['sku'] = sku_score
        if sku_score > 0.8:
            matched_fields.append('sku')
        elif sku_score == 0.0:
            # If SKUs are completely different, reduce confidence
            warnings.append("SKU/Model mismatch detected")
        
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
        elif brand_score < 0.5:
            warnings.append("Brand mismatch detected")
        
        # 3. Critical specification validation
        spec_validation = self._validate_critical_specs(
            product1, product2, category
        )
        
        if not spec_validation['valid']:
            rejection_reasons.extend(spec_validation['reasons'])
            return MatchResult(
                confidence=0.0,
                match_type='none',
                details={'spec_validation_failed': True, 'validation_details': spec_validation},
                matched_fields=[],
                warnings=warnings,
                rejection_reasons=rejection_reasons
            )
        
        # 4. Enhanced specification matching
        spec_score, spec_details = self._match_specifications_enhanced(
            product1.get('specs', {}),
            product2.get('specs', {}),
            product1.get('name', ''),
            product2.get('name', ''),
            category
        )
        scores['specs'] = spec_score
        if spec_score > 0.7:
            matched_fields.append('specifications')
        
        # 5. Name similarity (with reduced weight)
        name_score = self._match_names_conservative(
            product1.get('name', ''),
            product2.get('name', '')
        )
        scores['name'] = name_score
        if name_score > 0.8:
            matched_fields.append('name')
        
        # 6. Category matching
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
            # Reduce confidence for very different prices
            if price_check['variance'] > 0.8:
                confidence *= 0.7
                warnings.append("Extreme price difference detected")
        
        # Determine match type with stricter thresholds
        match_type = 'none'
        for type_name, threshold in sorted(self.thresholds.items(), key=lambda x: -x[1]):
            if type_name == 'minimum':
                continue
            if confidence >= threshold:
                match_type = type_name
                break
        
        # Additional rejection for low confidence with high variance
        if confidence < self.thresholds['minimum']:
            match_type = 'none'
            rejection_reasons.append(f"Confidence {confidence:.2f} below minimum threshold {self.thresholds['minimum']}")
        
        # Add detailed information
        details = {
            'sku_score': scores['sku'],
            'brand_score': scores['brand'],
            'name_score': scores['name'],
            'spec_score': scores['specs'],
            'category_score': scores['category'],
            'spec_details': spec_details,
            'price_variance': price_check['variance'],
            'weighted_confidence': confidence,
            'spec_validation': spec_validation
        }
        
        return MatchResult(
            confidence=confidence,
            match_type=match_type,
            details=details,
            matched_fields=matched_fields,
            warnings=warnings,
            rejection_reasons=rejection_reasons
        )
    
    def _check_early_rejection(self, product1: Dict, product2: Dict, category: str) -> List[str]:
        """Check for obvious mismatches that should immediately reject the match"""
        rejections = []
        
        # Extract and compare BTU values for air conditioners
        if category == 'air-conditioner':
            btu1 = self._extract_btu(product1.get('name', ''))
            btu2 = self._extract_btu(product2.get('name', ''))
            
            if btu1 and btu2:
                btu_diff = abs(btu1 - btu2) / max(btu1, btu2)
                if btu_diff > 0.15:  # More than 15% BTU difference
                    rejections.append(f"BTU capacity mismatch: {btu1:,} vs {btu2:,} ({btu_diff*100:.1f}% difference)")
        
        # Check for obvious model number differences
        model1 = self._extract_model_number(product1.get('name', ''))
        model2 = self._extract_model_number(product2.get('name', ''))
        
        if model1 and model2:
            # Normalize models for comparison
            model1_norm = re.sub(r'[^a-z0-9]', '', model1.lower())
            model2_norm = re.sub(r'[^a-z0-9]', '', model2.lower())
            
            # If models are completely different (no overlap), likely different products
            if len(model1_norm) > 4 and len(model2_norm) > 4:
                # For DAIKIN air conditioners, apply stricter validation
                if category == 'air-conditioner' and ('daikin' in product1.get('brand', '').lower() or 'daikin' in product2.get('brand', '').lower()):
                    # Extract core model parts for DAIKIN
                    model1_parts = self._extract_model_parts(model1)
                    model2_parts = self._extract_model_parts(model2)
                    
                    # Reject if core model series differs (e.g., FTKZ vs FTM)
                    if model1_parts['series'] != model2_parts['series']:
                        rejections.append(f"Model series mismatch: {model1} ({model1_parts['series']}) vs {model2} ({model2_parts['series']})")
                elif not (model1_norm in model2_norm or model2_norm in model1_norm):
                    # For other products, check for shared sequences
                    shared_sequences = self._find_shared_sequences(model1_norm, model2_norm, min_length=3)
                    if not shared_sequences:
                        rejections.append(f"Model number mismatch: {model1} vs {model2}")
        
        return rejections
    
    def _extract_btu(self, text: str) -> Optional[int]:
        """Extract BTU value from text"""
        for pattern in self.btu_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                btu_str = match.group(1).replace(',', '')
                try:
                    return int(btu_str)
                except ValueError:
                    continue
        return None
    
    def _extract_model_number(self, text: str) -> Optional[str]:
        """Extract model number from text"""
        for pattern in self.model_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                if 'รุ่น' in match.group(0) or 'model' in match.group(0).lower():
                    return match.group(2) if len(match.groups()) > 1 else match.group(1)
                else:
                    return match.group(1)
        return None
    
    def _find_shared_sequences(self, text1: str, text2: str, min_length: int = 3) -> List[str]:
        """Find shared alphanumeric sequences between two strings"""
        shared = []
        for i in range(len(text1) - min_length + 1):
            for j in range(min_length, len(text1) - i + 1):
                sequence = text1[i:i+j]
                if sequence in text2:
                    shared.append(sequence)
        return shared
    
    def _extract_model_parts(self, model: str) -> Dict[str, str]:
        """Extract model parts for detailed comparison (especially for DAIKIN)"""
        parts = {
            'full': model,
            'series': '',
            'capacity': '',
            'suffix': ''
        }
        
        # Try DAIKIN pattern first
        daikin_match = self.daikin_model_pattern.match(model)
        if daikin_match:
            full_model = daikin_match.group(1).upper()
            # Extract series (first 3-4 letters)
            series_match = re.match(r'^([A-Z]{3,4})', full_model)
            if series_match:
                parts['series'] = series_match.group(1)
            
            # Extract capacity (digits in middle)
            capacity_match = re.search(r'(\d{2,3})', full_model)
            if capacity_match:
                parts['capacity'] = capacity_match.group(1)
            
            # Extract suffix (remaining part)
            suffix_match = re.search(r'\d{2,3}([A-Z0-9]+)$', full_model)
            if suffix_match:
                parts['suffix'] = suffix_match.group(1)
        else:
            # Generic extraction
            # Try to extract letter prefix
            prefix_match = re.match(r'^([A-Z]+)', model.upper())
            if prefix_match:
                parts['series'] = prefix_match.group(1)
        
        return parts
    
    def _validate_critical_specs(self, product1: Dict, product2: Dict, category: str) -> Dict:
        """Validate critical specifications for the product category"""
        if category not in self.critical_specs:
            return {'valid': True, 'reasons': []}
        
        critical_fields = self.critical_specs[category]
        validation_results = {'valid': True, 'reasons': []}
        
        # Extract specs from names if not provided
        specs1 = product1.get('specs', {})
        specs2 = product2.get('specs', {})
        
        if not specs1:
            specs1 = self.normalizer.extract_specifications(product1.get('name', ''))
        if not specs2:
            specs2 = self.normalizer.extract_specifications(product2.get('name', ''))
        
        # Also extract from names directly
        name_specs1 = self.normalizer.extract_specifications(product1.get('name', ''))
        name_specs2 = self.normalizer.extract_specifications(product2.get('name', ''))
        
        # Merge specs - but don't overwrite existing values with extracted ones
        for key, value in name_specs1.items():
            if key not in specs1:
                specs1[key] = value
        for key, value in name_specs2.items():
            if key not in specs2:
                specs2[key] = value
        
        # Check each critical field
        for field in critical_fields:
            val1 = specs1.get(field)
            val2 = specs2.get(field)
            
            if val1 is not None and val2 is not None:
                # Get tolerance for this category and field
                tolerances = self.spec_tolerances.get(category, self.spec_tolerances['default'])
                tolerance = tolerances.get(field, 0.10)  # Default 10% tolerance
                
                if isinstance(val1, (int, float)) and isinstance(val2, (int, float)):
                    if abs(val1 - val2) > max(val1, val2) * tolerance:
                        validation_results['valid'] = False
                        validation_results['reasons'].append(
                            f"Critical {field} mismatch: {val1} vs {val2} (>{tolerance*100:.0f}% tolerance)"
                        )
                else:
                    # String comparison
                    val1_str = str(val1).lower().strip()
                    val2_str = str(val2).lower().strip()
                    if val1_str != val2_str:
                        # Allow some flexibility for type descriptions
                        if field == 'type':
                            similarity = self._calculate_string_similarity(val1_str, val2_str)
                            if similarity < 0.6:
                                validation_results['valid'] = False
                                validation_results['reasons'].append(
                                    f"Product type mismatch: '{val1}' vs '{val2}'"
                                )
                        else:
                            validation_results['valid'] = False
                            validation_results['reasons'].append(
                                f"Critical {field} mismatch: '{val1}' vs '{val2}'"
                            )
        
        return validation_results
    
    def _match_sku_enhanced(self, sku1: str, sku2: str, name1: str, name2: str, category: str = 'default') -> float:
        """Enhanced SKU matching with model number extraction"""
        # Direct SKU match
        if sku1 and sku2:
            if sku1.lower() == sku2.lower():
                return 1.0
            
            # Normalize and compare
            sku1_norm = re.sub(r'[^a-z0-9]', '', sku1.lower())
            sku2_norm = re.sub(r'[^a-z0-9]', '', sku2.lower())
            
            if sku1_norm == sku2_norm:
                return 0.98
            
            # Partial match (one contains the other)
            if len(sku1_norm) > 4 and len(sku2_norm) > 4:
                if sku1_norm in sku2_norm or sku2_norm in sku1_norm:
                    return 0.85
        
        # Extract model numbers from names
        model1 = self._extract_model_number(name1)
        model2 = self._extract_model_number(name2)
        
        if model1 and model2:
            model1_norm = re.sub(r'[^a-z0-9]', '', model1.lower())
            model2_norm = re.sub(r'[^a-z0-9]', '', model2.lower())
            
            if model1_norm == model2_norm:
                return 0.90
            
            # Stricter matching for air conditioner models
            if category == 'air-conditioner':
                # Extract model parts for comparison
                model1_parts = self._extract_model_parts(model1)
                model2_parts = self._extract_model_parts(model2)
                
                # Require exact series match for air conditioners
                if model1_parts['series'] != model2_parts['series']:
                    return 0.0  # Different series = different product
                
                # If series matches, check other parts
                if model1_parts['capacity'] == model2_parts['capacity'] and model1_parts['suffix'] == model2_parts['suffix']:
                    return 0.95  # Same series, capacity, and suffix
                elif model1_parts['capacity'] == model2_parts['capacity']:
                    return 0.70  # Same series and capacity, different suffix (might be variant)
                else:
                    return 0.30  # Same series but different capacity
            
            # For other products, use original logic
            if len(model1_norm) > 4 and len(model2_norm) > 4:
                if model1_norm in model2_norm or model2_norm in model1_norm:
                    return 0.75
                    
                # Similarity score for models
                similarity = self._calculate_string_similarity(model1_norm, model2_norm)
                if similarity > 0.8:
                    return similarity * 0.8
        
        return 0.0
    
    def _match_specifications_enhanced(
        self,
        specs1: Dict,
        specs2: Dict,
        name1: str,
        name2: str,
        category: str
    ) -> Tuple[float, Dict]:
        """Enhanced specification matching with category-specific tolerances"""
        
        # Extract specs from names if not provided
        if not specs1:
            specs1 = self.normalizer.extract_specifications(name1)
        if not specs2:
            specs2 = self.normalizer.extract_specifications(name2)
        
        # Also extract additional specs from names
        name_specs1 = self.normalizer.extract_specifications(name1)
        name_specs2 = self.normalizer.extract_specifications(name2)
        
        # Merge specs - prioritize provided specs over extracted ones
        merged_specs1 = {**name_specs1, **specs1}
        merged_specs2 = {**name_specs2, **specs2}
        
        if not merged_specs1 and not merged_specs2:
            return 0.5, {}  # No specs to compare
        
        # Get tolerances for this category
        tolerances = self.spec_tolerances.get(category, self.spec_tolerances['default'])
        
        matched_specs = {}
        total_score = 0
        spec_count = 0
        
        # Compare each specification
        for spec_name in set(merged_specs1.keys()).union(merged_specs2.keys()):
            val1 = merged_specs1.get(spec_name)
            val2 = merged_specs2.get(spec_name)
            
            if val1 is None or val2 is None:
                continue
            
            spec_count += 1
            tolerance = tolerances.get(spec_name, 0.10)  # Default 10% tolerance
            
            # Numeric specifications
            if isinstance(val1, (int, float)) and isinstance(val2, (int, float)):
                max_val = max(val1, val2)
                if max_val == 0:
                    score = 1.0 if val1 == val2 else 0.0
                else:
                    diff = abs(val1 - val2) / max_val
                    if diff <= tolerance:
                        score = 1.0 - (diff / tolerance) * 0.2  # Small penalty for differences
                    else:
                        score = max(0.0, 1.0 - (diff / tolerance))  # Steep penalty for large differences
                
                total_score += score
                matched_specs[spec_name] = {
                    'match': score > 0.7,
                    'score': score,
                    'values': [val1, val2],
                    'tolerance': tolerance
                }
            # String specifications
            else:
                val1_str = str(val1).lower()
                val2_str = str(val2).lower()
                if val1_str == val2_str:
                    score = 1.0
                else:
                    similarity = self._calculate_string_similarity(val1_str, val2_str)
                    score = similarity
                
                total_score += score
                matched_specs[spec_name] = {
                    'match': score > 0.8,
                    'score': score,
                    'values': [val1, val2]
                }
        
        final_score = total_score / spec_count if spec_count > 0 else 0.5
        
        return final_score, matched_specs
    
    def _match_names_conservative(self, name1: str, name2: str) -> float:
        """Conservative name matching to reduce false positives"""
        if not name1 or not name2:
            return 0.0
        
        # Normalize names
        norm1 = self.normalizer.normalize(name1)
        norm2 = self.normalizer.normalize(name2)
        
        # Extract important tokens (brands, models, specifications)
        tokens1 = set(self.normalizer.extract_tokens(name1))
        tokens2 = set(self.normalizer.extract_tokens(name2))
        
        if not tokens1 or not tokens2:
            return 0.0
        
        # Focus on important token overlap rather than all tokens
        important_tokens1 = self._extract_important_tokens(tokens1)
        important_tokens2 = self._extract_important_tokens(tokens2)
        
        if not important_tokens1 or not important_tokens2:
            # Fall back to regular token comparison but with lower weight
            intersection = tokens1.intersection(tokens2)
            union = tokens1.union(tokens2)
            jaccard = len(intersection) / len(union) if union else 0
            return jaccard * 0.8  # Reduce score when no important tokens
        
        # Calculate important token overlap
        important_intersection = important_tokens1.intersection(important_tokens2)
        important_union = important_tokens1.union(important_tokens2)
        
        if not important_union:
            return 0.0
        
        important_jaccard = len(important_intersection) / len(important_union)
        
        # Bonus for model/brand matches
        brand_bonus = 0.0
        model_bonus = 0.0
        
        # Check for brand overlap
        for token in important_intersection:
            if len(token) > 3 and any(brand in token.lower() for brand in ['daikin', 'mitsubishi', 'samsung', 'lg', 'panasonic', 'toshiba']):
                brand_bonus = 0.1
                break
        
        # Check for model number overlap
        for token in important_intersection:
            if re.match(r'^[A-Z0-9]{4,}$', token.upper()):
                model_bonus = 0.15
                break
        
        final_score = important_jaccard + brand_bonus + model_bonus
        return min(1.0, final_score)
    
    def _extract_important_tokens(self, tokens: Set[str]) -> Set[str]:
        """Extract tokens that are important for matching (brands, models, specs)"""
        important = set()
        
        for token in tokens:
            # Brand names
            if token.lower() in ['daikin', 'mitsubishi', 'samsung', 'lg', 'panasonic', 'toshiba', 'sharp', 'haier']:
                important.add(token)
            # Model-like patterns
            elif re.match(r'^[A-Z]{2,6}\d{2,6}[A-Z0-9]*$', token.upper()):
                important.add(token)
            # Technical specifications
            elif any(spec in token.lower() for spec in ['btu', 'watt', 'volt', 'inverter', 'hp']):
                important.add(token)
            # Numbers (could be model numbers or specifications)
            elif re.match(r'^\d{3,}$', token):
                important.add(token)
        
        return important
    
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
    
    def _match_category(self, category1: str, category2: str) -> float:
        """Match product categories"""
        if not category1 or not category2:
            return 0.5
        
        cat1_norm = category1.lower().strip()
        cat2_norm = category2.lower().strip()
        
        if cat1_norm == cat2_norm:
            return 1.0
        
        # Check for category similarity
        similarity = self._calculate_string_similarity(cat1_norm, cat2_norm)
        return similarity
    
    def _check_price_consistency(self, price1: Optional[float], price2: Optional[float]) -> Dict:
        """Check if prices are reasonably consistent"""
        if not price1 or not price2:
            return {'consistent': True, 'variance': 0, 'warning': ''}
        
        variance = abs(price1 - price2) / max(price1, price2)
        
        if variance > 1.0:  # More than 100% difference
            return {
                'consistent': False,
                'variance': variance,
                'warning': f'Extreme price difference: {variance*100:.1f}%'
            }
        elif variance > 0.5:  # More than 50% difference
            return {
                'consistent': False,
                'variance': variance,
                'warning': f'Large price difference: {variance*100:.1f}%'
            }
        
        return {'consistent': True, 'variance': variance, 'warning': ''}
    
    def _calculate_string_similarity(self, str1: str, str2: str) -> float:
        """Calculate string similarity using multiple methods"""
        if not str1 or not str2:
            return 0.0
        
        # Jaccard similarity
        set1 = set(str1.lower().split())
        set2 = set(str2.lower().split())
        
        if not set1 and not set2:
            return 1.0
        elif not set1 or not set2:
            return 0.0
        
        intersection = set1.intersection(set2)
        union = set1.union(set2)
        
        jaccard = len(intersection) / len(union)
        
        # Character-level similarity
        from difflib import SequenceMatcher
        char_similarity = SequenceMatcher(None, str1.lower(), str2.lower()).ratio()
        
        # Combined score
        return (jaccard * 0.7 + char_similarity * 0.3)