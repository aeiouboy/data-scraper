"""Factory for generating test product matches."""

import random
from datetime import datetime, timedelta
from typing import Optional, List
from src.models.product import Product


class MatchFactory:
    """Generate test product matches."""
    
    MATCH_TYPES = ['automatic', 'manual', 'suggested', 'rejected']
    
    @classmethod
    def create(
        cls,
        product1: Product,
        product2: Product,
        confidence_score: Optional[float] = None,
        match_type: Optional[str] = None,
        **kwargs
    ) -> ProductMatch:
        """Create a single product match."""
        
        # Generate confidence score based on match type
        if confidence_score is None:
            if match_type == 'manual':
                confidence_score = 1.0  # Manual matches are 100% confident
            elif match_type == 'rejected':
                confidence_score = random.uniform(0.3, 0.6)  # Low confidence
            elif match_type == 'suggested':
                confidence_score = random.uniform(0.6, 0.8)  # Medium confidence
            else:  # automatic
                confidence_score = random.uniform(0.8, 0.95)  # High confidence
        
        match_type = match_type or random.choice(cls.MATCH_TYPES)
        
        # Generate match details
        match_details = cls._generate_match_details(product1, product2, confidence_score)
        
        match_data = {
            'product1_id': product1.id,
            'product2_id': product2.id,
            'confidence_score': confidence_score,
            'match_type': match_type,
            'match_details': match_details,
            'matched_at': datetime.utcnow() - timedelta(hours=random.randint(0, 168))
        }
        
        # Override with any provided kwargs
        match_data.update(kwargs)
        
        return ProductMatch(**match_data)
    
    @classmethod
    def create_match_group(
        cls,
        products: List[Product],
        base_product_index: int = 0
    ) -> List[ProductMatch]:
        """Create matches between a base product and other products."""
        
        matches = []
        base_product = products[base_product_index]
        
        for i, product in enumerate(products):
            if i == base_product_index:
                continue
            
            # Calculate similarity based on brand and category
            same_brand = base_product.brand.lower() == product.brand.lower()
            same_category = base_product.category == product.category
            
            if same_brand and same_category:
                confidence = random.uniform(0.8, 0.95)
                match_type = 'automatic'
            elif same_brand or same_category:
                confidence = random.uniform(0.5, 0.7)
                match_type = 'suggested'
            else:
                confidence = random.uniform(0.2, 0.4)
                match_type = 'rejected'
            
            match = cls.create(
                product1=base_product,
                product2=product,
                confidence_score=confidence,
                match_type=match_type
            )
            
            matches.append(match)
        
        return matches
    
    @classmethod
    def _generate_match_details(
        cls,
        product1: Product,
        product2: Product,
        confidence_score: float
    ) -> dict:
        """Generate detailed match information."""
        
        details = {
            'score_breakdown': {
                'name_similarity': random.uniform(0.7, 1.0) if confidence_score > 0.7 else random.uniform(0.3, 0.7),
                'brand_match': 1.0 if product1.brand.lower() == product2.brand.lower() else 0.0,
                'sku_similarity': random.uniform(0.5, 0.9),
                'price_similarity': 1.0 - abs(product1.current_price - product2.current_price) / max(product1.current_price, product2.current_price),
                'category_match': 1.0 if product1.category == product2.category else random.uniform(0.3, 0.7)
            },
            'matched_fields': []
        }
        
        # Determine which fields matched
        if details['score_breakdown']['brand_match'] == 1.0:
            details['matched_fields'].append('brand')
        
        if details['score_breakdown']['name_similarity'] > 0.8:
            details['matched_fields'].append('name')
        
        if details['score_breakdown']['category_match'] == 1.0:
            details['matched_fields'].append('category')
        
        if details['score_breakdown']['price_similarity'] > 0.9:
            details['matched_fields'].append('price')
        
        # Add any specification matches
        if product1.specifications and product2.specifications:
            spec_matches = []
            for key in product1.specifications:
                if key in product2.specifications:
                    if str(product1.specifications[key]).lower() == str(product2.specifications[key]).lower():
                        spec_matches.append(key)
            
            if spec_matches:
                details['matched_specifications'] = spec_matches
        
        return details