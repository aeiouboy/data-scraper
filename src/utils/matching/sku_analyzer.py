"""
SKU analysis utility for product matching
"""
import re
import logging
from typing import Optional, Dict, Any, List, Tuple, Set

logger = logging.getLogger(__name__)


class SKUAnalyzer:
    """Utility class for SKU analysis and comparison"""
    
    # Common SKU patterns
    SKU_PATTERNS = [
        r'^[A-Z]{2,4}-?\d{3,8}$',  # Standard format: ABC-123456
        r'^\d{8,12}$',             # Pure numeric
        r'^[A-Z]\d{6,10}$',        # Letter followed by numbers
        r'^[A-Z]{2,3}\d{3,6}[A-Z]?$',  # Mixed alphanumeric
    ]
    
    def __init__(self):
        self.sku_cache = {}
    
    def normalize_sku(self, sku: str) -> str:
        """
        Normalize SKU by removing common separators and standardizing format
        
        Args:
            sku: Raw SKU string
            
        Returns:
            Normalized SKU
        """
        if not sku:
            return ""
        
        # Cache check
        if sku in self.sku_cache:
            return self.sku_cache[sku]
        
        # Basic normalization
        normalized = sku.strip().upper()
        
        # Remove common separators
        normalized = re.sub(r'[-_\s]+', '', normalized)
        
        # Remove leading zeros from numeric parts (but preserve if it's all zeros)
        normalized = re.sub(r'\b0+(\d+)', r'\1', normalized)
        
        self.sku_cache[sku] = normalized
        return normalized
    
    def skus_match(self, sku1: str, sku2: str) -> bool:
        """
        Check if two SKUs match exactly
        
        Args:
            sku1: First SKU
            sku2: Second SKU
            
        Returns:
            True if SKUs match
        """
        if not sku1 or not sku2:
            return False
        
        normalized1 = self.normalize_sku(sku1)
        normalized2 = self.normalize_sku(sku2)
        
        return normalized1 == normalized2
    
    def calculate_sku_similarity(self, sku1: str, sku2: str) -> float:
        """
        Calculate similarity score between two SKUs
        
        Args:
            sku1: First SKU
            sku2: Second SKU
            
        Returns:
            Similarity score between 0.0 and 1.0
        """
        if not sku1 or not sku2:
            return 0.0
        
        # Exact match
        if self.skus_match(sku1, sku2):
            return 1.0
        
        normalized1 = self.normalize_sku(sku1)
        normalized2 = self.normalize_sku(sku2)
        
        # Check if one is substring of another
        if normalized1 in normalized2 or normalized2 in normalized1:
            # Higher score if the shorter one is significant portion
            min_len = min(len(normalized1), len(normalized2))
            max_len = max(len(normalized1), len(normalized2))
            
            if min_len >= 4:  # Minimum meaningful SKU length
                return min_len / max_len
        
        # Character-level similarity
        common_chars = sum(c1 == c2 for c1, c2 in zip(normalized1, normalized2))
        max_len = max(len(normalized1), len(normalized2))
        
        return common_chars / max_len if max_len > 0 else 0.0
    
    def extract_sku_components(self, sku: str) -> Dict[str, Any]:
        """
        Extract components from SKU for analysis
        
        Args:
            sku: SKU to analyze
            
        Returns:
            Dictionary with SKU components
        """
        if not sku:
            return {}
        
        normalized = self.normalize_sku(sku)
        
        # Extract letters and numbers
        letters = re.findall(r'[A-Z]+', normalized)
        numbers = re.findall(r'\d+', normalized)
        
        return {
            'original': sku,
            'normalized': normalized,
            'letters': letters,
            'numbers': numbers,
            'length': len(normalized),
            'has_letters': bool(letters),
            'has_numbers': bool(numbers),
            'pattern_match': self._identify_pattern(normalized)
        }
    
    def _identify_pattern(self, sku: str) -> Optional[str]:
        """
        Identify which pattern the SKU matches
        
        Args:
            sku: Normalized SKU
            
        Returns:
            Pattern name or None
        """
        for i, pattern in enumerate(self.SKU_PATTERNS):
            if re.match(pattern, sku):
                return f"pattern_{i}"
        
        return None