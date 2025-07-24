"""
Enhanced text normalizer with configurable Thai language support
Implements Phase 1 improvements from the matching accuracy plan
"""

import re
import unicodedata
import logging
from typing import Dict, List, Optional, Tuple, Set
from functools import lru_cache
import json

from src.config.text_normalization_config import DEFAULT_CONFIG

logger = logging.getLogger(__name__)


class EnhancedTextNormalizer:
    """Enhanced text normalizer with advanced Thai language support"""
    
    def __init__(self, config: Dict = None):
        """Initialize with custom configuration"""
        self.config = config or DEFAULT_CONFIG
        self.brand_mappings = self.config['brand_mappings']
        self.unit_mappings = self.config['unit_mappings']
        self.stop_words = self.config['stop_words']
        self.model_patterns = self.config['model_patterns']
        self.sku_patterns = self.config['sku_patterns']
        self.brand_exclusions = self.config['brand_exclusions']
        self.text_settings = self.config['text_processing']
        
        # Compile regex patterns for better performance
        self._compile_patterns()
        
        # Initialize caches
        self._init_caches()
    
    def _compile_patterns(self):
        """Compile regex patterns for better performance"""
        self.compiled_model_patterns = [
            re.compile(pattern, re.IGNORECASE | re.UNICODE)
            for pattern in self.model_patterns
        ]
        
        self.compiled_sku_patterns = [
            re.compile(pattern, re.IGNORECASE | re.UNICODE)
            for pattern in self.sku_patterns
        ]
        
        # Thai character pattern
        self.thai_pattern = re.compile(r'[\u0E00-\u0E7F]+')
        
        # English character pattern
        self.english_pattern = re.compile(r'[a-zA-Z]+')
        
        # Number pattern
        self.number_pattern = re.compile(r'\d+(?:[.,]\d+)?')
        
        # Special character cleanup pattern
        self.special_char_pattern = re.compile(r'[^\w\s\-,.ก-๙]')
        
        # Multiple whitespace pattern
        self.whitespace_pattern = re.compile(r'\s+')
    
    def _init_caches(self):
        """Initialize LRU caches for performance"""
        cache_size = self.config['performance']['cache_size']
        
        # Cache for normalized text
        self.normalize_cache = {}
        self.sku_cache = {}
        self.spec_cache = {}
        
        # Set cache size limits
        self.max_cache_size = cache_size
    
    @lru_cache(maxsize=10000)
    def normalize(self, text: str) -> str:
        """Main normalization function with caching"""
        if not text:
            return ""
        
        # Unicode normalization
        normalized = unicodedata.normalize(self.text_settings['unicode_normalization'], text)
        
        # Convert to lowercase
        normalized = normalized.lower()
        
        # Handle mixed Thai-English text
        normalized = self._normalize_mixed_language(normalized)
        
        # Replace Thai brands with English equivalents
        normalized = self._replace_brands(normalized)
        
        # Normalize units
        normalized = self._normalize_units(normalized)
        
        # Extract and preserve important patterns
        preserved_patterns = self._extract_preserved_patterns(text)
        
        # Clean special characters
        normalized = self._clean_special_chars(normalized)
        
        # Remove stop words
        normalized = self._remove_stop_words(normalized)
        
        # Re-add preserved patterns
        if preserved_patterns:
            normalized += ' ' + ' '.join(preserved_patterns)
        
        # Final cleanup
        normalized = self._final_cleanup(normalized)
        
        return normalized.strip()
    
    def _normalize_mixed_language(self, text: str) -> str:
        """Handle mixed Thai-English text normalization"""
        # Split into Thai and English segments
        segments = []
        current_pos = 0
        
        # Find Thai segments
        for match in self.thai_pattern.finditer(text):
            if match.start() > current_pos:
                # Add English segment
                segments.append(('en', text[current_pos:match.start()]))
            # Add Thai segment
            segments.append(('th', match.group()))
            current_pos = match.end()
        
        # Add remaining English segment
        if current_pos < len(text):
            segments.append(('en', text[current_pos:]))
        
        # Process each segment
        processed = []
        for lang, segment in segments:
            if lang == 'th':
                processed.append(self._normalize_thai_segment(segment))
            else:
                processed.append(self._normalize_english_segment(segment))
        
        return ''.join(processed)
    
    def _normalize_thai_segment(self, text: str) -> str:
        """Normalize Thai text segment"""
        # Remove Thai tone marks if configured
        if self.text_settings.get('remove_accents', False):
            # Thai tone marks: ่ ้ ๊ ๋
            text = re.sub(r'[่้๊๋]', '', text)
        
        # Normalize Thai spacing
        text = re.sub(r'([ก-๙])\s+([ก-๙])', r'\1\2', text)
        
        return text
    
    def _normalize_english_segment(self, text: str) -> str:
        """Normalize English text segment"""
        # Remove accents from English characters
        if self.text_settings.get('remove_accents', False):
            text = unicodedata.normalize('NFD', text)
            text = ''.join(c for c in text if unicodedata.category(c) != 'Mn')
        
        return text
    
    def _extract_preserved_patterns(self, text: str) -> List[str]:
        """Extract patterns that should be preserved"""
        preserved = []
        
        # Extract model numbers
        for pattern in self.compiled_model_patterns:
            matches = pattern.findall(text)
            preserved.extend(matches)
        
        # Extract SKUs
        for pattern in self.compiled_sku_patterns:
            matches = pattern.findall(text)
            preserved.extend(matches)
        
        # Extract numbers with units
        unit_numbers = re.findall(r'\d+(?:[.,]\d+)?\s*(?:' + '|'.join(self.unit_mappings.keys()) + ')', text)
        preserved.extend(unit_numbers)
        
        # Remove duplicates while preserving order
        seen = set()
        unique_preserved = []
        for item in preserved:
            if isinstance(item, tuple):
                item = item[0]
            item_normalized = item.upper().replace(' ', '')
            if item_normalized not in seen:
                seen.add(item_normalized)
                unique_preserved.append(item)
        
        return unique_preserved
    
    def _replace_brands(self, text: str) -> str:
        """Replace Thai brand names with English equivalents"""
        for thai, english in self.brand_mappings.items():
            # Use word boundaries for better matching
            pattern = r'\b' + re.escape(thai) + r'\b'
            text = re.sub(pattern, english, text, flags=re.IGNORECASE)
        
        return text
    
    def _normalize_units(self, text: str) -> str:
        """Normalize unit representations"""
        for thai, english in self.unit_mappings.items():
            # Use word boundaries to avoid partial replacements
            pattern = r'\b' + re.escape(thai) + r'\b'
            text = re.sub(pattern, english, text, flags=re.IGNORECASE)
        
        return text
    
    def _clean_special_chars(self, text: str) -> str:
        """Remove special characters while preserving important ones"""
        # Keep alphanumeric, Thai characters, spaces, and some punctuation
        if self.text_settings.get('preserve_hyphens', True):
            text = re.sub(r'[^\w\s\-,.ก-๙]', ' ', text)
        else:
            text = re.sub(r'[^\w\s,.ก-๙]', ' ', text)
        
        # Replace multiple spaces with single space
        text = self.whitespace_pattern.sub(' ', text)
        
        return text
    
    def _remove_stop_words(self, text: str) -> str:
        """Remove stop words from text"""
        words = text.split()
        filtered = [word for word in words if word not in self.stop_words and len(word) > 1]
        return ' '.join(filtered)
    
    def _final_cleanup(self, text: str) -> str:
        """Final text cleanup"""
        # Remove extra whitespace
        text = self.whitespace_pattern.sub(' ', text)
        
        # Remove leading/trailing whitespace
        text = text.strip()
        
        # Remove very short words (unless they're numbers)
        words = text.split()
        filtered = [
            word for word in words 
            if len(word) > 2 or word.isdigit() or any(c.isdigit() for c in word)
        ]
        
        return ' '.join(filtered)
    
    def extract_sku(self, text: str) -> Optional[str]:
        """Extract SKU or model number from text with caching"""
        if not text:
            return None
        
        # Check cache first
        cache_key = text.lower()
        if cache_key in self.sku_cache:
            return self.sku_cache[cache_key]
        
        # Try each SKU pattern
        for pattern in self.compiled_sku_patterns:
            matches = pattern.findall(text)
            for match in matches:
                sku = match if isinstance(match, str) else match[0]
                
                # Skip if it's a known brand name
                if sku.upper() in self.brand_exclusions:
                    continue
                
                # Skip if it's just numbers
                if sku.replace('-', '').replace('/', '').isdigit():
                    continue
                
                # Check length constraints
                if (len(sku) < self.text_settings['min_sku_length'] or 
                    len(sku) > self.text_settings['max_sku_length']):
                    continue
                
                # Must contain at least one digit
                if not any(c.isdigit() for c in sku):
                    continue
                
                # Cache and return
                result = sku.upper().replace(' ', '-')
                self.sku_cache[cache_key] = result
                return result
        
        # Cache miss result
        self.sku_cache[cache_key] = None
        return None
    
    def extract_specifications(self, text: str) -> Dict[str, str]:
        """Extract key specifications from product text with caching"""
        if not text:
            return {}
        
        # Check cache first
        cache_key = text.lower()
        if cache_key in self.spec_cache:
            return self.spec_cache[cache_key]
        
        specs = {}
        
        # Extract BTU capacity
        btu_pattern = r'(\d{1,2}[,.]?\d{3})\s*(?:BTU|บีทียู|btu)'
        btu_match = re.search(btu_pattern, text, re.IGNORECASE)
        if btu_match:
            specs['capacity_btu'] = btu_match.group(1).replace(',', '').replace('.', '')
        
        # Extract size in inches
        size_pattern = r'(\d+(?:\.\d+)?)\s*(?:inch|นิ้ว|"|\'\')'
        size_match = re.search(size_pattern, text, re.IGNORECASE)
        if size_match:
            specs['size_inch'] = size_match.group(1)
        
        # Extract volume in liters
        volume_pattern = r'(\d+(?:\.\d+)?)\s*(?:L|l|ลิตร|liters?|litres?)'
        volume_match = re.search(volume_pattern, text, re.IGNORECASE)
        if volume_match:
            specs['volume_liters'] = volume_match.group(1)
        
        # Extract power in watts
        power_pattern = r'(\d+(?:\.\d+)?)\s*(?:W|w|วัตต์|watts?|watt)'
        power_match = re.search(power_pattern, text, re.IGNORECASE)
        if power_match:
            specs['power_watts'] = power_match.group(1)
        
        # Extract weight in kg
        weight_pattern = r'(\d+(?:\.\d+)?)\s*(?:kg|กก\.|กิโลกรัม|kilograms?)'
        weight_match = re.search(weight_pattern, text, re.IGNORECASE)
        if weight_match:
            specs['weight_kg'] = weight_match.group(1)
        
        # Extract voltage
        voltage_pattern = r'(\d+(?:\.\d+)?)\s*(?:V|v|โวลต์|volts?|volt)'
        voltage_match = re.search(voltage_pattern, text, re.IGNORECASE)
        if voltage_match:
            specs['voltage_v'] = voltage_match.group(1)
        
        # Extract frequency
        freq_pattern = r'(\d+(?:\.\d+)?)\s*(?:Hz|hz|เฮิรตซ์|hertz)'
        freq_match = re.search(freq_pattern, text, re.IGNORECASE)
        if freq_match:
            specs['frequency_hz'] = freq_match.group(1)
        
        # Extract amperage
        amp_pattern = r'(\d+(?:\.\d+)?)\s*(?:A|a|แอมป์|amps?|ampere)'
        amp_match = re.search(amp_pattern, text, re.IGNORECASE)
        if amp_match:
            specs['amperage_a'] = amp_match.group(1)
        
        # Cache and return
        self.spec_cache[cache_key] = specs
        return specs
    
    def normalize_sku(self, sku: str) -> str:
        """Normalize SKU for comparison"""
        if not sku:
            return ""
        
        # Remove common separators and convert to uppercase
        normalized = sku.upper()
        normalized = normalized.replace('-', '').replace('/', '').replace(' ', '')
        normalized = normalized.replace('.', '').replace('_', '')
        
        return normalized
    
    def compare_skus(self, sku1: Optional[str], sku2: Optional[str]) -> bool:
        """Compare two SKUs with normalization"""
        if not sku1 or not sku2:
            return False
        
        norm1 = self.normalize_sku(sku1)
        norm2 = self.normalize_sku(sku2)
        
        # Direct match
        if norm1 == norm2:
            return True
        
        # Check if one is a substring of the other (partial SKU match)
        if len(norm1) >= 6 and len(norm2) >= 6:
            if norm1 in norm2 or norm2 in norm1:
                return True
        
        # Check for version variants (e.g., "ABC123" vs "ABC123V2")
        if len(norm1) >= 6 and len(norm2) >= 6:
            # Remove version suffixes
            base1 = re.sub(r'[A-Z]*\d*$', '', norm1)
            base2 = re.sub(r'[A-Z]*\d*$', '', norm2)
            if base1 == base2 and len(base1) >= 4:
                return True
        
        return False
    
    def calculate_similarity(self, text1: str, text2: str) -> float:
        """Calculate similarity between two normalized texts"""
        # Normalize both texts
        norm1 = self.normalize(text1)
        norm2 = self.normalize(text2)
        
        if not norm1 or not norm2:
            return 0.0
        
        # Token-based similarity
        tokens1 = set(norm1.split())
        tokens2 = set(norm2.split())
        
        if not tokens1 or not tokens2:
            return 0.0
        
        # Calculate various similarity metrics
        jaccard = self._jaccard_similarity(tokens1, tokens2)
        cosine = self._cosine_similarity(tokens1, tokens2)
        important_match = self._important_token_match(tokens1, tokens2)
        
        # Combine scores with weights
        similarity = (jaccard * 0.4 + cosine * 0.4 + important_match * 0.2)
        
        return min(1.0, similarity)
    
    def _jaccard_similarity(self, tokens1: Set[str], tokens2: Set[str]) -> float:
        """Calculate Jaccard similarity between token sets"""
        intersection = tokens1 & tokens2
        union = tokens1 | tokens2
        return len(intersection) / len(union) if union else 0.0
    
    def _cosine_similarity(self, tokens1: Set[str], tokens2: Set[str]) -> float:
        """Calculate cosine similarity between token sets"""
        intersection = tokens1 & tokens2
        if not intersection:
            return 0.0
        
        return len(intersection) / (len(tokens1) * len(tokens2)) ** 0.5
    
    def _important_token_match(self, tokens1: Set[str], tokens2: Set[str]) -> float:
        """Calculate score for important token matches"""
        intersection = tokens1 & tokens2
        if not intersection:
            return 0.0
        
        important_score = 0.0
        for token in intersection:
            # Give higher weight to longer tokens or tokens with digits
            if len(token) > 5:
                important_score += 0.3
            elif any(c.isdigit() for c in token):
                important_score += 0.2
            elif len(token) > 3:
                important_score += 0.1
        
        return min(1.0, important_score)
    
    def clear_cache(self):
        """Clear all caches"""
        self.sku_cache.clear()
        self.spec_cache.clear()
    
    def get_cache_stats(self) -> Dict[str, int]:
        """Get cache statistics"""
        return {
            'sku_cache_size': len(self.sku_cache),
            'spec_cache_size': len(self.spec_cache),
            'max_cache_size': self.max_cache_size
        }


