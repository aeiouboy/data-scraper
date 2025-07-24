"""Mock product matcher for testing."""

from typing import List, Dict, Any
from src.models.product import Product


class ProductMatcher:
    """Mock product matcher."""
    
    def calculate_match_score(self, product1: Product, product2: Product) -> float:
        """Calculate match score between two products."""
        if product1.sku == product2.sku:
            return 1.0
        if product1.brand == product2.brand and product1.name == product2.name:
            return 0.95
        if product1.brand == product2.brand:
            return 0.7
        return 0.3
    
    def find_matches(self, product: Product, products: List[Product], threshold: float = 0.7) -> List[Dict[str, Any]]:
        """Find matches for a product."""
        matches = []
        for p in products:
            if p.id != product.id:
                score = self.calculate_match_score(product, p)
                if score >= threshold:
                    matches.append({"product": p, "score": score})
        return sorted(matches, key=lambda x: x["score"], reverse=True)
    
    def match_by_sku(self, product1: Product, product2: Product) -> float:
        """Match products by SKU."""
        if product1.sku == product2.sku:
            return 1.0
        # Simple similarity check
        return 0.5 if product1.sku and product2.sku and product1.sku[:3] == product2.sku[:3] else 0.0
    
    def match_by_name(self, product1: Product, product2: Product) -> float:
        """Match products by name."""
        if product1.name == product2.name:
            return 1.0
        # Simple similarity
        return 0.5
    
    def match_by_specifications(self, product1: Product, product2: Product) -> float:
        """Match products by specifications."""
        return 0.5
    
    def match_by_price(self, product1: Product, product2: Product) -> float:
        """Match products by price."""
        if not product1.current_price or not product2.current_price:
            return 0.5
        diff = abs(product1.current_price - product2.current_price) / max(product1.current_price, product2.current_price)
        return max(0, 1 - diff)
    
    def group_matches(self, products: List[Product], threshold: float = 0.7) -> List[List[Product]]:
        """Group products by matches."""
        groups = []
        processed = set()
        
        for product in products:
            if product.id in processed:
                continue
            
            group = [product]
            processed.add(product.id)
            
            for other in products:
                if other.id not in processed:
                    if self.calculate_match_score(product, other) >= threshold:
                        group.append(other)
                        processed.add(other.id)
            
            groups.append(group)
        
        return groups
    
    def match_by_brand(self, product1: Product, product2: Product) -> float:
        """Match products by brand."""
        if not product1.brand or not product2.brand:
            return 0.0
        return 1.0 if product1.brand.lower() == product2.brand.lower() else 0.0
