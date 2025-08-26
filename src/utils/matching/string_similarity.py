"""
String similarity utilities for product name matching
Implements various algorithms for fuzzy string matching and text similarity
"""
import re
import logging
from typing import List, Tuple, Dict, Any, Optional
from difflib import SequenceMatcher
from collections import Counter
import unicodedata

try:
    from rapidfuzz import fuzz, process
    RAPIDFUZZ_AVAILABLE = True
except ImportError:
    try:
        from fuzzywuzzy import fuzz, process
        RAPIDFUZZ_AVAILABLE = False
    except ImportError:
        fuzz = None
        process = None
        RAPIDFUZZ_AVAILABLE = False

logger = logging.getLogger(__name__)


class StringSimilarity:
    """Advanced string similarity calculations for product matching"""
    
    def __init__(self):
        self.fuzzy_available = fuzz is not None
        if not self.fuzzy_available:
            logger.warning("Neither rapidfuzz nor fuzzywuzzy available. Some features may be limited.")
    
    def calculate_similarity(
        self,
        text1: str,
        text2: str,
        method: str = 'hybrid'
    ) -> float:
        """
        Calculate similarity between two strings
        
        Args:
            text1, text2: Strings to compare
            method: Similarity method ('exact', 'fuzzy', 'token', 'hybrid')
        
        Returns:
            Similarity score (0.0 to 1.0)
        """
        if not text1 or not text2:
            return 0.0
        
        # Normalize inputs
        norm_text1 = self.normalize_text(text1)
        norm_text2 = self.normalize_text(text2)
        
        if method == 'exact':
            return 1.0 if norm_text1 == norm_text2 else 0.0
        elif method == 'fuzzy':
            return self._fuzzy_similarity(norm_text1, norm_text2)
        elif method == 'token':
            return self._token_similarity(norm_text1, norm_text2)
        elif method == 'hybrid':
            return self._hybrid_similarity(norm_text1, norm_text2)
        else:
            raise ValueError(f"Unknown similarity method: {method}")
    
    def normalize_text(self, text: str) -> str:
        """
        Normalize text for comparison
        
        Args:
            text: Input text
            
        Returns:
            Normalized text
        """
        if not text:
            return ""
        
        # Convert to lowercase
        text = text.lower()
        
        # Unicode normalization
        text = unicodedata.normalize('NFKD', text)
        
        # Remove extra whitespace
        text = ' '.join(text.split())
        
        # Remove common noise words and characters
        noise_patterns = [
            r'\b(for|and|with|or|the|a|an)\b',
            r'[^\w\s\-.]',  # Keep only alphanumeric, spaces, hyphens, dots
            r'\s+',  # Multiple spaces to single space
        ]
        
        for pattern in noise_patterns[:-1]:
            text = re.sub(pattern, ' ', text)
        
        # Final cleanup
        text = re.sub(noise_patterns[-1], ' ', text).strip()
        
        return text
    
    def extract_tokens(self, text: str) -> List[str]:
        """
        Extract meaningful tokens from text
        
        Args:
            text: Input text
            
        Returns:
            List of tokens
        """
        normalized = self.normalize_text(text)
        
        # Split by common separators
        tokens = re.split(r'[\s\-_.,/\\]+', normalized)
        
        # Filter out short tokens and common words
        stop_words = {
            'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
            'of', 'with', 'by', 'is', 'are', 'was', 'were', 'be', 'been', 'have',
            'has', 'had', 'do', 'does', 'did', 'will', 'would', 'should', 'could',
            'may', 'might', 'can', 'shall'
        }
        
        meaningful_tokens = []
        for token in tokens:
            if len(token) >= 2 and token not in stop_words:
                meaningful_tokens.append(token)
        
        return meaningful_tokens
    
    def calculate_token_overlap(
        self,
        text1: str,
        text2: str
    ) -> Dict[str, Any]:
        """
        Calculate token-based overlap between texts
        
        Args:
            text1, text2: Texts to compare
            
        Returns:
            Dictionary with overlap statistics
        """
        tokens1 = self.extract_tokens(text1)
        tokens2 = self.extract_tokens(text2)
        
        if not tokens1 or not tokens2:
            return {
                'common_tokens': [],
                'unique_tokens_1': tokens1,
                'unique_tokens_2': tokens2,
                'overlap_ratio': 0.0,
                'jaccard_similarity': 0.0
            }
        
        set1, set2 = set(tokens1), set(tokens2)
        common_tokens = set1 & set2
        all_tokens = set1 | set2
        
        overlap_ratio = len(common_tokens) / min(len(set1), len(set2))
        jaccard_similarity = len(common_tokens) / len(all_tokens)
        
        return {
            'common_tokens': list(common_tokens),
            'unique_tokens_1': list(set1 - common_tokens),
            'unique_tokens_2': list(set2 - common_tokens),
            'overlap_ratio': overlap_ratio,
            'jaccard_similarity': jaccard_similarity
        }
    
    def _fuzzy_similarity(self, text1: str, text2: str) -> float:
        """Calculate fuzzy string similarity"""
        if not self.fuzzy_available:
            # Fallback to difflib
            return SequenceMatcher(None, text1, text2).ratio()
        
        # Use rapidfuzz or fuzzywuzzy
        return fuzz.ratio(text1, text2) / 100.0
    
    def _token_similarity(self, text1: str, text2: str) -> float:
        """Calculate token-based similarity"""
        if not self.fuzzy_available:
            overlap = self.calculate_token_overlap(text1, text2)
            return overlap['jaccard_similarity']
        
        # Use token sort ratio from fuzzy library
        return fuzz.token_sort_ratio(text1, text2) / 100.0
    
    def _hybrid_similarity(self, text1: str, text2: str) -> float:
        """Calculate hybrid similarity combining multiple methods"""
        
        # Weight different similarity measures
        weights = {
            'exact': 0.3,
            'fuzzy': 0.25,
            'token_sort': 0.25,
            'token_set': 0.2
        }
        
        scores = {}
        
        # Exact match bonus
        scores['exact'] = 1.0 if text1 == text2 else 0.0
        
        if self.fuzzy_available:
            # Fuzzy similarities
            scores['fuzzy'] = fuzz.ratio(text1, text2) / 100.0
            scores['token_sort'] = fuzz.token_sort_ratio(text1, text2) / 100.0
            scores['token_set'] = fuzz.token_set_ratio(text1, text2) / 100.0
        else:
            # Fallback implementations
            scores['fuzzy'] = SequenceMatcher(None, text1, text2).ratio()
            overlap = self.calculate_token_overlap(text1, text2)
            scores['token_sort'] = overlap['jaccard_similarity']
            scores['token_set'] = overlap['overlap_ratio']
        
        # Calculate weighted average
        weighted_score = sum(
            scores[method] * weight 
            for method, weight in weights.items()
        )
        
        return weighted_score
    
    def find_best_matches(
        self,
        query: str,
        candidates: List[str],
        limit: int = 5,
        threshold: float = 0.6
    ) -> List[Tuple[str, float]]:
        """
        Find best matching candidates for a query
        
        Args:
            query: Query string
            candidates: List of candidate strings
            limit: Maximum number of results
            threshold: Minimum similarity threshold
            
        Returns:
            List of (candidate, similarity_score) tuples
        """
        if not query or not candidates:
            return []
        
        if self.fuzzy_available and process:
            # Use fuzzy process for efficient matching
            results = process.extract(
                query, candidates, 
                limit=limit,
                score_cutoff=threshold * 100
            )
            return [(match[0], match[1] / 100.0) for match in results]
        else:
            # Manual implementation
            scored_candidates = []
            
            for candidate in candidates:
                similarity = self.calculate_similarity(query, candidate, 'hybrid')
                if similarity >= threshold:
                    scored_candidates.append((candidate, similarity))
            
            # Sort by similarity and return top matches
            scored_candidates.sort(key=lambda x: x[1], reverse=True)
            return scored_candidates[:limit]
    
    def calculate_name_similarity_detailed(
        self,
        name1: str,
        name2: str
    ) -> Dict[str, Any]:
        """
        Calculate detailed similarity analysis between product names
        
        Args:
            name1, name2: Product names to compare
            
        Returns:
            Detailed similarity analysis
        """
        norm1 = self.normalize_text(name1)
        norm2 = self.normalize_text(name2)
        
        # Basic similarity scores
        exact_match = norm1 == norm2
        
        similarities = {
            'fuzzy_ratio': self._fuzzy_similarity(norm1, norm2),
            'token_similarity': self._token_similarity(norm1, norm2),
            'hybrid_similarity': self._hybrid_similarity(norm1, norm2)
        }
        
        # Token analysis
        token_analysis = self.calculate_token_overlap(name1, name2)
        
        # Length similarity
        len1, len2 = len(norm1), len(norm2)
        length_ratio = min(len1, len2) / max(len1, len2) if max(len1, len2) > 0 else 0
        
        # Calculate final confidence score
        confidence = similarities['hybrid_similarity']
        
        # Boost for exact match
        if exact_match:
            confidence = 1.0
        
        # Boost for high token overlap
        if token_analysis['overlap_ratio'] > 0.8:
            confidence = min(1.0, confidence + 0.1)
        
        # Penalty for very different lengths
        if length_ratio < 0.5:
            confidence *= 0.9
        
        return {
            'original_name_1': name1,
            'original_name_2': name2,
            'normalized_name_1': norm1,
            'normalized_name_2': norm2,
            'exact_match': exact_match,
            'similarities': similarities,
            'token_analysis': token_analysis,
            'length_ratio': length_ratio,
            'final_confidence': round(confidence, 3),
            'method': 'string_similarity_v2'
        }