# Example usage and testing
if __name__ == "__main__":
    # Initialize enhanced normalizer
    normalizer = EnhancedTextNormalizer()
    
    # Test cases
    test_cases = [
        "MITSUBISHI แอร์ติดผนัง รุ่น MSY-KP13VF 12000BTU",
        "มิตซูบิชิ เครื่องปรับอากาศ MSY-KP13VF 12,000 บีทียู",
        "Samsung ตู้เย็น 2 ประตู 300 ลิตร RT29K5511S8",
        "ซัมซุง ตู้เย็น 2 ประตู 300L รุ่น RT29K5511S8",
        "LG Smart TV 55 นิ้ว รุ่น 55UN7300PTC",
        "แอลจี สมาร์ททีวี 55\" 55UN7300PTC",
    ]
    
    print("Enhanced Text Normalizer Test Results:")
    print("=" * 50)
    
    for i, text in enumerate(test_cases, 1):
        print(f"\nTest {i}: {text}")
        normalized = normalizer.normalize(text)
        sku = normalizer.extract_sku(text)
        specs = normalizer.extract_specifications(text)
        
        print(f"  Normalized: {normalized}")
        print(f"  SKU: {sku}")
        print(f"  Specs: {specs}")
    
    # Test similarity
    print(f"\nSimilarity Tests:")
    print("=" * 50)
    
    pairs = [
        (test_cases[0], test_cases[1]),
        (test_cases[2], test_cases[3]),
        (test_cases[4], test_cases[5]),
    ]
    
    for text1, text2 in pairs:
        similarity = normalizer.calculate_similarity(text1, text2)
        print(f"\nSimilarity: {similarity:.3f}")
        print(f"  Text 1: {text1}")
        print(f"  Text 2: {text2}")
    
    # Cache statistics
    print(f"\nCache Statistics:")
    print(normalizer.get_cache_stats())