"""
Advanced product matching algorithm with ML-powered similarity and confidence scoring
"""
import re
import logging
from typing import List, Dict, Optional, Tuple, Any
from datetime import datetime
import numpy as np
from fuzzywuzzy import fuzz
from sentence_transformers import SentenceTransformer
import asyncio
from concurrent.futures import ThreadPoolExecutor

from src.models.matching_models import (
    MatchFeature,
    ConfidenceBreakdown,
    NormalizedSpecifications,
    CanonicalProduct,
    ProductMatchGroup,
    MatchMetadata,
    MatchedProduct,
    PriceAnalysis,
    PriceVolatilityLevel,
    SavingsOpportunity,
    MatchingAlgorithmConfig
)
from src.services.supabase_service import SupabaseService

logger = logging.getLogger(__name__)


class AdvancedProductMatcher:
    """Advanced product matching with multi-stage pipeline and ML"""
    
    def __init__(self, supabase_service: SupabaseService, config: Optional[MatchingAlgorithmConfig] = None):
        self.supabase = supabase_service
        self.config = config or MatchingAlgorithmConfig()
        self._ml_model = None
        self._executor = ThreadPoolExecutor(max_workers=4)
        
    @property
    def ml_model(self) -> SentenceTransformer:
        """Lazy load ML model"""
        if self._ml_model is None and self.config.use_ml_matching:
            self._ml_model = SentenceTransformer(self.config.ml_model_name)
        return self._ml_model
    
    async def match_products(self, products: List[Dict[str, Any]]) -> List[ProductMatchGroup]:
        """Match products across retailers using advanced algorithm"""
        start_time = datetime.now()
        
        # Group products by potential matches
        match_groups = await self._group_products(products)
        
        # Process each group
        results = []
        for group in match_groups:
            if len(group) > 1:
                match_group = await self._create_match_group(group)
                if match_group.confidence.overall >= 0.5:  # Default minimum confidence
                    results.append(match_group)
        
        processing_time = int((datetime.now() - start_time).total_seconds() * 1000)
        logger.info(f"Matched {len(products)} products into {len(results)} groups in {processing_time}ms")
        
        return results
    
    async def _group_products(self, products: List[Dict[str, Any]]) -> List[List[Dict[str, Any]]]:
        """Group products that might be matches"""
        groups = []
        processed = set()
        
        for i, product1 in enumerate(products):
            if i in processed:
                continue
                
            group = [product1]
            processed.add(i)
            
            for j, product2 in enumerate(products[i+1:], i+1):
                if j in processed:
                    continue
                    
                if await self._are_potential_matches(product1, product2):
                    group.append(product2)
                    processed.add(j)
            
            if len(group) > 1:
                groups.append(group)
        
        return groups
    
    async def _are_potential_matches(self, product1: Dict, product2: Dict) -> bool:
        """Quick check if products could be matches"""
        # Same retailer products can't match
        if product1.get('retailer_code') == product2.get('retailer_code'):
            return False
        
        # Category check
        if self.config.require_same_category:
            cat1 = self._normalize_category(product1.get('category', ''))
            cat2 = self._normalize_category(product2.get('category', ''))
            if cat1 != cat2:
                return False
        
        # Brand check
        brand1 = self._normalize_brand(product1.get('brand', ''))
        brand2 = self._normalize_brand(product2.get('brand', ''))
        if brand1 and brand2 and brand1 != brand2:
            return False
        
        # Price range check
        price1 = float(product1.get('current_price') or 0)
        price2 = float(product2.get('current_price') or 0)
        if price1 > 0 and price2 > 0:
            price_ratio = max(price1, price2) / min(price1, price2)
            if price_ratio > (1 + self.config.price_variance_threshold):
                return False
        
        return True
    
    async def _create_match_group(self, products: List[Dict[str, Any]]) -> ProductMatchGroup:
        """Create a match group with confidence scoring"""
        # Calculate canonical product
        canonical = await self._determine_canonical_product(products)
        
        # Calculate match confidence
        confidence, features = await self._calculate_confidence(products, canonical)
        
        # Create matched products
        matched_products = [
            MatchedProduct(
                product_id=p['id'],
                retailer_code=p['retailer_code'],
                retailer_name=p.get('retailer_name', p['retailer_code']),
                product_name=p['name'],
                current_price=float(p.get('current_price') or 0),
                url=p.get('url', ''),
                availability=p.get('in_stock', True) and 'in_stock' or 'out_of_stock',
                last_updated=datetime.now()
            )
            for p in products
        ]
        
        # Analyze prices
        price_analysis = await self._analyze_prices(matched_products)
        
        # Create metadata
        metadata = MatchMetadata(
            algorithm_version="2.0",
            match_features=features,
            processing_time_ms=0,  # Would be calculated in real implementation
            data_sources=['supabase'],
            created_at=datetime.now()
        )
        
        return ProductMatchGroup(
            id=f"mg_{datetime.now().timestamp()}",
            canonical_product=canonical,
            matched_products=matched_products,
            confidence=confidence,
            match_metadata=metadata,
            price_analysis=price_analysis,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
    
    async def _determine_canonical_product(self, products: List[Dict[str, Any]]) -> CanonicalProduct:
        """Determine canonical representation from product group"""
        # Extract common features
        brands = [self._normalize_brand(p.get('brand', '')) for p in products if p.get('brand')]
        categories = [p.get('category', '') for p in products if p.get('category')]
        
        # Use most common or longest name
        names = [p['name'] for p in products]
        canonical_name = max(names, key=len)
        
        # Extract key features using NLP
        key_features = await self._extract_key_features(names)
        
        # Normalize specifications
        specs = await self._normalize_specifications(products)
        
        return CanonicalProduct(
            normalized_name=self._normalize_product_name(canonical_name),
            brand=brands[0] if brands else "Unknown",
            category=categories[0] if categories else "Unknown",
            product_type=self._determine_product_type(canonical_name, categories[0] if categories else ""),
            key_features=key_features,
            specifications=specs
        )
    
    async def _calculate_confidence(self, products: List[Dict[str, Any]], canonical: CanonicalProduct) -> Tuple[ConfidenceBreakdown, List[MatchFeature]]:
        """Calculate match confidence with detailed breakdown"""
        features = []
        
        # Name matching
        name_scores = []
        if self.config.use_ml_matching and self.ml_model:
            # ML-based semantic similarity
            embeddings = await self._get_embeddings([p['name'] for p in products])
            name_scores = self._calculate_embedding_similarities(embeddings)
        else:
            # Fuzzy string matching
            for i in range(len(products)):
                for j in range(i+1, len(products)):
                    score = fuzz.token_sort_ratio(
                        self._normalize_product_name(products[i]['name']),
                        self._normalize_product_name(products[j]['name'])
                    ) / 100.0
                    name_scores.append(score)
        
        avg_name_score = np.mean(name_scores) if name_scores else 0
        features.append(MatchFeature(
            name="name_similarity",
            value=avg_name_score,
            weight=0.3,
            matched=avg_name_score >= self.config.min_name_similarity,
            similarity_score=avg_name_score
        ))
        
        # Brand matching
        brands = [self._normalize_brand(p.get('brand', '')) for p in products if p.get('brand')]
        brand_score = 1.0 if len(set(brands)) == 1 and brands else 0.0
        features.append(MatchFeature(
            name="brand_match",
            value=brand_score,
            weight=0.25,
            matched=brand_score >= self.config.min_brand_similarity,
            similarity_score=brand_score
        ))
        
        # Specification matching
        spec_score = await self._calculate_spec_similarity(products)
        features.append(MatchFeature(
            name="specification_match",
            value=spec_score,
            weight=0.25,
            matched=spec_score >= 0.7,
            similarity_score=spec_score
        ))
        
        # Price consistency
        prices = [float(p.get('current_price') or 0) for p in products if p.get('current_price') and p.get('current_price') != 0]
        price_score = self._calculate_price_consistency(prices)
        features.append(MatchFeature(
            name="price_consistency",
            value=price_score,
            weight=0.15,
            matched=price_score >= 0.5,
            similarity_score=price_score
        ))
        
        # Calculate overall confidence
        confidence = ConfidenceBreakdown(
            name_match=avg_name_score,
            brand_match=brand_score,
            spec_match=spec_score,
            price_consistency=price_score,
            user_validation=0.0  # Would come from user feedback
        )
        
        return confidence, features
    
    async def _get_embeddings(self, texts: List[str]) -> np.ndarray:
        """Get sentence embeddings using ML model"""
        loop = asyncio.get_event_loop()
        embeddings = await loop.run_in_executor(
            self._executor,
            self.ml_model.encode,
            texts
        )
        return embeddings
    
    def _calculate_embedding_similarities(self, embeddings: np.ndarray) -> List[float]:
        """Calculate cosine similarities between embeddings"""
        from sklearn.metrics.pairwise import cosine_similarity
        
        similarities = []
        for i in range(len(embeddings)):
            for j in range(i+1, len(embeddings)):
                sim = cosine_similarity(
                    embeddings[i].reshape(1, -1),
                    embeddings[j].reshape(1, -1)
                )[0][0]
                similarities.append(sim)
        
        return similarities
    
    def _calculate_price_consistency(self, prices: List[float]) -> float:
        """Calculate price consistency score"""
        if not prices or len(prices) < 2:
            return 1.0
        
        # Calculate coefficient of variation
        mean_price = np.mean(prices)
        std_price = np.std(prices)
        
        if mean_price == 0:
            return 0.0
        
        cv = std_price / mean_price
        
        # Convert to score (lower CV = higher score)
        if cv <= 0.05:
            return 1.0
        elif cv <= 0.1:
            return 0.9
        elif cv <= 0.2:
            return 0.7
        elif cv <= 0.3:
            return 0.5
        elif cv <= 0.5:
            return 0.3
        else:
            return 0.1
    
    async def _calculate_spec_similarity(self, products: List[Dict[str, Any]]) -> float:
        """Calculate specification similarity between products"""
        # Extract specifications from product descriptions
        all_specs = []
        for product in products:
            specs = self._extract_specifications(product.get('description', ''))
            if product.get('specifications'):
                specs.update(product['specifications'])
            all_specs.append(specs)
        
        if not all_specs:
            return 0.5  # No specs to compare
        
        # Calculate Jaccard similarity
        similarities = []
        for i in range(len(all_specs)):
            for j in range(i+1, len(all_specs)):
                spec_keys1 = set(all_specs[i].keys())
                spec_keys2 = set(all_specs[j].keys())
                
                if not spec_keys1 or not spec_keys2:
                    continue
                
                intersection = spec_keys1 & spec_keys2
                union = spec_keys1 | spec_keys2
                
                jaccard = len(intersection) / len(union) if union else 0
                similarities.append(jaccard)
        
        return np.mean(similarities) if similarities else 0.5
    
    def _extract_specifications(self, text: str) -> Dict[str, str]:
        """Extract specifications from product description"""
        specs = {}
        
        # Handle None or empty text
        if not text:
            return specs
        
        # Convert to string if not already
        text = str(text)
        
        # Common specification patterns
        patterns = [
            r'(\w+):\s*([^,\n]+)',  # key: value
            r'(\w+)\s*=\s*([^,\n]+)',  # key = value
            r'(\w+)\s+(\d+\s*\w+)',  # key value with units
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for key, value in matches:
                specs[key.lower()] = value.strip()
        
        return specs
    
    async def _analyze_prices(self, products: List[MatchedProduct]) -> PriceAnalysis:
        """Analyze prices across matched products"""
        prices = [(p.retailer_code, p.current_price) for p in products if p.current_price > 0]
        
        if not prices:
            return PriceAnalysis(
                current_best_price=0,
                current_best_retailer="Unknown",
                volatility=PriceVolatilityLevel.STABLE,
                volatility_score=0,
                last_updated=datetime.now()
            )
        
        # Find best price
        best_retailer, best_price = min(prices, key=lambda x: x[1])
        
        # Calculate volatility
        price_values = [p[1] for p in prices]
        volatility_score = np.std(price_values) / np.mean(price_values) if len(price_values) > 1 else 0
        
        # Determine volatility level
        if volatility_score < 0.05:
            volatility_level = PriceVolatilityLevel.STABLE
        elif volatility_score < 0.1:
            volatility_level = PriceVolatilityLevel.LOW
        elif volatility_score < 0.2:
            volatility_level = PriceVolatilityLevel.MODERATE
        elif volatility_score < 0.4:
            volatility_level = PriceVolatilityLevel.HIGH
        else:
            volatility_level = PriceVolatilityLevel.EXTREME
        
        # Calculate savings opportunity
        savings_opportunity = None
        if len(prices) > 1:
            max_price = max(price_values)
            if max_price > best_price:
                savings_opportunity = SavingsOpportunity(
                    amount=max_price - best_price,
                    percentage=((max_price - best_price) / max_price) * 100,
                    best_retailer=best_retailer,
                    compared_to_retailers=[r for r, _ in prices if r != best_retailer],
                    confidence=0.9  # High confidence in direct price comparison
                )
        
        return PriceAnalysis(
            current_best_price=best_price,
            current_best_retailer=best_retailer,
            savings_opportunity=savings_opportunity,
            volatility=volatility_level,
            volatility_score=volatility_score,
            last_updated=datetime.now()
        )
    
    async def _extract_key_features(self, names: List[str]) -> List[str]:
        """Extract key features from product names"""
        # Common feature patterns
        feature_patterns = [
            r'\b\d+(?:\.\d+)?\s*(?:GB|TB|MB|L|ml|kg|g|W|inch|")\b',  # Capacity/size
            r'\b(?:HD|FHD|4K|8K|OLED|LED|LCD)\b',  # Display tech
            r'\b(?:WiFi|Bluetooth|USB|HDMI)\b',  # Connectivity
            r'\b(?:Energy Star|Inverter|Smart)\b',  # Features
        ]
        
        features = set()
        for name in names:
            for pattern in feature_patterns:
                matches = re.findall(pattern, name, re.IGNORECASE)
                features.update(matches)
        
        return list(features)
    
    async def _normalize_specifications(self, products: List[Dict[str, Any]]) -> Optional[NormalizedSpecifications]:
        """Normalize specifications across products"""
        # This would be more sophisticated in production
        # For now, return None
        return None
    
    def _normalize_product_name(self, name: str) -> str:
        """Normalize product name for comparison"""
        # Remove special characters and extra spaces
        name = re.sub(r'[^\w\s-]', ' ', name)
        name = re.sub(r'\s+', ' ', name)
        return name.strip().lower()
    
    def _normalize_brand(self, brand: str) -> str:
        """Normalize brand name"""
        if not brand:
            return ""
        
        # Common brand aliases
        brand_aliases = {
            'lg': ['lg electronics', 'lg electric'],
            'samsung': ['samsung electronics'],
            'sony': ['sony corporation'],
            'panasonic': ['panasonic corporation'],
        }
        
        normalized = brand.strip().lower()
        
        # Check aliases
        for canonical, aliases in brand_aliases.items():
            if normalized in aliases:
                return canonical
        
        return normalized
    
    def _normalize_category(self, category: str) -> str:
        """Normalize category name"""
        if not category:
            return ""
        
        # Remove retailer-specific prefixes
        category = re.sub(r'^[A-Z]+\d+\s*-\s*', '', category)
        
        return category.strip().lower()
    
    def _determine_product_type(self, name: str, category: str) -> str:
        """Determine product type from name and category"""
        name_lower = name.lower()
        
        # Common product type patterns
        if 'refrigerator' in name_lower or 'fridge' in name_lower:
            return 'refrigerator'
        elif 'tv' in name_lower or 'television' in name_lower:
            return 'television'
        elif 'air condition' in name_lower or 'แอร์' in name_lower:
            return 'air_conditioner'
        elif 'wash' in name_lower and 'machine' in name_lower:
            return 'washing_machine'
        else:
            return category.split()[0] if category else 'unknown'