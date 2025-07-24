"""
Ultra-Strict Product Matcher with enhanced model differentiation
Fixes false positives when products have similar but different model numbers
"""
import re
import logging
from typing import Dict, List, Tuple, Optional, Set
from dataclasses import dataclass
from collections import defaultdict
import math
from decimal import Decimal
from difflib import SequenceMatcher

from src.utils.text_normalizer_enhanced import EnhancedTextNormalizer

logger = logging.getLogger(__name__)

@dataclass
class MatchResult:
    """Enhanced match result with detailed scoring"""
    confidence: float
    match_type: str  # 'exact', 'high', 'medium', 'low', 'none'
    details: Dict[str, any]
    matched_fields: List[str]
    warnings: List[str]
    rejection_reasons: List[str]

class UltraStrictProductMatcher:
    """Ultra-strict product matcher with enhanced model differentiation"""
    
    def __init__(self):
        self.normalizer = EnhancedTextNormalizer()
        
        # Weights for different matching components
        self.weights = {
            'sku': 0.45,      # Increased SKU weight - most critical
            'brand': 0.20,    # Brand match
            'name': 0.10,     # Reduced name weight further
            'specs': 0.20,    # Specification match
            'category': 0.05  # Category match
        }
        
        # Much stricter thresholds to prevent false positives
        self.thresholds = {
            'exact': 0.99,    # Near perfect match required
            'high': 0.90,     # High confidence threshold raised significantly
            'medium': 0.80,   # Medium threshold raised significantly
            'low': 0.70,      # Low threshold raised significantly
            'minimum': 0.60   # Minimum to even consider
        }
        
        # Enhanced specification tolerances by category
        self.spec_tolerances = {
            # Air conditioners - very strict tolerances
            'air-conditioner': {
                'btu': 0.02,       # Only 2% BTU tolerance for AC units
                'power': 0.03,     # 3% power tolerance
                'capacity': 0.02,  # 2% capacity tolerance
                'voltage': 0.01,   # 1% voltage tolerance
                'size': 0.05,      # 5% size tolerance
            },
            # Refrigerators - strict capacity tolerance
            'refrigerator': {
                'capacity': 0.05,  # 5% capacity tolerance
                'volume': 0.05,    # 5% volume tolerance
                'power': 0.08,     # 8% power tolerance
                'size': 0.08,      # 8% size tolerance
            },
            # Default tolerances for other categories
            'default': {
                'size': 0.08,      # 8% tolerance for sizes
                'capacity': 0.08,  # 8% tolerance for capacity
                'power': 0.10,     # 10% tolerance for power ratings
                'weight': 0.08,    # 8% tolerance for weight
                'voltage': 0.03,   # 3% tolerance for voltage
            }
        }
        
        # Critical specification mismatches that should prevent matching
        self.critical_specs = {
            'air-conditioner': ['btu', 'power', 'capacity', 'type', 'model'],
            'refrigerator': ['capacity', 'volume', 'type', 'model'],
            'washing-machine': ['capacity', 'type', 'model'],
            'television': ['size', 'resolution', 'model'],
        }
        
        # Model number patterns (enhanced for better extraction)
        self.model_patterns = [
            r'\b([A-Z]{2,6}[\-]?\d{2,6}[A-Z0-9\-]*)\b',  # Standard model codes with optional dashes
            r'\b(รุ่น\s*([A-Z0-9\-]+))',                  # Thai "model" prefix
            r'\b(model\s*([A-Z0-9\-]+))',                 # English "model" prefix
            r'\b([A-Z]+\d+[A-Z]*[0-9]*[A-Z]*)\b',        # Flexible model pattern
        ]
        
        # Enhanced model similarity patterns
        self.model_similarity_patterns = [
            # Letters followed by numbers pattern
            r'^([A-Z]+)(\d+)([A-Z0-9]*)$',
            # Complex patterns for different manufacturers
            r'^([A-Z]{2,4})[\-]?(\d{1,3})([A-Z0-9\-]*)$',
        ]
    
    def match_products(
        self,
        product1: Dict[str, any],
        product2: Dict[str, any],
        category: str = 'default'
    ) -> MatchResult:
        """
        Match two products with ultra-strict validation
        
        Args:
            product1: First product dict
            product2: Second product dict  
            category: Product category for category-specific rules
            
        Returns:
            MatchResult with confidence score and details
        """
        # Normalize category to handle both underscore and hyphen formats
        category = self._normalize_category(category)
        scores = {}
        matched_fields = []
        warnings = []
        rejection_reasons = []
        
        # Early rejection checks (enhanced)
        early_rejection = self._check_early_rejection_strict(product1, product2, category)
        if early_rejection:
            return MatchResult(
                confidence=0.0,
                match_type='none',
                details={'early_rejection': True},
                matched_fields=[],
                warnings=[],
                rejection_reasons=early_rejection
            )
        
        # 1. Ultra-strict SKU/Model matching
        sku_score = self._match_sku_ultra_strict(
            product1.get('sku', ''),
            product2.get('sku', ''),
            product1.get('name', ''),
            product2.get('name', ''),
            category
        )
        scores['sku'] = sku_score
        
        # If SKU/model score is very low, likely different products
        if sku_score < 0.5:  # Raised threshold from 0.3 to 0.5
            rejection_reasons.append(f"Model/SKU mismatch: {sku_score:.3f} below threshold")
            return MatchResult(
                confidence=0.0,
                match_type='none',
                details={'sku_rejection': True, 'sku_score': sku_score},
                matched_fields=[],
                warnings=[],
                rejection_reasons=rejection_reasons
            )
        
        if sku_score > 0.9:
            matched_fields.append('sku')
        elif sku_score < 0.5:
            warnings.append("Low SKU/Model similarity detected")
        
        # 2. Brand matching
        brand_score = self._match_brand_strict(
            product1.get('brand', ''),
            product2.get('brand', ''),
            product1.get('name', ''),
            product2.get('name', '')
        )
        scores['brand'] = brand_score
        if brand_score > 0.9:
            matched_fields.append('brand')
        elif brand_score < 0.8:
            warnings.append("Brand mismatch detected")
            # For ultra-strict matching, significant brand differences should be rejected
            if brand_score < 0.6:
                rejection_reasons.append(f"Brand mismatch: {brand_score:.3f} below threshold")
                return MatchResult(
                    confidence=0.0,
                    match_type='none',
                    details={'brand_rejection': True, 'brand_score': brand_score},
                    matched_fields=[],
                    warnings=warnings,
                    rejection_reasons=rejection_reasons
                )
        
        # 3. Ultra-strict specification validation
        spec_validation = self._validate_critical_specs_strict(
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
        spec_score, spec_details = self._match_specifications_strict(
            product1.get('specs', {}),
            product2.get('specs', {}),
            product1.get('name', ''),
            product2.get('name', ''),
            category
        )
        scores['specs'] = spec_score
        if spec_score > 0.8:
            matched_fields.append('specifications')
        
        # 5. Conservative name similarity
        name_score = self._match_names_ultra_conservative(
            product1.get('name', ''),
            product2.get('name', ''),
            category
        )
        scores['name'] = name_score
        if name_score > 0.9:
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
        
        # Confidence boost for perfect critical spec matches
        # This helps legitimate matches with identical models/BTU but slightly different names
        if category == 'air-conditioner':
            model1 = self._extract_model_number_enhanced(product1.get('name', ''))
            model2 = self._extract_model_number_enhanced(product2.get('name', ''))
            btu1 = self._extract_btu_enhanced(product1.get('name', ''))
            btu2 = self._extract_btu_enhanced(product2.get('name', ''))
            
            perfect_critical_match = False
            if model1 and model2 and model1 == model2:  # Identical models
                if btu1 and btu2 and btu1 == btu2:      # Identical BTU
                    perfect_critical_match = True
                    confidence += 0.15  # Boost for perfect critical spec match
                    
        # Additional model validation penalty
        model_penalty = self._calculate_model_penalty(
            product1.get('name', ''),
            product2.get('name', ''),
            product1.get('sku', ''),
            product2.get('sku', '')
        )
        confidence *= (1.0 - model_penalty)
        
        # Price consistency check
        price_check = self._check_price_consistency_strict(
            product1.get('price'),
            product2.get('price')
        )
        if not price_check['consistent']:
            warnings.append(price_check['warning'])
            confidence *= 0.8  # Reduce confidence for price inconsistencies
        
        # Determine match type with stricter thresholds
        match_type = 'none'
        for type_name, threshold in sorted(self.thresholds.items(), key=lambda x: -x[1]):
            if type_name == 'minimum':
                continue
            if confidence >= threshold:
                match_type = type_name
                break
        
        # Final rejection for low confidence
        if confidence < self.thresholds['minimum']:
            match_type = 'none'
            rejection_reasons.append(f"Final confidence {confidence:.3f} below minimum threshold {self.thresholds['minimum']}")
        
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
            'model_penalty': model_penalty,
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
    
    def _check_early_rejection_strict(self, product1: Dict, product2: Dict, category: str) -> List[str]:
        """Enhanced early rejection checks"""
        rejections = []
        
        # Extract model numbers for strict comparison
        model1 = self._extract_model_number_enhanced(product1.get('name', ''))
        model2 = self._extract_model_number_enhanced(product2.get('name', ''))
        
        if model1 and model2:
            # Exact model comparison first
            if model1.upper() != model2.upper():
                # Check if models are genuinely different
                similarity = self._calculate_model_similarity(model1, model2)
                if similarity < 0.5:  # If models are less than 50% similar (stricter)
                    rejections.append(f"Model mismatch: {model1} vs {model2} (similarity: {similarity:.3f})")
        
        # Enhanced BTU validation for air conditioners
        if category == 'air-conditioner':
            btu1 = self._extract_btu_enhanced(product1.get('name', ''))
            btu2 = self._extract_btu_enhanced(product2.get('name', ''))
            
            if btu1 and btu2:
                btu_diff = abs(btu1 - btu2) / max(btu1, btu2)
                if btu_diff > 0.05:  # Only 5% BTU tolerance
                    rejections.append(f"BTU mismatch: {btu1:,} vs {btu2:,} ({btu_diff*100:.1f}% difference)")
        
        return rejections
    
    def _extract_model_number_enhanced(self, text: str) -> Optional[str]:
        """Enhanced model number extraction with better accuracy"""
        # Try each pattern and return the most likely model
        candidates = []
        
        for pattern in self.model_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                if isinstance(match, tuple):
                    # Extract the actual model from tuple
                    model = match[1] if len(match) > 1 and match[1] else match[0]
                else:
                    model = match
                
                # Clean the model
                model = model.strip().upper()
                
                # Validate model format
                if self._is_valid_model_format(model):
                    candidates.append(model)
        
        # Return the most likely candidate (longest valid model)
        if candidates:
            return max(candidates, key=len)
        
        return None
    
    def _is_valid_model_format(self, model: str) -> bool:
        """Check if a string looks like a valid model number"""
        # Must have letters and numbers
        if not re.search(r'[A-Z]', model) or not re.search(r'\d', model):
            return False
        
        # Must be reasonable length
        if len(model) < 3 or len(model) > 20:
            return False
        
        # Should not be common words
        common_words = ['AIR', 'CONDITIONER', 'BTU', 'WATT', 'VOLT', 'POWER']
        if model in common_words:
            return False
        
        return True
    
    def _calculate_model_similarity(self, model1: str, model2: str) -> float:
        """Calculate similarity between two model numbers - ULTRA STRICT"""
        if not model1 or not model2:
            return 0.0
        
        # Normalize models
        m1 = re.sub(r'[^A-Z0-9]', '', model1.upper())
        m2 = re.sub(r'[^A-Z0-9]', '', model2.upper())
        
        # If identical, return 1.0
        if m1 == m2:
            return 1.0
        
        # For ultra-strict matching, any difference in model numbers should be heavily penalized
        # This is especially important for similar models like HSU-13CQRD vs HSU-12CQRD
        
        # Try to decompose models into parts
        parts1 = self._decompose_model(m1)
        parts2 = self._decompose_model(m2)
        
        similarity = 0.0
        
        # Compare prefix (series) - must be identical
        if parts1['prefix'] == parts2['prefix']:
            similarity += 0.3  # Reduced from 0.4
        else:
            # Different prefix = different product line
            return 0.0
        
        # Compare numeric part - must be identical for high similarity
        if parts1['numeric'] == parts2['numeric']:
            similarity += 0.5  # Increased importance
        elif parts1['numeric'] and parts2['numeric']:
            try:
                num1 = int(parts1['numeric'])
                num2 = int(parts2['numeric'])
                # Any numeric difference is highly penalized
                if abs(num1 - num2) == 1:
                    similarity += 0.1  # Very low score for adjacent numbers
                else:
                    similarity += 0.0  # No score for larger differences
            except ValueError:
                pass
        
        # Compare suffix - must be identical
        if parts1['suffix'] == parts2['suffix']:
            similarity += 0.2
        else:
            # Different suffix typically means different variant
            similarity *= 0.5  # Reduce overall similarity
        
        # Apply ultra-strict penalty for any differences
        if similarity < 1.0:
            similarity *= 0.4  # Heavily penalize any model differences
        
        return similarity
    
    def _decompose_model(self, model: str) -> Dict[str, str]:
        """Decompose a model number into prefix, numeric, and suffix parts"""
        parts = {'prefix': '', 'numeric': '', 'suffix': ''}
        
        # Try different decomposition patterns
        for pattern in self.model_similarity_patterns:
            match = re.match(pattern, model)
            if match:
                parts['prefix'] = match.group(1)
                parts['numeric'] = match.group(2)
                parts['suffix'] = match.group(3) if len(match.groups()) > 2 else ''
                return parts
        
        # Fallback: simple decomposition
        # Find first number sequence
        num_match = re.search(r'(\d+)', model)
        if num_match:
            start = num_match.start()
            end = num_match.end()
            parts['prefix'] = model[:start]
            parts['numeric'] = model[start:end]
            parts['suffix'] = model[end:]
        else:
            parts['prefix'] = model
        
        return parts
    
    def _match_sku_ultra_strict(self, sku1: str, sku2: str, name1: str, name2: str, category: str = 'default') -> float:
        """Ultra-strict SKU matching with enhanced model validation"""
        # Direct SKU match - but ignore pure numeric IDs (likely internal product IDs)
        if sku1 and sku2:
            # Check if both SKUs are pure numeric (likely internal IDs, not real SKUs)
            if sku1.isdigit() and sku2.isdigit():
                # Ignore numeric IDs and fall through to model extraction
                pass
            else:
                if sku1.upper() == sku2.upper():
                    return 1.0
                
                # Calculate similarity
                similarity = self._calculate_model_similarity(sku1, sku2)
                if similarity >= 0.95:
                    return 0.98
                elif similarity >= 0.8:
                    return 0.7  # Reduced score for similar but not identical
                elif similarity >= 0.6:
                    return 0.4  # Low score for somewhat similar
                else:
                    return 0.0  # No match for different models
        
        # Extract model numbers from names
        model1 = self._extract_model_number_enhanced(name1)
        model2 = self._extract_model_number_enhanced(name2)
        
        if model1 and model2:
            similarity = self._calculate_model_similarity(model1, model2)
            if similarity >= 0.95:
                return 0.95  # Increased from 0.90 for near-perfect matches
            elif similarity >= 0.8:
                return 0.75  # Increased from 0.65
            elif similarity >= 0.6:
                return 0.45  # Increased from 0.35
            else:
                return 0.0  # No match
        
        return 0.0
    
    def _calculate_model_penalty(self, name1: str, name2: str, sku1: str, sku2: str) -> float:
        """Calculate penalty for model differences"""
        penalty = 0.0
        
        # Extract models from both sources
        models1 = set()
        models2 = set()
        
        if sku1:
            models1.add(sku1.upper())
        if sku2:
            models2.add(sku2.upper())
        
        name_model1 = self._extract_model_number_enhanced(name1)
        name_model2 = self._extract_model_number_enhanced(name2)
        
        if name_model1:
            models1.add(name_model1.upper())
        if name_model2:
            models2.add(name_model2.upper())
        
        # Calculate penalty based on model differences
        if models1 and models2:
            max_similarity = 0.0
            for m1 in models1:
                for m2 in models2:
                    similarity = self._calculate_model_similarity(m1, m2)
                    max_similarity = max(max_similarity, similarity)
            
            # Penalty increases as similarity decreases
            penalty = 1.0 - max_similarity
            
            # Apply stricter penalty for air conditioners
            if 'air-conditioner' in [name1.lower(), name2.lower()]:
                penalty *= 1.5  # Increase penalty for AC products
        
        return min(penalty, 0.8)  # Cap penalty at 80%
    
    def _normalize_category(self, category: str) -> str:
        """Normalize category format to handle both underscore and hyphen formats"""
        if not category:
            return 'default'
        
        # Convert underscore to hyphen for consistent category handling
        normalized = category.lower().replace('_', '-')
        
        # Map known categories
        category_mapping = {
            'air-conditioner': 'air-conditioner',
            'refrigerator': 'refrigerator',
            'washing-machine': 'washing-machine',
            'television': 'television',
            'default': 'default'
        }
        
        return category_mapping.get(normalized, 'default')
    
    def _extract_btu_enhanced(self, text: str) -> Optional[int]:
        """Enhanced BTU extraction"""
        patterns = [
            r'(\d+(?:,\d+)?)\s*(?:btu|บีทียู|BTU)',
            r'(\d+(?:,\d+)?)\s*(?:บีทียู/ชม\.?|BTU/HR?)',
            r'(\d+(?:,\d+)?)\s*(?:บีทียู/ชั่วโมง)',
            r'(\d+(?:,\d+)?)\s*(?:บีทียู)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                btu_str = match.group(1).replace(',', '')
                try:
                    return int(btu_str)
                except ValueError:
                    continue
        return None
    
    def _validate_critical_specs_strict(self, product1: Dict, product2: Dict, category: str) -> Dict:
        """Stricter critical specification validation with improved handling for legitimate matches"""
        if category not in self.critical_specs:
            return {'valid': True, 'reasons': []}
        
        critical_fields = self.critical_specs[category]
        validation_results = {'valid': True, 'reasons': []}
        
        # Extract specs from names and provided specs
        specs1 = self._get_all_specs(product1)
        specs2 = self._get_all_specs(product2)
        
        # Check each critical field with stricter validation
        for field in critical_fields:
            val1 = specs1.get(field)
            val2 = specs2.get(field)
            
            if field == 'model':
                # Always use the dedicated model extractor for consistency
                model1 = self._extract_model_number_enhanced(product1.get('name', ''))
                model2 = self._extract_model_number_enhanced(product2.get('name', ''))
                
                if model1 and model2:
                    similarity = self._calculate_model_similarity(model1, model2)
                    if similarity < 0.8:
                        validation_results['valid'] = False
                        validation_results['reasons'].append(
                            f"Model mismatch: {model1} vs {model2} (similarity: {similarity:.3f})"
                        )
            elif field == 'power' and category == 'air-conditioner':
                # Special handling for air conditioner power vs BTU confusion
                # For air conditioners, BTU is the cooling power and should be compared instead
                btu1 = specs1.get('btu') or self._extract_btu_enhanced(product1.get('name', ''))
                btu2 = specs2.get('btu') or self._extract_btu_enhanced(product2.get('name', ''))
                
                # If we have BTU values, use those instead of the problematic power extraction
                if btu1 and btu2:
                    btu_diff = abs(btu1 - btu2) / max(btu1, btu2)
                    tolerance = self.spec_tolerances.get(category, {}).get('btu', 0.02)  # 2% BTU tolerance
                    if btu_diff > tolerance:
                        validation_results['valid'] = False
                        validation_results['reasons'].append(
                            f"BTU mismatch: {btu1:,} vs {btu2:,} ({btu_diff*100:.1f}% difference > {tolerance*100:.0f}%)"
                        )
                elif val1 is not None and val2 is not None:
                    # Fall back to power comparison only if BTU not available
                    if isinstance(val1, (int, float)) and isinstance(val2, (int, float)):
                        tolerances = self.spec_tolerances.get(category, self.spec_tolerances['default'])
                        tolerance = tolerances.get(field, 0.05)
                        
                        if abs(val1 - val2) > max(val1, val2) * tolerance:
                            validation_results['valid'] = False
                            validation_results['reasons'].append(
                                f"Critical {field} mismatch: {val1} vs {val2} (>{tolerance*100:.0f}% tolerance)"
                            )
            elif val1 is not None and val2 is not None:
                # Standard numeric validation with stricter tolerances
                if isinstance(val1, (int, float)) and isinstance(val2, (int, float)):
                    tolerances = self.spec_tolerances.get(category, self.spec_tolerances['default'])
                    tolerance = tolerances.get(field, 0.05)  # Default 5% tolerance
                    
                    if abs(val1 - val2) > max(val1, val2) * tolerance:
                        validation_results['valid'] = False
                        validation_results['reasons'].append(
                            f"Critical {field} mismatch: {val1} vs {val2} (>{tolerance*100:.0f}% tolerance)"
                        )
        
        return validation_results
    
    def _get_all_specs(self, product: Dict) -> Dict:
        """Get all specifications from both provided specs and extracted from name"""
        specs = product.get('specs', {}).copy()
        
        # Extract additional specs from name
        name_specs = self.normalizer.extract_specifications(product.get('name', ''))
        
        # Add extracted specs that aren't already present
        for key, value in name_specs.items():
            if key not in specs:
                specs[key] = value
        
        return specs
    
    def _match_specifications_strict(self, specs1: Dict, specs2: Dict, name1: str, name2: str, category: str) -> Tuple[float, Dict]:
        """Strict specification matching"""
        # Get all specs including extracted ones
        all_specs1 = specs1.copy()
        all_specs2 = specs2.copy()
        
        # Extract from names
        name_specs1 = self.normalizer.extract_specifications(name1)
        name_specs2 = self.normalizer.extract_specifications(name2)
        
        # Merge specs
        for key, value in name_specs1.items():
            if key not in all_specs1:
                all_specs1[key] = value
        for key, value in name_specs2.items():
            if key not in all_specs2:
                all_specs2[key] = value
        
        if not all_specs1 and not all_specs2:
            return 0.5, {}
        
        # Get strict tolerances
        tolerances = self.spec_tolerances.get(category, self.spec_tolerances['default'])
        
        matched_specs = {}
        total_score = 0
        spec_count = 0
        
        # Compare specifications with strict validation
        for spec_name in set(all_specs1.keys()).union(all_specs2.keys()):
            val1 = all_specs1.get(spec_name)
            val2 = all_specs2.get(spec_name)
            
            if val1 is None or val2 is None:
                continue
            
            spec_count += 1
            tolerance = tolerances.get(spec_name, 0.05)  # Default 5% tolerance
            
            if isinstance(val1, (int, float)) and isinstance(val2, (int, float)):
                max_val = max(val1, val2)
                if max_val == 0:
                    score = 1.0 if val1 == val2 else 0.0
                else:
                    diff = abs(val1 - val2) / max_val
                    if diff <= tolerance:
                        score = 1.0 - (diff / tolerance) * 0.1  # Small penalty
                    else:
                        score = 0.0  # No score for out-of-tolerance differences
                
                total_score += score
                matched_specs[spec_name] = {
                    'match': score > 0.8,
                    'score': score,
                    'values': [val1, val2],
                    'tolerance': tolerance
                }
            else:
                # String comparison
                val1_str = str(val1).lower()
                val2_str = str(val2).lower()
                score = 1.0 if val1_str == val2_str else 0.0
                
                total_score += score
                matched_specs[spec_name] = {
                    'match': score > 0.9,
                    'score': score,
                    'values': [val1, val2]
                }
        
        final_score = total_score / spec_count if spec_count > 0 else 0.5
        return final_score, matched_specs
    
    def _match_names_ultra_conservative(self, name1: str, name2: str, category: str) -> float:
        """Ultra-conservative name matching"""
        if not name1 or not name2:
            return 0.0
        
        # Focus on model numbers in names
        model1 = self._extract_model_number_enhanced(name1)
        model2 = self._extract_model_number_enhanced(name2)
        
        if model1 and model2:
            # If models are different, reduce name score significantly
            model_similarity = self._calculate_model_similarity(model1, model2)
            if model_similarity < 0.8:
                return 0.2  # Very low score for different models
        
        # Standard name comparison
        norm1 = self.normalizer.normalize(name1)
        norm2 = self.normalizer.normalize(name2)
        
        # Calculate basic similarity
        similarity = SequenceMatcher(None, norm1, norm2).ratio()
        
        # Apply penalties for differences
        if category == 'air-conditioner':
            # Extract BTU from names
            btu1 = self._extract_btu_enhanced(name1)
            btu2 = self._extract_btu_enhanced(name2)
            
            if btu1 and btu2 and btu1 != btu2:
                similarity *= 0.5  # Reduce score for different BTU
        
        return similarity
    
    def _match_brand_strict(self, brand1: str, brand2: str, name1: str, name2: str) -> float:
        """Strict brand matching"""
        if not brand1:
            brand1 = self.normalizer.extract_brand(name1) or ''
        if not brand2:
            brand2 = self.normalizer.extract_brand(name2) or ''
        
        if not brand1 or not brand2:
            return 0.5
        
        brand1_norm = self.normalizer.normalize(brand1)
        brand2_norm = self.normalizer.normalize(brand2)
        
        if brand1_norm == brand2_norm:
            return 1.0
        
        # Very strict brand matching - small differences matter
        similarity = SequenceMatcher(None, brand1_norm, brand2_norm).ratio()
        return similarity if similarity > 0.9 else 0.0
    
    def _match_category(self, category1: str, category2: str) -> float:
        """Match product categories"""
        if not category1 or not category2:
            return 0.5
        
        cat1_norm = category1.lower().strip()
        cat2_norm = category2.lower().strip()
        
        return 1.0 if cat1_norm == cat2_norm else 0.0
    
    def _check_price_consistency_strict(self, price1: Optional[float], price2: Optional[float]) -> Dict:
        """Strict price consistency check"""
        if not price1 or not price2:
            return {'consistent': True, 'variance': 0, 'warning': ''}
        
        variance = abs(price1 - price2) / max(price1, price2)
        
        if variance > 0.8:  # More than 80% difference
            return {
                'consistent': False,
                'variance': variance,
                'warning': f'Extreme price difference: {variance*100:.1f}%'
            }
        elif variance > 0.4:  # More than 40% difference
            return {
                'consistent': False,
                'variance': variance,
                'warning': f'Large price difference: {variance*100:.1f}%'
            }
        
        return {'consistent': True, 'variance': variance, 'warning': ''}