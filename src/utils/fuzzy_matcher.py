"""
Advanced Fuzzy String Matching Algorithms
Implements multiple fuzzy matching techniques for product name comparison
"""

import re
import math
import logging
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from difflib import SequenceMatcher
import unicodedata

logger = logging.getLogger(__name__)


@dataclass
class FuzzyMatchResult:
    """Result of fuzzy matching with detailed scores"""
    similarity: float
    method: str
    details: Dict[str, Any]
    confidence: float


class FuzzyMatcher:
    """Advanced fuzzy string matching system"""
    
    def __init__(self, config: Optional[Dict] = None):
        """Initialize fuzzy matcher with configuration"""
        self.config = config or {}
        
        # Matching algorithm weights
        self.algorithm_weights = {
            'levenshtein': 0.25,
            'jaro_winkler': 0.25,
            'cosine': 0.20,
            'jaccard': 0.15,
            'longest_common_subsequence': 0.10,
            'soundex': 0.05
        }
        
        # Thai character mappings for phonetic matching
        self.thai_phonetic_map = {
            'ก': 'k', 'ข': 'k', 'ค': 'k', 'ฆ': 'k',
            'จ': 'j', 'ฉ': 'ch', 'ช': 'ch', 'ซ': 's',
            'ด': 'd', 'ต': 't', 'ถ': 't', 'ท': 't', 'ธ': 't',
            'น': 'n', 'บ': 'b', 'ป': 'p', 'ผ': 'p', 'ฝ': 'f',
            'พ': 'p', 'ฟ': 'f', 'ภ': 'p', 'ม': 'm',
            'ย': 'y', 'ร': 'r', 'ล': 'l', 'ว': 'w',
            'ศ': 's', 'ษ': 's', 'ส': 's', 'ห': 'h',
            'อ': '', 'ฮ': 'h'
        }
        
        # Preprocessing patterns
        self.preprocessing_patterns = [
            (r'\s+', ' '),  # Multiple spaces to single
            (r'[^\w\s\u0E00-\u0E7F]', ''),  # Remove special chars except Thai
            (r'\b(model|รุ่น|type|series)\b', ''),  # Remove common prefixes
        ]
    
    def calculate_similarity(self, text1: str, text2: str, 
                           methods: Optional[List[str]] = None) -> FuzzyMatchResult:
        """
        Calculate fuzzy similarity using multiple algorithms
        
        Args:
            text1: First text string
            text2: Second text string
            methods: Optional list of specific methods to use
            
        Returns:
            FuzzyMatchResult with combined similarity score
        """
        if not text1 or not text2:
            return FuzzyMatchResult(
                similarity=0.0,
                method='empty_input',
                details={'reason': 'Empty input strings'},
                confidence=0.0
            )
        
        # Preprocess texts
        processed_text1 = self._preprocess_text(text1)
        processed_text2 = self._preprocess_text(text2)
        
        # Calculate similarities using different algorithms
        similarities = {}
        details = {}
        
        # Use specified methods or all available
        if methods is None:
            methods = list(self.algorithm_weights.keys())
        
        for method in methods:
            if method in self.algorithm_weights:
                try:
                    similarity, method_details = self._calculate_method_similarity(
                        processed_text1, processed_text2, method
                    )
                    similarities[method] = similarity
                    details[method] = method_details
                except Exception as e:
                    logger.warning(f"Error in {method} calculation: {e}")
                    similarities[method] = 0.0
                    details[method] = {'error': str(e)}
        
        # Calculate weighted average
        total_weight = sum(self.algorithm_weights[m] for m in similarities.keys())
        if total_weight > 0:
            weighted_similarity = sum(
                similarities[m] * self.algorithm_weights[m] 
                for m in similarities.keys()
            ) / total_weight
        else:
            weighted_similarity = 0.0
        
        # Calculate confidence based on agreement between methods
        confidence = self._calculate_confidence(similarities)
        
        return FuzzyMatchResult(
            similarity=weighted_similarity,
            method='weighted_ensemble',
            details={
                'individual_scores': similarities,
                'method_details': details,
                'weights': {m: self.algorithm_weights[m] for m in similarities.keys()},
                'processed_text1': processed_text1,
                'processed_text2': processed_text2
            },
            confidence=confidence
        )
    
    def _preprocess_text(self, text: str) -> str:
        """Preprocess text for fuzzy matching"""
        # Normalize unicode
        text = unicodedata.normalize('NFKC', text)
        
        # Convert to lowercase
        text = text.lower()
        
        # Apply preprocessing patterns
        for pattern, replacement in self.preprocessing_patterns:
            text = re.sub(pattern, replacement, text, flags=re.IGNORECASE)
        
        # Strip and normalize whitespace
        text = ' '.join(text.split())
        
        return text
    
    def _calculate_method_similarity(self, text1: str, text2: str, method: str) -> Tuple[float, Dict]:
        """Calculate similarity using specific method"""
        if method == 'levenshtein':
            return self._levenshtein_similarity(text1, text2)
        elif method == 'jaro_winkler':
            return self._jaro_winkler_similarity(text1, text2)
        elif method == 'cosine':
            return self._cosine_similarity(text1, text2)
        elif method == 'jaccard':
            return self._jaccard_similarity(text1, text2)
        elif method == 'longest_common_subsequence':
            return self._lcs_similarity(text1, text2)
        elif method == 'soundex':
            return self._soundex_similarity(text1, text2)
        else:
            return 0.0, {'error': f'Unknown method: {method}'}
    
    def _levenshtein_similarity(self, text1: str, text2: str) -> Tuple[float, Dict]:
        """Calculate Levenshtein distance based similarity"""
        if not text1 or not text2:
            return 0.0, {'distance': -1}
        
        # Calculate Levenshtein distance
        distance = self._levenshtein_distance(text1, text2)
        max_len = max(len(text1), len(text2))
        
        # Convert to similarity (0-1)
        similarity = 1 - (distance / max_len) if max_len > 0 else 0.0
        
        return similarity, {
            'distance': distance,
            'max_length': max_len,
            'normalized_distance': distance / max_len if max_len > 0 else 0
        }
    
    def _levenshtein_distance(self, s1: str, s2: str) -> int:
        """Calculate Levenshtein distance between two strings"""
        if len(s1) < len(s2):
            return self._levenshtein_distance(s2, s1)
        
        if len(s2) == 0:
            return len(s1)
        
        previous_row = list(range(len(s2) + 1))
        for i, c1 in enumerate(s1):
            current_row = [i + 1]
            for j, c2 in enumerate(s2):
                insertions = previous_row[j + 1] + 1
                deletions = current_row[j] + 1
                substitutions = previous_row[j] + (c1 != c2)
                current_row.append(min(insertions, deletions, substitutions))
            previous_row = current_row
        
        return previous_row[-1]
    
    def _jaro_winkler_similarity(self, text1: str, text2: str) -> Tuple[float, Dict]:
        """Calculate Jaro-Winkler similarity"""
        if not text1 or not text2:
            return 0.0, {'jaro': 0.0, 'winkler_bonus': 0.0}
        
        # Calculate Jaro similarity
        jaro_sim = self._jaro_similarity(text1, text2)
        
        # Calculate Winkler prefix bonus
        prefix_length = 0
        for i in range(min(len(text1), len(text2), 4)):
            if text1[i] == text2[i]:
                prefix_length += 1
            else:
                break
        
        winkler_bonus = 0.1 * prefix_length * (1 - jaro_sim)
        jaro_winkler_sim = jaro_sim + winkler_bonus
        
        return jaro_winkler_sim, {
            'jaro': jaro_sim,
            'prefix_length': prefix_length,
            'winkler_bonus': winkler_bonus
        }
    
    def _jaro_similarity(self, s1: str, s2: str) -> float:
        """Calculate Jaro similarity"""
        if s1 == s2:
            return 1.0
        
        len1, len2 = len(s1), len(s2)
        if len1 == 0 or len2 == 0:
            return 0.0
        
        # Calculate match window
        match_window = max(len1, len2) // 2 - 1
        match_window = max(0, match_window)
        
        # Initialize match arrays
        s1_matches = [False] * len1
        s2_matches = [False] * len2
        
        matches = 0
        transpositions = 0
        
        # Find matches
        for i in range(len1):
            start = max(0, i - match_window)
            end = min(i + match_window + 1, len2)
            
            for j in range(start, end):
                if s2_matches[j] or s1[i] != s2[j]:
                    continue
                s1_matches[i] = s2_matches[j] = True
                matches += 1
                break
        
        if matches == 0:
            return 0.0
        
        # Count transpositions
        k = 0
        for i in range(len1):
            if not s1_matches[i]:
                continue
            while not s2_matches[k]:
                k += 1
            if s1[i] != s2[k]:
                transpositions += 1
            k += 1
        
        # Calculate Jaro similarity
        jaro = (matches / len1 + matches / len2 + (matches - transpositions / 2) / matches) / 3
        return jaro
    
    def _cosine_similarity(self, text1: str, text2: str) -> Tuple[float, Dict]:
        """Calculate cosine similarity using character n-grams"""
        if not text1 or not text2:
            return 0.0, {'ngram_size': 0}
        
        # Generate character bigrams
        ngrams1 = self._get_ngrams(text1, 2)
        ngrams2 = self._get_ngrams(text2, 2)
        
        if not ngrams1 or not ngrams2:
            return 0.0, {'ngram_size': 0}
        
        # Calculate cosine similarity
        intersection = set(ngrams1.keys()) & set(ngrams2.keys())
        
        if not intersection:
            return 0.0, {'ngram_size': 0, 'intersection_size': 0}
        
        # Calculate dot product
        dot_product = sum(ngrams1[gram] * ngrams2[gram] for gram in intersection)
        
        # Calculate magnitudes
        magnitude1 = math.sqrt(sum(count ** 2 for count in ngrams1.values()))
        magnitude2 = math.sqrt(sum(count ** 2 for count in ngrams2.values()))
        
        # Calculate cosine similarity
        if magnitude1 * magnitude2 == 0:
            return 0.0, {'magnitude_product': 0}
        
        cosine_sim = dot_product / (magnitude1 * magnitude2)
        
        return cosine_sim, {
            'ngrams1_count': len(ngrams1),
            'ngrams2_count': len(ngrams2),
            'intersection_size': len(intersection),
            'dot_product': dot_product,
            'magnitude1': magnitude1,
            'magnitude2': magnitude2
        }
    
    def _get_ngrams(self, text: str, n: int) -> Dict[str, int]:
        """Generate n-grams from text"""
        if len(text) < n:
            return {text: 1}
        
        ngrams = {}
        for i in range(len(text) - n + 1):
            gram = text[i:i + n]
            ngrams[gram] = ngrams.get(gram, 0) + 1
        
        return ngrams
    
    def _jaccard_similarity(self, text1: str, text2: str) -> Tuple[float, Dict]:
        """Calculate Jaccard similarity using character sets"""
        if not text1 or not text2:
            return 0.0, {'union_size': 0, 'intersection_size': 0}
        
        # Convert to character sets
        set1 = set(text1)
        set2 = set(text2)
        
        # Calculate Jaccard similarity
        intersection = set1 & set2
        union = set1 | set2
        
        if not union:
            return 0.0, {'union_size': 0, 'intersection_size': 0}
        
        jaccard_sim = len(intersection) / len(union)
        
        return jaccard_sim, {
            'set1_size': len(set1),
            'set2_size': len(set2),
            'intersection_size': len(intersection),
            'union_size': len(union)
        }
    
    def _lcs_similarity(self, text1: str, text2: str) -> Tuple[float, Dict]:
        """Calculate similarity based on Longest Common Subsequence"""
        if not text1 or not text2:
            return 0.0, {'lcs_length': 0}
        
        # Calculate LCS length
        lcs_length = self._lcs_length(text1, text2)
        max_length = max(len(text1), len(text2))
        
        # Convert to similarity
        similarity = lcs_length / max_length if max_length > 0 else 0.0
        
        return similarity, {
            'lcs_length': lcs_length,
            'text1_length': len(text1),
            'text2_length': len(text2),
            'max_length': max_length
        }
    
    def _lcs_length(self, s1: str, s2: str) -> int:
        """Calculate length of Longest Common Subsequence"""
        m, n = len(s1), len(s2)
        
        # Create DP table
        dp = [[0] * (n + 1) for _ in range(m + 1)]
        
        # Fill DP table
        for i in range(1, m + 1):
            for j in range(1, n + 1):
                if s1[i - 1] == s2[j - 1]:
                    dp[i][j] = dp[i - 1][j - 1] + 1
                else:
                    dp[i][j] = max(dp[i - 1][j], dp[i][j - 1])
        
        return dp[m][n]
    
    def _soundex_similarity(self, text1: str, text2: str) -> Tuple[float, Dict]:
        """Calculate similarity using Soundex phonetic algorithm"""
        if not text1 or not text2:
            return 0.0, {'soundex1': '', 'soundex2': ''}
        
        # Generate Soundex codes
        soundex1 = self._soundex(text1)
        soundex2 = self._soundex(text2)
        
        # Calculate similarity
        similarity = 1.0 if soundex1 == soundex2 else 0.0
        
        # For partial matching, compare character by character
        if similarity == 0.0 and soundex1 and soundex2:
            matches = sum(1 for a, b in zip(soundex1, soundex2) if a == b)
            similarity = matches / max(len(soundex1), len(soundex2))
        
        return similarity, {
            'soundex1': soundex1,
            'soundex2': soundex2,
            'exact_match': soundex1 == soundex2
        }
    
    def _soundex(self, text: str) -> str:
        """Generate Soundex code for text"""
        if not text:
            return ""
        
        # Convert to uppercase and keep only alphabetic characters
        text = ''.join(c for c in text.upper() if c.isalpha() or ord(c) >= 0x0E00)
        
        if not text:
            return ""
        
        # Handle Thai characters
        if any(ord(c) >= 0x0E00 for c in text):
            return self._thai_soundex(text)
        
        # Standard English Soundex
        return self._english_soundex(text)
    
    def _english_soundex(self, text: str) -> str:
        """Generate English Soundex code"""
        if not text:
            return ""
        
        # Soundex mapping
        soundex_map = {
            'B': '1', 'F': '1', 'P': '1', 'V': '1',
            'C': '2', 'G': '2', 'J': '2', 'K': '2', 'Q': '2', 'S': '2', 'X': '2', 'Z': '2',
            'D': '3', 'T': '3',
            'L': '4',
            'M': '5', 'N': '5',
            'R': '6'
        }
        
        # Keep first letter
        result = text[0]
        
        # Convert rest to codes
        for char in text[1:]:
            if char in soundex_map:
                code = soundex_map[char]
                if result[-1] != code:  # Avoid consecutive duplicates
                    result += code
        
        # Pad or truncate to 4 characters
        result = (result + '000')[:4]
        
        return result
    
    def _thai_soundex(self, text: str) -> str:
        """Generate Thai phonetic code"""
        result = ""
        
        for char in text:
            if char in self.thai_phonetic_map:
                phonetic = self.thai_phonetic_map[char]
                if phonetic and (not result or result[-1] != phonetic):
                    result += phonetic
        
        return result[:4].ljust(4, '0')
    
    def _calculate_confidence(self, similarities: Dict[str, float]) -> float:
        """Calculate confidence based on agreement between methods"""
        if not similarities:
            return 0.0
        
        values = list(similarities.values())
        if len(values) == 1:
            return values[0]
        
        # Calculate standard deviation
        mean_sim = sum(values) / len(values)
        variance = sum((x - mean_sim) ** 2 for x in values) / len(values)
        std_dev = math.sqrt(variance)
        
        # High agreement (low std dev) means high confidence
        max_std_dev = 0.5  # Maximum expected standard deviation
        confidence = max(0.0, 1.0 - (std_dev / max_std_dev))
        
        return confidence
    
    def find_best_matches(self, target: str, candidates: List[str], 
                         top_k: int = 5, min_similarity: float = 0.5) -> List[Tuple[str, FuzzyMatchResult]]:
        """
        Find best fuzzy matches for target string
        
        Args:
            target: Target string to match
            candidates: List of candidate strings
            top_k: Number of top matches to return
            min_similarity: Minimum similarity threshold
            
        Returns:
            List of (candidate, FuzzyMatchResult) tuples sorted by similarity
        """
        results = []
        
        for candidate in candidates:
            result = self.calculate_similarity(target, candidate)
            if result.similarity >= min_similarity:
                results.append((candidate, result))
        
        # Sort by similarity and return top k
        results.sort(key=lambda x: x[1].similarity, reverse=True)
        return results[:top_k]
    
    def batch_similarity(self, pairs: List[Tuple[str, str]]) -> List[FuzzyMatchResult]:
        """Calculate similarity for multiple string pairs"""
        results = []
        
        for text1, text2 in pairs:
            result = self.calculate_similarity(text1, text2)
            results.append(result)
        
        return results


