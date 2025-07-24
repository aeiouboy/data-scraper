"""
Standardized SKU/Model Number Extraction System
Advanced pattern matching and normalization for product model identification
"""

import re
import logging
from typing import Dict, List, Optional, Tuple, Set
from dataclasses import dataclass
from collections import defaultdict
import json

from src.config.text_normalization_config import SKU_PATTERNS, BRAND_EXCLUSIONS

logger = logging.getLogger(__name__)


@dataclass
class SkuMatch:
    """SKU match result with metadata"""
    sku: str
    confidence: float
    pattern_type: str
    position: int
    length: int
    context: str
    normalized: str


class SkuExtractor:
    """Advanced SKU/Model number extraction system"""
    
    def __init__(self, custom_patterns: Optional[List[str]] = None):
        """Initialize SKU extractor with patterns"""
        self.base_patterns = SKU_PATTERNS.copy()
        self.brand_exclusions = set(BRAND_EXCLUSIONS)
        
        if custom_patterns:
            self.base_patterns.extend(custom_patterns)
        
        # Compile patterns for better performance
        self.compiled_patterns = self._compile_patterns()
        
        # Initialize pattern statistics
        self.pattern_stats = defaultdict(int)
        
        # Common SKU formats by retailer
        self.retailer_patterns = {
            'homepro': [
                r'\b(HP[0-9]{6,8})\b',  # HP123456
                r'\b([A-Z]{2,3}[-]?[0-9]{4,6}[-]?[A-Z]{0,2})\b',  # AB-1234-X
            ],
            'thaiwatsadu': [
                r'\b(TWD[0-9]{6,8})\b',  # TWD123456
                r'\b([A-Z]{3}[-]?[0-9]{3,4}[-]?[A-Z]{1,2})\b',  # ABC-123-X
            ],
            'globalhouse': [
                r'\b(GH[0-9]{6,8})\b',  # GH123456
                r'\b([A-Z]{2}[-]?[0-9]{4,6})\b',  # AB-1234
            ],
            'megahome': [
                r'\b(MH[-]?[0-9]{4}[-]?[0-9]{3})\b',  # MH-1234-001
                r'\b([A-Z]{3}[0-9]{3}[A-Z]{1,2})\b',  # ABC123X
            ],
            'boonthavorn': [
                r'\b(BT[0-9]{6,8})\b',  # BT123456
                r'\b([A-Z]{2,4}[-]?[0-9]{3,5})\b',  # ABCD-123
            ],
            'dohome': [
                r'\b(DH[0-9]{6,8})\b',  # DH123456
                r'\b([A-Z]{2}[0-9]{4}[A-Z]{0,2})\b',  # AB1234X
            ]
        }
        
        # Add retailer patterns to base patterns
        for retailer_patterns in self.retailer_patterns.values():
            self.base_patterns.extend(retailer_patterns)
        
        # Recompile with retailer patterns
        self.compiled_patterns = self._compile_patterns()
    
    def _compile_patterns(self) -> List[Tuple[re.Pattern, str]]:
        """Compile regex patterns with metadata"""
        compiled = []
        
        for i, pattern in enumerate(self.base_patterns):
            try:
                compiled_pattern = re.compile(pattern, re.IGNORECASE | re.UNICODE)
                pattern_type = self._classify_pattern(pattern)
                compiled.append((compiled_pattern, pattern_type))
            except re.error as e:
                logger.warning(f"Invalid regex pattern {i}: {pattern} - {e}")
        
        return compiled
    
    def _classify_pattern(self, pattern: str) -> str:
        """Classify pattern type for better matching"""
        if 'MSY' in pattern or 'FTKF' in pattern:
            return 'air_conditioner'
        elif 'CS-' in pattern:
            return 'panasonic'
        elif 'WW' in pattern or 'RT' in pattern:
            return 'samsung'
        elif 'GN-' in pattern:
            return 'sharp'
        elif 'NA-' in pattern:
            return 'panasonic_washing'
        elif 'UN' in pattern or 'QN' in pattern:
            return 'samsung_tv'
        elif 'KD-' in pattern:
            return 'sony_tv'
        elif 'HP' in pattern:
            return 'homepro'
        elif 'TWD' in pattern:
            return 'thaiwatsadu'
        elif 'รุ่น' in pattern:
            return 'thai_model'
        elif 'Model' in pattern:
            return 'english_model'
        elif r'\d' in pattern and r'[A-Z]' in pattern:
            return 'alphanumeric'
        else:
            return 'generic'
    
    def extract_sku(self, text: str, retailer: Optional[str] = None) -> Optional[SkuMatch]:
        """Extract the best SKU match from text"""
        if not text:
            return None
        
        matches = self.extract_all_skus(text, retailer)
        
        if not matches:
            return None
        
        # Return the best match (highest confidence)
        return max(matches, key=lambda m: m.confidence)
    
    def extract_all_skus(self, text: str, retailer: Optional[str] = None) -> List[SkuMatch]:
        """Extract all potential SKU matches from text"""
        if not text:
            return []
        
        matches = []
        
        # Use retailer-specific patterns first if retailer is specified
        if retailer and retailer in self.retailer_patterns:
            retailer_matches = self._extract_with_patterns(
                text, 
                self.retailer_patterns[retailer], 
                f"{retailer}_specific"
            )
            matches.extend(retailer_matches)
        
        # Use general patterns
        for pattern, pattern_type in self.compiled_patterns:
            pattern_matches = self._extract_with_pattern(text, pattern, pattern_type)
            matches.extend(pattern_matches)
        
        # Filter and rank matches
        filtered_matches = self._filter_matches(matches)
        ranked_matches = self._rank_matches(filtered_matches)
        
        return ranked_matches
    
    def _extract_with_patterns(self, text: str, patterns: List[str], pattern_type: str) -> List[SkuMatch]:
        """Extract matches using a list of patterns"""
        matches = []
        
        for pattern in patterns:
            try:
                compiled_pattern = re.compile(pattern, re.IGNORECASE | re.UNICODE)
                pattern_matches = self._extract_with_pattern(text, compiled_pattern, pattern_type)
                matches.extend(pattern_matches)
            except re.error as e:
                logger.warning(f"Invalid pattern: {pattern} - {e}")
        
        return matches
    
    def _extract_with_pattern(self, text: str, pattern: re.Pattern, pattern_type: str) -> List[SkuMatch]:
        """Extract matches using a single compiled pattern"""
        matches = []
        
        for match in pattern.finditer(text):
            sku = match.group(1) if match.groups() else match.group(0)
            
            # Skip if it's a brand name
            if sku.upper() in self.brand_exclusions:
                continue
            
            # Skip if it's just numbers
            if sku.replace('-', '').replace('/', '').replace(' ', '').isdigit():
                continue
            
            # Skip if too short or too long
            if len(sku) < 3 or len(sku) > 20:
                continue
            
            # Must contain at least one digit
            if not any(c.isdigit() for c in sku):
                continue
            
            # Must contain at least one letter
            if not any(c.isalpha() for c in sku):
                continue
            
            # Calculate confidence
            confidence = self._calculate_confidence(sku, pattern_type, match, text)
            
            # Get context around the match
            context = self._get_context(text, match.start(), match.end())
            
            # Normalize SKU
            normalized = self._normalize_sku(sku)
            
            sku_match = SkuMatch(
                sku=sku,
                confidence=confidence,
                pattern_type=pattern_type,
                position=match.start(),
                length=len(sku),
                context=context,
                normalized=normalized
            )
            
            matches.append(sku_match)
            
            # Update statistics
            self.pattern_stats[pattern_type] += 1
        
        return matches
    
    def _calculate_confidence(self, sku: str, pattern_type: str, match: re.Match, text: str) -> float:
        """Calculate confidence score for SKU match"""
        confidence = 0.5  # Base confidence
        
        # Pattern type bonuses
        pattern_bonuses = {
            'air_conditioner': 0.3,
            'panasonic': 0.25,
            'samsung': 0.25,
            'samsung_tv': 0.25,
            'sony_tv': 0.25,
            'thai_model': 0.2,
            'english_model': 0.2,
            'alphanumeric': 0.15,
            'generic': 0.1
        }
        
        confidence += pattern_bonuses.get(pattern_type, 0)
        
        # Length bonus (optimal length 6-12 characters)
        length = len(sku)
        if 6 <= length <= 12:
            confidence += 0.1
        elif 4 <= length <= 15:
            confidence += 0.05
        
        # Character composition bonus
        alpha_count = sum(1 for c in sku if c.isalpha())
        digit_count = sum(1 for c in sku if c.isdigit())
        
        if alpha_count > 0 and digit_count > 0:
            confidence += 0.1
        
        # Balanced alphanumeric
        if 0.2 <= alpha_count / len(sku) <= 0.8:
            confidence += 0.05
        
        # Context bonus
        context_keywords = ['รุ่น', 'model', 'sku', 'code', 'part', 'item']
        context_text = text[max(0, match.start() - 20):match.end() + 20].lower()
        
        for keyword in context_keywords:
            if keyword in context_text:
                confidence += 0.1
                break
        
        # Format bonus (common SKU formats)
        if re.match(r'^[A-Z]{2,4}[-]?[0-9]{3,6}[-]?[A-Z]{0,3}$', sku):
            confidence += 0.15
        
        # Hyphen/dash bonus (structured format)
        if '-' in sku or '_' in sku:
            confidence += 0.05
        
        # Penalty for very common patterns that might be false positives
        if sku.upper() in ['ABC123', 'TEST123', 'DEMO123']:
            confidence -= 0.3
        
        return min(1.0, confidence)
    
    def _get_context(self, text: str, start: int, end: int, context_size: int = 30) -> str:
        """Get context around the SKU match"""
        context_start = max(0, start - context_size)
        context_end = min(len(text), end + context_size)
        
        return text[context_start:context_end].strip()
    
    def _normalize_sku(self, sku: str) -> str:
        """Normalize SKU for comparison"""
        # Remove common separators and convert to uppercase
        normalized = sku.upper()
        normalized = normalized.replace('-', '').replace('/', '').replace(' ', '')
        normalized = normalized.replace('.', '').replace('_', '')
        
        return normalized
    
    def _filter_matches(self, matches: List[SkuMatch]) -> List[SkuMatch]:
        """Filter out low-quality matches"""
        filtered = []
        
        for match in matches:
            # Minimum confidence threshold
            if match.confidence < 0.3:
                continue
            
            # Check for duplicate normalized SKUs
            normalized = match.normalized
            is_duplicate = False
            
            for existing in filtered:
                if existing.normalized == normalized:
                    # Keep the one with higher confidence
                    if match.confidence > existing.confidence:
                        filtered.remove(existing)
                        break
                    else:
                        is_duplicate = True
                        break
            
            if not is_duplicate:
                filtered.append(match)
        
        return filtered
    
    def _rank_matches(self, matches: List[SkuMatch]) -> List[SkuMatch]:
        """Rank matches by confidence and other factors"""
        return sorted(matches, key=lambda m: (m.confidence, -m.position), reverse=True)
    
    def compare_skus(self, sku1: str, sku2: str) -> bool:
        """Compare two SKUs for equivalence"""
        if not sku1 or not sku2:
            return False
        
        norm1 = self._normalize_sku(sku1)
        norm2 = self._normalize_sku(sku2)
        
        # Direct match
        if norm1 == norm2:
            return True
        
        # Partial match for longer SKUs
        if len(norm1) >= 6 and len(norm2) >= 6:
            if norm1 in norm2 or norm2 in norm1:
                return True
        
        # Version variant match
        if len(norm1) >= 6 and len(norm2) >= 6:
            base1 = re.sub(r'[A-Z]*\d*$', '', norm1)
            base2 = re.sub(r'[A-Z]*\d*$', '', norm2)
            if base1 == base2 and len(base1) >= 4:
                return True
        
        return False
    
    def get_pattern_statistics(self) -> Dict[str, int]:
        """Get pattern usage statistics"""
        return dict(self.pattern_stats)
    
    def add_custom_pattern(self, pattern: str, pattern_type: str = 'custom'):
        """Add a custom SKU pattern"""
        try:
            compiled_pattern = re.compile(pattern, re.IGNORECASE | re.UNICODE)
            self.compiled_patterns.append((compiled_pattern, pattern_type))
            self.base_patterns.append(pattern)
            logger.info(f"Added custom pattern: {pattern}")
        except re.error as e:
            logger.error(f"Invalid custom pattern: {pattern} - {e}")
    
    def validate_sku(self, sku: str) -> Dict[str, any]:
        """Validate SKU format and return analysis"""
        if not sku:
            return {'valid': False, 'reason': 'Empty SKU'}
        
        analysis = {
            'valid': True,
            'length': len(sku),
            'alpha_count': sum(1 for c in sku if c.isalpha()),
            'digit_count': sum(1 for c in sku if c.isdigit()),
            'special_chars': sum(1 for c in sku if not c.isalnum()),
            'format_score': 0,
            'issues': []
        }
        
        # Length check
        if len(sku) < 3:
            analysis['valid'] = False
            analysis['issues'].append('Too short')
        elif len(sku) > 20:
            analysis['valid'] = False
            analysis['issues'].append('Too long')
        
        # Character composition
        if analysis['alpha_count'] == 0:
            analysis['issues'].append('No alphabetic characters')
        
        if analysis['digit_count'] == 0:
            analysis['issues'].append('No numeric characters')
        
        # Format scoring
        if 6 <= len(sku) <= 12:
            analysis['format_score'] += 0.3
        
        if analysis['alpha_count'] > 0 and analysis['digit_count'] > 0:
            analysis['format_score'] += 0.4
        
        if re.match(r'^[A-Z]{2,4}[-]?[0-9]{3,6}[-]?[A-Z]{0,3}$', sku):
            analysis['format_score'] += 0.3
        
        # Check against brand exclusions
        if sku.upper() in self.brand_exclusions:
            analysis['valid'] = False
            analysis['issues'].append('Matches brand exclusion')
        
        return analysis


