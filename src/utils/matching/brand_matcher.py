"""
Brand matching utility for product comparison
"""
import logging
from typing import Optional, Dict, Any, List, Tuple
from src.utils.brand_alias_manager import BrandAliasManager

logger = logging.getLogger(__name__)


class BrandMatcher:
    """Utility class for brand matching and comparison"""
    
    def __init__(self):
        self.alias_manager = BrandAliasManager()
    
    def normalize_brand(self, brand: str) -> str:
        """
        Normalize brand name using the alias manager
        
        Args:
            brand: Raw brand name
            
        Returns:
            Normalized brand name
        """
        if not brand:
            return ""
        
        return self.alias_manager.normalize_brand_name(brand.strip())
    
    def brands_match(self, brand1: str, brand2: str) -> bool:
        """
        Check if two brand names match
        
        Args:
            brand1: First brand name
            brand2: Second brand name
            
        Returns:
            True if brands match
        """
        if not brand1 or not brand2:
            return False
        
        normalized1 = self.normalize_brand(brand1)
        normalized2 = self.normalize_brand(brand2)
        
        return normalized1.lower() == normalized2.lower()
    
    def calculate_brand_similarity(self, brand1: str, brand2: str) -> float:
        """
        Calculate similarity score between two brand names
        
        Args:
            brand1: First brand name
            brand2: Second brand name
            
        Returns:
            Similarity score between 0.0 and 1.0
        """
        if not brand1 or not brand2:
            return 0.0
        
        # Exact match after normalization
        if self.brands_match(brand1, brand2):
            return 1.0
        
        # Basic string similarity as fallback
        normalized1 = self.normalize_brand(brand1).lower()
        normalized2 = self.normalize_brand(brand2).lower()
        
        if normalized1 in normalized2 or normalized2 in normalized1:
            return 0.8
        
        # Calculate Jaccard similarity
        set1 = set(normalized1.split())
        set2 = set(normalized2.split())
        
        if not set1 or not set2:
            return 0.0
        
        intersection = len(set1.intersection(set2))
        union = len(set1.union(set2))
        
        return intersection / union if union > 0 else 0.0