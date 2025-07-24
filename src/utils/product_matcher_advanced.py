"""
Advanced Product Matcher with improved Thai-English multilingual support
Uses phonetic matching, n-grams, and contextual scoring
"""
import re
import logging
import math
from typing import Dict, List, Tuple, Optional, Set, Any
from dataclasses import dataclass
from collections import defaultdict, Counter
from decimal import Decimal
import unicodedata
from difflib import SequenceMatcher

from src.utils.text_normalizer_advanced import AdvancedTextNormalizer

logger = logging.getLogger(__name__)

@dataclass
class AdvancedMatchResult:
    """Enhanced match result with detailed multilingual scoring"""
    confidence: float
    match_type: str  # 'exact', 'high', 'medium', 'low', 'none'
    details: Dict[str, float]
    matched_fields: List[str]
    warnings: List[str]
    linguistic_scores: Dict[str, float]  # Phonetic, n-gram, semantic scores
    
class AdvancedProductMatcher:
    """Advanced product matcher with multilingual and contextual support"""
    
    def __init__(self):
        self.normalizer = AdvancedTextNormalizer()
        
        # Dynamic weights based on product category
        self.weight_profiles = {
            'electronics': {
                'sku': 0.40,      # Model numbers are critical
                'brand': 0.25,    
                'specs': 0.20,    # Technical specs important
                'name': 0.10,     
                'category': 0.05  
            },
            'appliances': {
                'sku': 0.35,      
                'brand': 0.25,    
                'specs': 0.20,    # Size, capacity important
                'name': 0.15,     
                'category': 0.05  
            },
            'general': {
                'sku': 0.30,      
                'brand': 0.25,    
                'name': 0.25,     # Name more important for general items
                'specs': 0.15,    
                'category': 0.05  
            }
        }
        
        # Adaptive thresholds
        self.thresholds = {
            'exact': 0.95,
            'high': 0.85,
            'medium': 0.70,
            'low': 0.55
        }
        
        # N-gram settings
        self.ngram_sizes = [2, 3, 4]  # Character n-grams
        
        # Phonetic patterns for Thai-English
        self.phonetic_patterns = self._build_phonetic_patterns()
        
        # Specification tolerances with context
        self.spec_tolerances = {
            'size': {'default': 0.01, 'display': 0.005},      
            'capacity': {'default': 0.02, 'cooling': 0.05},   
            'power': {'default': 0.05, 'exact': 0.01},        
            'weight': {'default': 0.03},
            'voltage': {'default': 0.01},
            'frequency': {'default': 0.001}
        }
        
    def _build_phonetic_patterns(self) -> Dict[str, List[str]]:
        """Build phonetic matching patterns for Thai-English transliteration"""
        return {
            # Common Thai phonetic variations in English
            'ph': ['พ', 'ภ', 'ฟ'],
            'th': ['ท', 'ธ', 'ต', 'ถ'],
            'ch': ['ช', 'ฉ', 'จ'],
            'kh': ['ค', 'ข'],
            'ng': ['ง'],
            's': ['ส', 'ศ', 'ซ'],
            'r': ['ร', 'ล'],  # L/R confusion common
            'l': ['ล', 'ร'],
            'n': ['น', 'ณ'],
            'm': ['ม'],
            'k': ['ก', 'ค'],
            't': ['ต', 'ท'],
            'p': ['ป', 'พ'],
            'b': ['บ', 'พ'],
            'd': ['ด', 'ต'],
            # Vowel patterns
            'a': ['า', 'ะ', 'ั'],
            'i': ['ิ', 'ี'],
            'u': ['ุ', 'ู'],
            'e': ['เ', 'แ'],
            'o': ['โ', 'อ'],
            'ae': ['แ'],
            'ai': ['ไ', 'ใ'],
            'ue': ['ื', 'ึ'],
            'oe': ['เอ'],
        }
    
    def match_products(
        self,
        product1: Dict[str, Any],
        product2: Dict[str, Any],
        category_hint: Optional[str] = None
    ) -> AdvancedMatchResult:
        """
        Match two products with advanced multilingual support
        
        Args:
            product1: First product dict
            product2: Second product dict
            category_hint: Optional category for contextual matching
            
        Returns:
            AdvancedMatchResult with detailed scoring
        """
        # Determine weight profile based on category
        category = category_hint or self._infer_category(product1, product2)
        weights = self.weight_profiles.get(category, self.weight_profiles['general'])
        
        scores = {}
        linguistic_scores = {}
        matched_fields = []
        warnings = []
        
        # 1. SKU/Model matching with fuzzy support
        sku_score, sku_linguistic = self._match_sku_advanced(
            product1.get('sku', ''),
            product2.get('sku', ''),
            product1.get('name', ''),
            product2.get('name', '')
        )
        scores['sku'] = sku_score
        linguistic_scores['sku'] = sku_linguistic
        if sku_score > 0.8:
            matched_fields.append('sku')
        
        # 2. Brand matching with phonetic support
        brand_score, brand_linguistic = self._match_brand_advanced(
            product1.get('brand', ''),
            product2.get('brand', ''),
            product1.get('name', ''),
            product2.get('name', '')
        )
        scores['brand'] = brand_score
        linguistic_scores['brand'] = brand_linguistic
        if brand_score > 0.8:
            matched_fields.append('brand')
        
        # 3. Name similarity with n-gram and semantic matching
        name_score, name_linguistic = self._match_names_advanced(
            product1.get('name', ''),
            product2.get('name', '')
        )
        scores['name'] = name_score
        linguistic_scores['name'] = name_linguistic
        if name_score > 0.7:
            matched_fields.append('name')
        
        # 4. Specification matching with context
        spec_score, spec_details = self._match_specifications_advanced(
            product1.get('specs', {}),
            product2.get('specs', {}),
            product1.get('name', ''),
            product2.get('name', ''),
            category
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
        
        # Calculate weighted confidence with boosting
        base_confidence = sum(
            scores.get(field, 0) * weight
            for field, weight in weights.items()
        )
        
        # Apply linguistic boosting
        linguistic_boost = self._calculate_linguistic_boost(linguistic_scores)
        confidence = min(1.0, base_confidence + linguistic_boost)
        
        # Cross-validation checks
        cross_validation = self._cross_validate_match(
            product1, product2, scores, linguistic_scores
        )
        if cross_validation['adjustments']:
            confidence *= cross_validation['confidence_multiplier']
            warnings.extend(cross_validation['warnings'])
        
        # Price consistency check
        price_check = self._check_price_consistency_advanced(
            product1.get('price'),
            product2.get('price'),
            category
        )
        if not price_check['consistent']:
            warnings.append(price_check['warning'])
            confidence *= price_check['confidence_penalty']
        
        # Determine match type with adaptive thresholds
        match_type = self._determine_match_type(confidence, scores, category)
        
        # Compile detailed results
        details = {
            'sku_score': scores['sku'],
            'brand_score': scores['brand'],
            'name_score': scores['name'],
            'spec_score': scores['specs'],
            'category_score': scores['category'],
            'spec_details': spec_details,
            'price_variance': price_check['variance'],
            'weighted_confidence': base_confidence,
            'linguistic_boost': linguistic_boost,
            'final_confidence': confidence,
            'weight_profile': category,
            'cross_validation': cross_validation
        }
        
        return AdvancedMatchResult(
            confidence=confidence,
            match_type=match_type,
            details=details,
            matched_fields=matched_fields,
            warnings=warnings,
            linguistic_scores=linguistic_scores
        )
    
    def _match_sku_advanced(
        self, 
        sku1: str, 
        sku2: str, 
        name1: str, 
        name2: str
    ) -> Tuple[float, Dict[str, float]]:
        """Advanced SKU matching with fuzzy and extraction support"""
        linguistic_scores = {}
        
        # Direct match
        if sku1 and sku2:
            # Normalize SKUs
            sku1_norm = self.normalizer.normalize_sku(sku1)
            sku2_norm = self.normalizer.normalize_sku(sku2)
            
            if sku1_norm == sku2_norm:
                return 1.0, {'exact': 1.0}
            
            # Fuzzy matching
            fuzzy_score = self._calculate_fuzzy_score(sku1_norm, sku2_norm)
            if fuzzy_score > 0.9:
                linguistic_scores['fuzzy'] = fuzzy_score
                return fuzzy_score, linguistic_scores
            
            # N-gram similarity
            ngram_score = self._calculate_ngram_similarity(sku1_norm, sku2_norm)
            if ngram_score > 0.85:
                linguistic_scores['ngram'] = ngram_score
                return ngram_score * 0.95, linguistic_scores
        
        # Extract from names
        specs1 = self.normalizer.extract_specifications(name1)
        specs2 = self.normalizer.extract_specifications(name2)
        
        model1 = specs1.get('model', sku1)
        model2 = specs2.get('model', sku2)
        
        if model1 and model2:
            # Try phonetic matching for models
            phonetic_score = self._calculate_phonetic_similarity(model1, model2)
            if phonetic_score > 0.8:
                linguistic_scores['phonetic'] = phonetic_score
                return phonetic_score * 0.9, linguistic_scores
            
            # Pattern-based matching
            pattern_score = self._match_model_patterns(model1, model2)
            if pattern_score > 0.8:
                linguistic_scores['pattern'] = pattern_score
                return pattern_score, linguistic_scores
        
        return 0.0, linguistic_scores
    
    def _match_brand_advanced(
        self,
        brand1: str,
        brand2: str,
        name1: str,
        name2: str
    ) -> Tuple[float, Dict[str, float]]:
        """Advanced brand matching with phonetic and transliteration support"""
        linguistic_scores = {}
        
        # Extract brands if needed
        if not brand1:
            brand1 = self.normalizer.extract_brand(name1) or ''
        if not brand2:
            brand2 = self.normalizer.extract_brand(name2) or ''
        
        if not brand1 or not brand2:
            return 0.0, linguistic_scores
        
        # Normalize brands
        brand1_norm = self.normalizer.normalize(brand1)
        brand2_norm = self.normalizer.normalize(brand2)
        
        # Exact match
        if brand1_norm == brand2_norm:
            return 1.0, {'exact': 1.0}
        
        # Phonetic matching for Thai-English
        phonetic_score = self._calculate_phonetic_similarity(brand1, brand2)
        if phonetic_score > 0.85:
            linguistic_scores['phonetic'] = phonetic_score
            return phonetic_score, linguistic_scores
        
        # Fuzzy matching
        fuzzy_score = self._calculate_fuzzy_score(brand1_norm, brand2_norm)
        if fuzzy_score > 0.8:
            linguistic_scores['fuzzy'] = fuzzy_score
            return fuzzy_score, linguistic_scores
        
        # Check transliteration variations
        transliteration_score = self._check_transliteration_match(brand1, brand2)
        if transliteration_score > 0.8:
            linguistic_scores['transliteration'] = transliteration_score
            return transliteration_score, linguistic_scores
        
        return 0.0, linguistic_scores
    
    def _match_names_advanced(
        self,
        name1: str,
        name2: str
    ) -> Tuple[float, Dict[str, float]]:
        """Advanced name matching with multiple algorithms"""
        linguistic_scores = {}
        
        # Normalize names
        norm1 = self.normalizer.normalize(name1)
        norm2 = self.normalizer.normalize(name2)
        
        # Extract tokens
        tokens1 = set(self.normalizer.extract_tokens(name1))
        tokens2 = set(self.normalizer.extract_tokens(name2))
        
        if not tokens1 or not tokens2:
            return 0.0, linguistic_scores
        
        # 1. Token-based similarity
        token_score = self._calculate_token_similarity(tokens1, tokens2)
        linguistic_scores['token'] = token_score
        
        # 2. N-gram similarity
        ngram_score = self._calculate_ngram_similarity(norm1, norm2)
        linguistic_scores['ngram'] = ngram_score
        
        # 3. Sequence matching
        sequence_score = self._calculate_sequence_score(name1, name2)
        linguistic_scores['sequence'] = sequence_score
        
        # 4. Semantic similarity (keywords)
        semantic_score = self._calculate_semantic_similarity(tokens1, tokens2)
        linguistic_scores['semantic'] = semantic_score
        
        # 5. Cross-lingual matching
        crosslingual_score = self._calculate_crosslingual_score(name1, name2)
        linguistic_scores['crosslingual'] = crosslingual_score
        
        # Weighted combination
        final_score = (
            token_score * 0.25 +
            ngram_score * 0.20 +
            sequence_score * 0.15 +
            semantic_score * 0.20 +
            crosslingual_score * 0.20
        )
        
        return min(1.0, final_score), linguistic_scores
    
    def _match_specifications_advanced(
        self,
        specs1: Dict[str, Any],
        specs2: Dict[str, Any],
        name1: str,
        name2: str,
        category: str
    ) -> Tuple[float, Dict[str, Any]]:
        """Advanced specification matching with contextual tolerance"""
        # Extract specs from names if needed
        if not specs1:
            specs1 = self.normalizer.extract_specifications(name1)
        if not specs2:
            specs2 = self.normalizer.extract_specifications(name2)
        
        if not specs1 and not specs2:
            return 0.5, {}
        
        matched_specs = {}
        total_score = 0
        spec_count = 0
        critical_mismatches = 0
        
        # Define critical specs by category
        critical_specs = {
            'electronics': ['voltage', 'frequency', 'model'],
            'appliances': ['capacity', 'power', 'size'],
            'general': ['size', 'model']
        }
        
        category_critical = critical_specs.get(category, critical_specs['general'])
        
        # Compare specifications
        all_specs = set(specs1.keys()).union(specs2.keys())
        
        for spec_name in all_specs:
            val1 = specs1.get(spec_name)
            val2 = specs2.get(spec_name)
            
            if val1 is None or val2 is None:
                if spec_name in category_critical:
                    critical_mismatches += 1
                continue
            
            spec_count += 1
            is_critical = spec_name in category_critical
            
            # Numeric specifications
            if isinstance(val1, (int, float)) and isinstance(val2, (int, float)):
                tolerance_key = self._get_tolerance_key(spec_name, category)
                tolerance = self.spec_tolerances.get(spec_name, {}).get(
                    tolerance_key, 
                    self.spec_tolerances.get(spec_name, {}).get('default', 0.05)
                )
                
                relative_diff = abs(val1 - val2) / max(val1, val2) if max(val1, val2) > 0 else 0
                
                if relative_diff <= tolerance:
                    score = 1.0 - (relative_diff / tolerance)
                    total_score += score * (2.0 if is_critical else 1.0)
                    matched_specs[spec_name] = {
                        'match': True,
                        'score': score,
                        'values': [val1, val2],
                        'critical': is_critical
                    }
                else:
                    if is_critical:
                        critical_mismatches += 1
                    matched_specs[spec_name] = {
                        'match': False,
                        'score': 0,
                        'values': [val1, val2],
                        'critical': is_critical
                    }
            
            # String specifications
            else:
                str_score = self._match_spec_strings(str(val1), str(val2))
                total_score += str_score * (2.0 if is_critical else 1.0)
                matched_specs[spec_name] = {
                    'match': str_score > 0.8,
                    'score': str_score,
                    'values': [val1, val2],
                    'critical': is_critical
                }
                
                if str_score < 0.5 and is_critical:
                    critical_mismatches += 1
        
        # Calculate final score with critical spec penalty
        weight_sum = sum(2.0 if s in category_critical else 1.0 for s in matched_specs.keys())
        base_score = total_score / weight_sum if weight_sum > 0 else 0.5
        
        # Apply penalty for critical mismatches
        if critical_mismatches > 0:
            penalty = 0.2 * critical_mismatches
            base_score = max(0, base_score - penalty)
        
        return base_score, matched_specs
    
    def _calculate_fuzzy_score(self, s1: str, s2: str) -> float:
        """Calculate fuzzy string matching score"""
        if not s1 or not s2:
            return 0.0
        
        # Use SequenceMatcher for fuzzy matching
        return SequenceMatcher(None, s1.lower(), s2.lower()).ratio()
    
    def _calculate_ngram_similarity(self, s1: str, s2: str) -> float:
        """Calculate n-gram based similarity"""
        if not s1 or not s2:
            return 0.0
        
        scores = []
        for n in self.ngram_sizes:
            ngrams1 = self._get_ngrams(s1.lower(), n)
            ngrams2 = self._get_ngrams(s2.lower(), n)
            
            if ngrams1 and ngrams2:
                intersection = ngrams1.intersection(ngrams2)
                union = ngrams1.union(ngrams2)
                scores.append(len(intersection) / len(union))
        
        return sum(scores) / len(scores) if scores else 0.0
    
    def _get_ngrams(self, text: str, n: int) -> Set[str]:
        """Extract character n-grams from text"""
        if len(text) < n:
            return {text}
        return {text[i:i+n] for i in range(len(text) - n + 1)}
    
    def _calculate_phonetic_similarity(self, s1: str, s2: str) -> float:
        """Calculate phonetic similarity for Thai-English matching"""
        # Check if one is Thai and other is English
        is_thai1 = self.normalizer.is_thai_text(s1)
        is_thai2 = self.normalizer.is_thai_text(s2)
        
        if is_thai1 == is_thai2:
            # Both same language, use regular matching
            return self._calculate_fuzzy_score(s1, s2)
        
        # Cross-language phonetic matching
        if is_thai1:
            thai_text, eng_text = s1, s2
        else:
            thai_text, eng_text = s2, s1
        
        # Try to match using phonetic patterns
        score = 0.0
        matches = 0
        
        for eng_sound, thai_chars in self.phonetic_patterns.items():
            if eng_sound in eng_text.lower():
                for thai_char in thai_chars:
                    if thai_char in thai_text:
                        matches += 1
                        break
        
        # Calculate score based on matches
        if matches > 0:
            # Normalize by the length of the shorter string
            min_len = min(len(thai_text), len(eng_text))
            score = min(1.0, matches / (min_len * 0.5))
        
        return score
    
    def _check_transliteration_match(self, s1: str, s2: str) -> float:
        """Check if strings are transliteration variations"""
        # Common transliteration variations
        variations = [
            ('ph', 'p'), ('th', 't'), ('ch', 'c'),
            ('kh', 'k'), ('ng', 'n'), ('ae', 'a'),
            ('ue', 'u'), ('oe', 'o'), ('ai', 'i'),
            ('z', 's'), ('v', 'w'), ('x', 's')
        ]
        
        s1_lower = s1.lower()
        s2_lower = s2.lower()
        
        # Try variations
        for var1, var2 in variations:
            s1_variant = s1_lower.replace(var1, var2)
            s2_variant = s2_lower.replace(var1, var2)
            
            if s1_variant == s2_lower or s1_lower == s2_variant:
                return 0.9
            
            if s1_variant == s2_variant:
                return 0.85
        
        return 0.0
    
    def _calculate_token_similarity(self, tokens1: Set[str], tokens2: Set[str]) -> float:
        """Calculate token-based similarity with importance weighting"""
        if not tokens1 or not tokens2:
            return 0.0
        
        # Weight important tokens higher
        important_tokens1 = self._extract_important_tokens(tokens1)
        important_tokens2 = self._extract_important_tokens(tokens2)
        
        # Calculate weighted Jaccard
        all_tokens = tokens1.union(tokens2)
        weighted_intersection = 0
        weighted_union = 0
        
        for token in all_tokens:
            weight = 2.0 if (token in important_tokens1 or token in important_tokens2) else 1.0
            
            if token in tokens1 and token in tokens2:
                weighted_intersection += weight
            
            if token in tokens1 or token in tokens2:
                weighted_union += weight
        
        return weighted_intersection / weighted_union if weighted_union > 0 else 0.0
    
    def _calculate_sequence_score(self, s1: str, s2: str) -> float:
        """Calculate sequence-based similarity"""
        if not s1 or not s2:
            return 0.0
        
        # Normalize and tokenize
        tokens1 = self.normalizer.extract_tokens(s1)
        tokens2 = self.normalizer.extract_tokens(s2)
        
        if not tokens1 or not tokens2:
            return 0.0
        
        # Find longest common subsequence
        lcs_length = self._longest_common_subsequence(tokens1, tokens2)
        
        # Normalize by average length
        avg_len = (len(tokens1) + len(tokens2)) / 2
        
        return lcs_length / avg_len if avg_len > 0 else 0.0
    
    def _calculate_semantic_similarity(self, tokens1: Set[str], tokens2: Set[str]) -> float:
        """Calculate semantic similarity based on domain keywords"""
        # Define semantic groups
        semantic_groups = {
            'cooling': {'air', 'conditioner', 'ac', 'cooling', 'แอร์', 'เครื่องปรับอากาศ', 'ปรับอากาศ'},
            'inverter': {'inverter', 'อินเวอร์เตอร์', 'อินเวอเตอร์', 'ประหยัดไฟ'},
            'smart': {'smart', 'สมาร์ท', 'wifi', 'iot', 'app'},
            'size': {'btu', 'ton', 'hp', 'บีทียู', 'ตัน', 'แรงม้า'},
            'efficiency': {'energy', 'saving', 'eco', 'ประหยัด', 'พลังงาน', 'efficient'},
            'quality': {'premium', 'pro', 'plus', 'advanced', 'พรีเมียม', 'โปร'}
        }
        
        # Find semantic matches
        groups1 = set()
        groups2 = set()
        
        for group, keywords in semantic_groups.items():
            if any(token in keywords for token in tokens1):
                groups1.add(group)
            if any(token in keywords for token in tokens2):
                groups2.add(group)
        
        if not groups1 and not groups2:
            return 0.5  # No semantic information
        
        if groups1 and groups2:
            intersection = groups1.intersection(groups2)
            union = groups1.union(groups2)
            return len(intersection) / len(union)
        
        return 0.0
    
    def _calculate_crosslingual_score(self, s1: str, s2: str) -> float:
        """Calculate cross-lingual matching score"""
        # Check if texts are in different languages
        is_thai1 = self.normalizer.is_thai_text(s1)
        is_thai2 = self.normalizer.is_thai_text(s2)
        
        if is_thai1 == is_thai2:
            return 0.0  # Same language, no cross-lingual bonus
        
        # Extract numbers and codes (language-agnostic)
        numbers1 = re.findall(r'\d+', s1)
        numbers2 = re.findall(r'\d+', s2)
        
        codes1 = re.findall(r'[A-Z0-9]{3,}', s1.upper())
        codes2 = re.findall(r'[A-Z0-9]{3,}', s2.upper())
        
        score = 0.0
        
        # Match numbers
        if numbers1 and numbers2:
            number_matches = sum(1 for n in numbers1 if n in numbers2)
            score += (number_matches / max(len(numbers1), len(numbers2))) * 0.5
        
        # Match codes
        if codes1 and codes2:
            code_matches = sum(1 for c in codes1 if c in codes2)
            score += (code_matches / max(len(codes1), len(codes2))) * 0.5
        
        return min(1.0, score)
    
    def _match_model_patterns(self, model1: str, model2: str) -> float:
        """Match model numbers with pattern recognition"""
        # Extract pattern components
        pattern1 = self._extract_model_pattern(model1)
        pattern2 = self._extract_model_pattern(model2)
        
        if not pattern1 or not pattern2:
            return 0.0
        
        # Compare patterns
        matches = 0
        total = 0
        
        for key in set(pattern1.keys()).union(pattern2.keys()):
            total += 1
            if pattern1.get(key) == pattern2.get(key):
                matches += 1
        
        return matches / total if total > 0 else 0.0
    
    def _extract_model_pattern(self, model: str) -> Dict[str, str]:
        """Extract pattern components from model number"""
        pattern = {}
        
        # Extract prefix letters
        prefix_match = re.match(r'^([A-Z]+)', model.upper())
        if prefix_match:
            pattern['prefix'] = prefix_match.group(1)
        
        # Extract numbers
        numbers = re.findall(r'\d+', model)
        if numbers:
            pattern['numbers'] = '-'.join(numbers)
        
        # Extract suffix
        suffix_match = re.search(r'([A-Z]+)$', model.upper())
        if suffix_match and suffix_match.group(1) != pattern.get('prefix'):
            pattern['suffix'] = suffix_match.group(1)
        
        return pattern
    
    def _match_spec_strings(self, s1: str, s2: str) -> float:
        """Match specification strings with normalization"""
        # Normalize specifications
        s1_norm = self.normalizer.normalize_specification(s1)
        s2_norm = self.normalizer.normalize_specification(s2)
        
        if s1_norm == s2_norm:
            return 1.0
        
        # Try fuzzy matching
        return self._calculate_fuzzy_score(s1_norm, s2_norm)
    
    def _extract_important_tokens(self, tokens: Set[str]) -> Set[str]:
        """Extract important tokens for weighted matching"""
        important = set()
        
        for token in tokens:
            # Model numbers
            if any(c.isdigit() for c in token) and len(token) > 2:
                important.add(token)
            # Known brands
            elif token in self.normalizer.brand_mappings.values():
                important.add(token)
            # Technical specs
            elif any(unit in token for unit in ['btu', 'inch', 'liter', 'ton', 'hp', 'watt']):
                important.add(token)
            # Key features
            elif token in ['inverter', 'smart', 'digital', 'automatic', 'eco', 'premium', 'pro']:
                important.add(token)
        
        return important
    
    def _longest_common_subsequence(self, seq1: List[str], seq2: List[str]) -> int:
        """Find length of longest common subsequence"""
        m, n = len(seq1), len(seq2)
        dp = [[0] * (n + 1) for _ in range(m + 1)]
        
        for i in range(1, m + 1):
            for j in range(1, n + 1):
                if seq1[i-1] == seq2[j-1]:
                    dp[i][j] = dp[i-1][j-1] + 1
                else:
                    dp[i][j] = max(dp[i-1][j], dp[i][j-1])
        
        return dp[m][n]
    
    def _infer_category(self, product1: Dict[str, Any], product2: Dict[str, Any]) -> str:
        """Infer product category from product data"""
        # Check categories
        cat1 = product1.get('category', '').lower()
        cat2 = product2.get('category', '').lower()
        
        # Check for electronics keywords
        electronics_keywords = ['air conditioner', 'แอร์', 'tv', 'refrigerator', 'ตู้เย็น', 
                               'washer', 'เครื่องซักผ้า', 'computer', 'คอมพิวเตอร์']
        
        name1 = product1.get('name', '').lower()
        name2 = product2.get('name', '').lower()
        
        if any(kw in cat1 + cat2 + name1 + name2 for kw in electronics_keywords):
            return 'electronics'
        
        # Check for appliances
        appliance_keywords = ['kitchen', 'ครัว', 'home', 'บ้าน', 'appliance', 'เครื่องใช้']
        if any(kw in cat1 + cat2 + name1 + name2 for kw in appliance_keywords):
            return 'appliances'
        
        return 'general'
    
    def _get_tolerance_key(self, spec_name: str, category: str) -> str:
        """Get tolerance key based on spec name and category"""
        if spec_name == 'size' and category == 'electronics':
            return 'display'
        elif spec_name == 'capacity' and 'air' in category:
            return 'cooling'
        elif spec_name == 'power' and category == 'electronics':
            return 'exact'
        return 'default'
    
    def _calculate_linguistic_boost(self, linguistic_scores: Dict[str, Dict[str, float]]) -> float:
        """Calculate confidence boost from linguistic matching"""
        boost = 0.0
        
        for field, scores in linguistic_scores.items():
            if 'phonetic' in scores and scores['phonetic'] > 0.8:
                boost += 0.02
            if 'transliteration' in scores and scores['transliteration'] > 0.8:
                boost += 0.03
            if 'crosslingual' in scores and scores['crosslingual'] > 0.7:
                boost += 0.02
            if 'semantic' in scores and scores['semantic'] > 0.8:
                boost += 0.01
        
        return min(0.1, boost)  # Cap at 10% boost
    
    def _cross_validate_match(
        self,
        product1: Dict[str, Any],
        product2: Dict[str, Any],
        scores: Dict[str, float],
        linguistic_scores: Dict[str, Dict[str, float]]
    ) -> Dict[str, Any]:
        """Cross-validate match results for consistency"""
        validation = {
            'adjustments': False,
            'confidence_multiplier': 1.0,
            'warnings': []
        }
        
        # Check for inconsistencies
        
        # 1. High SKU match but low brand match
        if scores.get('sku', 0) > 0.9 and scores.get('brand', 0) < 0.5:
            validation['warnings'].append('SKU matches but brands differ significantly')
            validation['confidence_multiplier'] *= 0.9
            validation['adjustments'] = True
        
        # 2. Different categories but high name match
        if scores.get('category', 0) < 0.5 and scores.get('name', 0) > 0.8:
            validation['warnings'].append('Products in different categories despite name similarity')
            validation['confidence_multiplier'] *= 0.85
            validation['adjustments'] = True
        
        # 3. High linguistic scores but low direct matches
        avg_linguistic = sum(
            sum(field_scores.values()) / len(field_scores) 
            for field_scores in linguistic_scores.values() 
            if field_scores
        ) / len(linguistic_scores) if linguistic_scores else 0
        
        avg_direct = sum(scores.values()) / len(scores) if scores else 0
        
        if avg_linguistic > 0.8 and avg_direct < 0.5:
            validation['warnings'].append('High linguistic similarity but low direct matches')
            validation['confidence_multiplier'] *= 0.95
            validation['adjustments'] = True
        
        return validation
    
    def _check_price_consistency_advanced(
        self,
        price1: Any,
        price2: Any,
        category: str
    ) -> Dict[str, Any]:
        """Advanced price consistency check with category context"""
        result = {
            'consistent': True,
            'variance': 0.0,
            'warning': '',
            'confidence_penalty': 1.0
        }
        
        try:
            p1 = float(price1) if price1 else 0
            p2 = float(price2) if price2 else 0
            
            if p1 > 0 and p2 > 0:
                # Calculate variance
                mean_price = (p1 + p2) / 2
                variance = abs(p1 - p2) / mean_price
                result['variance'] = variance
                
                # Category-specific thresholds
                thresholds = {
                    'electronics': {'warning': 0.15, 'penalty': 0.25},
                    'appliances': {'warning': 0.20, 'penalty': 0.30},
                    'general': {'warning': 0.25, 'penalty': 0.35}
                }
                
                category_threshold = thresholds.get(category, thresholds['general'])
                
                if variance > category_threshold['penalty']:
                    result['consistent'] = False
                    result['warning'] = f"Large price difference: {variance:.1%}"
                    result['confidence_penalty'] = 0.8
                elif variance > category_threshold['warning']:
                    result['warning'] = f"Moderate price difference: {variance:.1%}"
                    result['confidence_penalty'] = 0.95
        
        except (ValueError, TypeError):
            result['warning'] = "Could not compare prices"
            result['confidence_penalty'] = 0.98
        
        return result
    
    def _determine_match_type(
        self,
        confidence: float,
        scores: Dict[str, float],
        category: str
    ) -> str:
        """Determine match type with adaptive thresholds"""
        # Adjust thresholds based on category
        category_adjustments = {
            'electronics': 0.0,    # Strict matching for electronics
            'appliances': -0.05,   # Slightly relaxed
            'general': -0.10       # More relaxed for general items
        }
        
        adjustment = category_adjustments.get(category, 0)
        
        # Check for exact match conditions
        if (scores.get('sku', 0) >= 0.95 and 
            scores.get('brand', 0) >= 0.90 and 
            confidence >= 0.90):
            return 'exact'
        
        # Apply adjusted thresholds
        for match_type, base_threshold in sorted(self.thresholds.items(), key=lambda x: -x[1]):
            adjusted_threshold = base_threshold + adjustment
            if confidence >= adjusted_threshold:
                return match_type
        
        return 'none'
    
    def _match_category(self, cat1: str, cat2: str) -> float:
        """Match categories with hierarchy support"""
        if not cat1 or not cat2:
            return 0.5
        
        # Normalize categories
        cat1_norm = self.normalizer.normalize(cat1)
        cat2_norm = self.normalizer.normalize(cat2)
        
        if cat1_norm == cat2_norm:
            return 1.0
        
        # Check hierarchical match
        if cat1_norm in cat2_norm or cat2_norm in cat1_norm:
            return 0.8
        
        # Token similarity
        tokens1 = set(self.normalizer.extract_tokens(cat1))
        tokens2 = set(self.normalizer.extract_tokens(cat2))
        
        if tokens1 and tokens2:
            jaccard = len(tokens1.intersection(tokens2)) / len(tokens1.union(tokens2))
            return jaccard
        
        return 0.0
    
    def find_best_matches(
        self,
        product: Dict[str, Any],
        candidates: List[Dict[str, Any]],
        min_confidence: float = 0.55,
        max_results: int = 10,
        category_hint: Optional[str] = None
    ) -> List[Tuple[Dict[str, Any], AdvancedMatchResult]]:
        """
        Find best matches with advanced algorithms
        
        Returns:
            List of (candidate, match_result) tuples sorted by confidence
        """
        matches = []
        
        for candidate in candidates:
            # Skip same product
            if product.get('id') == candidate.get('id'):
                continue
            
            # Skip same retailer unless allowed
            if product.get('retailer_code') == candidate.get('retailer_code'):
                continue
            
            result = self.match_products(product, candidate, category_hint)
            
            if result.confidence >= min_confidence:
                matches.append((candidate, result))
        
        # Sort by confidence
        matches.sort(key=lambda x: x[1].confidence, reverse=True)
        
        # Apply diversity filter if too many high-confidence matches
        if len(matches) > max_results * 2:
            matches = self._apply_diversity_filter(matches, max_results)
        
        return matches[:max_results]
    
    def _apply_diversity_filter(
        self,
        matches: List[Tuple[Dict[str, Any], AdvancedMatchResult]],
        target_count: int
    ) -> List[Tuple[Dict[str, Any], AdvancedMatchResult]]:
        """Apply diversity filter to avoid duplicate matches"""
        filtered = []
        seen_models = set()
        seen_brands = set()
        
        for candidate, result in matches:
            # Extract identifiers
            model = candidate.get('sku', '')
            brand = candidate.get('brand', '')
            
            # Check diversity
            if model and model in seen_models:
                continue
            
            if brand and len([b for b in seen_brands if b == brand]) >= 3:
                continue
            
            filtered.append((candidate, result))
            
            if model:
                seen_models.add(model)
            if brand:
                seen_brands.add(brand)
            
            if len(filtered) >= target_count:
                break
        
        return filtered