# Example usage and testing
if __name__ == "__main__":
    # Initialize fuzzy matcher
    matcher = FuzzyMatcher()
    
    # Test cases with Thai and English text
    test_pairs = [
        ("MITSUBISHI แอร์ติดผนัง", "มิตซูบิชิ เครื่องปรับอากาศ"),
        ("Samsung ตู้เย็น RT29K5511S8", "ซัมซุง ตู้เย็น RT29K5511S8"),
        ("LG Smart TV 55 นิ้ว", "แอลจี สมาร์ททีวี 55 inch"),
        ("Bosch Professional Drill", "Bosch Pro Drill"),
        ("iPhone 13 Pro Max", "iPhone 13 ProMax"),
        ("Different Product", "Completely Other Item")
    ]
    
    print("Fuzzy String Matching Test Results:")
    print("=" * 60)
    
    for i, (text1, text2) in enumerate(test_pairs, 1):
        result = matcher.calculate_similarity(text1, text2)
        
        print(f"\nTest {i}:")
        print(f"  Text 1: {text1}")
        print(f"  Text 2: {text2}")
        print(f"  Similarity: {result.similarity:.3f}")
        print(f"  Confidence: {result.confidence:.3f}")
        print(f"  Method: {result.method}")
        
        # Show individual algorithm scores
        individual_scores = result.details.get('individual_scores', {})
        print(f"  Individual Scores:")
        for method, score in individual_scores.items():
            print(f"    {method}: {score:.3f}")
    
    # Test best matches
    print(f"\n\nBest Matches Test:")
    print("=" * 60)
    
    target = "Samsung Smart TV 55 นิ้ว"
    candidates = [
        "ซัมซุง สมาร์ททีวี 55 inch",
        "Samsung 55 inch Smart Television",
        "LG Smart TV 55 นิ้ว",
        "Sony 55 inch TV",
        "Samsung Galaxy Phone",
        "Samsung ตู้เย็น",
        "ซัมซุง Smart TV 55\""
    ]
    
    best_matches = matcher.find_best_matches(target, candidates, top_k=3, min_similarity=0.3)
    
    print(f"Target: {target}")
    print(f"Found {len(best_matches)} matches:")
    
    for i, (candidate, result) in enumerate(best_matches, 1):
        print(f"  {i}. {candidate}")
        print(f"     Similarity: {result.similarity:.3f}")
        print(f"     Confidence: {result.confidence:.3f}")
    
    # Performance test
    print(f"\n\nPerformance Test:")
    print("=" * 60)
    
    import time
    
    # Test batch processing
    batch_pairs = test_pairs * 100  # 600 pairs
    
    start_time = time.time()
    batch_results = matcher.batch_similarity(batch_pairs)
    end_time = time.time()
    
    print(f"Processed {len(batch_pairs)} pairs in {end_time - start_time:.3f} seconds")
    print(f"Average time per pair: {(end_time - start_time) / len(batch_pairs) * 1000:.3f} ms")
    
    avg_similarity = sum(r.similarity for r in batch_results) / len(batch_results)
    print(f"Average similarity: {avg_similarity:.3f}")