# Example usage and testing
if __name__ == "__main__":
    # Initialize SKU extractor
    extractor = SkuExtractor()
    
    # Test cases
    test_cases = [
        "MITSUBISHI แอร์ติดผนัง รุ่น MSY-KP13VF 12000BTU",
        "Samsung ตู้เย็น RT29K5511S8 300 ลิตร",
        "LG Smart TV รุ่น 55UN7300PTC 55 นิ้ว",
        "Panasonic เครื่องซักผ้า NA-F70B3 7 กก.",
        "HomePro Item Code: HP-2023-001234",
        "Thai Watsadu Product TWD-456789",
        "Sharp ตู้เย็น GN-X392PBGB 13 คิว",
        "Sony TV KD-55X80J 55 inch 4K",
        "Bosch Drill Model GSB500RE Professional",
        "No SKU in this text at all"
    ]
    
    print("SKU Extraction Test Results:")
    print("=" * 60)
    
    for i, text in enumerate(test_cases, 1):
        print(f"\nTest {i}: {text}")
        
        # Extract best SKU
        best_sku = extractor.extract_sku(text)
        if best_sku:
            print(f"  Best SKU: {best_sku.sku}")
            print(f"  Confidence: {best_sku.confidence:.3f}")
            print(f"  Pattern Type: {best_sku.pattern_type}")
            print(f"  Normalized: {best_sku.normalized}")
        else:
            print("  No SKU found")
        
        # Extract all SKUs
        all_skus = extractor.extract_all_skus(text)
        if len(all_skus) > 1:
            print(f"  All SKUs: {[match.sku for match in all_skus]}")
    
    # Test SKU comparison
    print(f"\nSKU Comparison Test:")
    print("=" * 60)
    
    comparison_pairs = [
        ("MSY-KP13VF", "MSYKP13VF"),
        ("RT29K5511S8", "RT29K5511S8-ST"),
        ("55UN7300PTC", "55UN7300"),
        ("NA-F70B3", "NAF70B3"),
        ("Different1", "Different2")
    ]
    
    for sku1, sku2 in comparison_pairs:
        is_match = extractor.compare_skus(sku1, sku2)
        print(f"  '{sku1}' vs '{sku2}': {is_match}")
    
    # Test SKU validation
    print(f"\nSKU Validation Test:")
    print("=" * 60)
    
    test_skus = [
        "MSY-KP13VF",
        "RT29K5511S8",
        "ABC",
        "123456789012345678901",
        "ABCDEFGHIJKLMNOP",
        "123456789",
        "SAMSUNG",
        "VALID-123-SKU"
    ]
    
    for sku in test_skus:
        validation = extractor.validate_sku(sku)
        print(f"  '{sku}': Valid={validation['valid']}, Score={validation['format_score']:.2f}")
        if validation['issues']:
            print(f"    Issues: {validation['issues']}")
    
    # Pattern statistics
    print(f"\nPattern Statistics:")
    print("=" * 60)
    stats = extractor.get_pattern_statistics()
    for pattern_type, count in stats.items():
        print(f"  {pattern_type}: {count} matches")