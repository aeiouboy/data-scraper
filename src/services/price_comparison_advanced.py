"""
Advanced Price Comparison Service with multilingual matching support
"""
import logging
from typing import Dict, List, Tuple, Optional, Any
from datetime import datetime
from decimal import Decimal
import asyncio
from concurrent.futures import ThreadPoolExecutor
import json

from src.utils.product_matcher_advanced import AdvancedProductMatcher, AdvancedMatchResult
from src.services.supabase_service import SupabaseService

logger = logging.getLogger(__name__)

class AdvancedPriceComparisonService:
    """Advanced price comparison with improved Thai-English matching"""
    
    def __init__(self, supabase_service: SupabaseService):
        self.supabase = supabase_service
        self.matcher = AdvancedProductMatcher()
        self.executor = ThreadPoolExecutor(max_workers=4)
        
        # Cache for performance
        self._category_cache = {}
        self._product_cache = {}
        self._match_cache = {}
        
    async def find_price_comparisons(
        self,
        product_id: Optional[str] = None,
        category_id: Optional[str] = None,
        search_query: Optional[str] = None,
        min_confidence: float = 0.70,
        max_results: int = 20,
        include_same_retailer: bool = False
    ) -> List[Dict[str, Any]]:
        """
        Find price comparisons with advanced matching
        
        Args:
            product_id: Specific product to compare
            category_id: Category to search within
            search_query: Search query for products
            min_confidence: Minimum match confidence (0-1)
            max_results: Maximum results to return
            include_same_retailer: Include products from same retailer
            
        Returns:
            List of price comparison results
        """
        try:
            # Get reference products
            if product_id:
                reference_products = await self._get_product_by_id(product_id)
                if not reference_products:
                    return []
                reference_products = [reference_products]
            else:
                reference_products = await self._search_products(
                    category_id=category_id,
                    search_query=search_query,
                    limit=10
                )
            
            if not reference_products:
                logger.warning("No reference products found")
                return []
            
            # Process each reference product
            all_comparisons = []
            
            for ref_product in reference_products:
                # Get candidates for comparison
                candidates = await self._get_comparison_candidates(
                    ref_product,
                    category_id,
                    include_same_retailer
                )
                
                if not candidates:
                    continue
                
                # Determine category hint for better matching
                category_hint = self._determine_category_hint(ref_product)
                
                # Find matches using advanced matcher
                matches = await self._find_matches_parallel(
                    ref_product,
                    candidates,
                    min_confidence,
                    category_hint
                )
                
                # Format comparison results
                comparisons = self._format_comparisons(
                    ref_product,
                    matches,
                    max_results
                )
                
                all_comparisons.extend(comparisons)
            
            # Sort by confidence and deduplicate
            all_comparisons = self._deduplicate_comparisons(all_comparisons)
            all_comparisons.sort(key=lambda x: x['match_confidence'], reverse=True)
            
            return all_comparisons[:max_results]
            
        except Exception as e:
            logger.error(f"Error in find_price_comparisons: {str(e)}")
            raise
    
    async def compare_specific_products(
        self,
        product_ids: List[str]
    ) -> Dict[str, Any]:
        """
        Compare specific products directly
        
        Args:
            product_ids: List of product IDs to compare
            
        Returns:
            Detailed comparison results
        """
        try:
            # Fetch all products
            products = await self._get_products_by_ids(product_ids)
            
            if len(products) < 2:
                return {
                    'error': 'Need at least 2 products to compare',
                    'products_found': len(products)
                }
            
            # Create comparison matrix
            comparison_matrix = {}
            
            for i, product1 in enumerate(products):
                for j, product2 in enumerate(products):
                    if i >= j:  # Skip self and duplicate comparisons
                        continue
                    
                    # Determine category hint
                    category_hint = self._determine_category_hint(product1)
                    
                    # Match products
                    match_result = self.matcher.match_products(
                        product1,
                        product2,
                        category_hint
                    )
                    
                    key = f"{product1['id']}_{product2['id']}"
                    comparison_matrix[key] = {
                        'product1': self._format_product_info(product1),
                        'product2': self._format_product_info(product2),
                        'match_result': {
                            'confidence': match_result.confidence,
                            'match_type': match_result.match_type,
                            'matched_fields': match_result.matched_fields,
                            'linguistic_scores': match_result.linguistic_scores,
                            'details': match_result.details,
                            'warnings': match_result.warnings
                        },
                        'price_analysis': self._analyze_prices(product1, product2)
                    }
            
            return {
                'products': [self._format_product_info(p) for p in products],
                'comparisons': comparison_matrix,
                'summary': self._generate_comparison_summary(comparison_matrix)
            }
            
        except Exception as e:
            logger.error(f"Error in compare_specific_products: {str(e)}")
            raise
    
    async def find_best_deals(
        self,
        category_id: Optional[str] = None,
        brand: Optional[str] = None,
        min_discount_percent: float = 10.0,
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """
        Find products with best deals compared to similar products
        
        Args:
            category_id: Category to search within
            brand: Specific brand to filter
            min_discount_percent: Minimum discount percentage
            limit: Maximum results
            
        Returns:
            List of deals with comparison data
        """
        try:
            # Get products in category/brand
            products = await self._search_products(
                category_id=category_id,
                brand=brand,
                limit=100
            )
            
            deals = []
            
            for product in products:
                # Skip if no price
                if not product.get('price'):
                    continue
                
                # Find similar products
                candidates = await self._get_comparison_candidates(
                    product,
                    category_id,
                    include_same_retailer=False
                )
                
                if not candidates:
                    continue
                
                # Match and analyze prices
                category_hint = self._determine_category_hint(product)
                matches = self.matcher.find_best_matches(
                    product,
                    candidates,
                    min_confidence=0.75,
                    max_results=5,
                    category_hint=category_hint
                )
                
                if not matches:
                    continue
                
                # Calculate average price of matches
                match_prices = [
                    float(m[0]['price']) 
                    for m in matches 
                    if m[0].get('price') and float(m[0]['price']) > 0
                ]
                
                if not match_prices:
                    continue
                
                avg_price = sum(match_prices) / len(match_prices)
                product_price = float(product['price'])
                
                # Calculate discount
                discount_percent = ((avg_price - product_price) / avg_price) * 100
                
                if discount_percent >= min_discount_percent:
                    deals.append({
                        'product': self._format_product_info(product),
                        'average_price': avg_price,
                        'discount_percent': round(discount_percent, 1),
                        'savings': round(avg_price - product_price, 2),
                        'compared_with': len(match_prices),
                        'similar_products': [
                            {
                                'product': self._format_product_info(m[0]),
                                'confidence': m[1].confidence,
                                'match_type': m[1].match_type
                            }
                            for m in matches[:3]
                        ]
                    })
            
            # Sort by discount percentage
            deals.sort(key=lambda x: x['discount_percent'], reverse=True)
            
            return deals[:limit]
            
        except Exception as e:
            logger.error(f"Error in find_best_deals: {str(e)}")
            raise
    
    async def analyze_price_trends(
        self,
        product_id: str,
        days: int = 30
    ) -> Dict[str, Any]:
        """
        Analyze price trends for a product and similar products
        
        Args:
            product_id: Product to analyze
            days: Number of days to analyze
            
        Returns:
            Price trend analysis
        """
        try:
            # Get product
            product = await self._get_product_by_id(product_id)
            if not product:
                return {'error': 'Product not found'}
            
            # Get price history (would need price_history table)
            # For now, return current analysis
            
            # Find similar products
            candidates = await self._get_comparison_candidates(
                product,
                product.get('category_id'),
                include_same_retailer=False
            )
            
            category_hint = self._determine_category_hint(product)
            matches = self.matcher.find_best_matches(
                product,
                candidates,
                min_confidence=0.75,
                max_results=10,
                category_hint=category_hint
            )
            
            # Analyze current market position
            market_analysis = self._analyze_market_position(product, matches)
            
            return {
                'product': self._format_product_info(product),
                'market_analysis': market_analysis,
                'similar_products': [
                    {
                        'product': self._format_product_info(m[0]),
                        'confidence': m[1].confidence,
                        'price_difference': self._calculate_price_difference(
                            product.get('price'),
                            m[0].get('price')
                        )
                    }
                    for m in matches[:5]
                ],
                'recommendation': self._generate_price_recommendation(
                    product,
                    market_analysis
                )
            }
            
        except Exception as e:
            logger.error(f"Error in analyze_price_trends: {str(e)}")
            raise
    
    async def _get_product_by_id(self, product_id: str) -> Optional[Dict[str, Any]]:
        """Get product by ID with caching"""
        if product_id in self._product_cache:
            return self._product_cache[product_id]
        
        result = await self.supabase.get_products(product_id=product_id)
        if result and result.get('data'):
            product = result['data'][0] if isinstance(result['data'], list) else result['data']
            self._product_cache[product_id] = product
            return product
        
        return None
    
    async def _get_products_by_ids(self, product_ids: List[str]) -> List[Dict[str, Any]]:
        """Get multiple products by IDs"""
        products = []
        
        for product_id in product_ids:
            product = await self._get_product_by_id(product_id)
            if product:
                products.append(product)
        
        return products
    
    async def _search_products(
        self,
        category_id: Optional[str] = None,
        search_query: Optional[str] = None,
        brand: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Search for products with filters"""
        params = {}
        
        if category_id:
            params['category_id'] = category_id
        if brand:
            params['brand'] = brand
        
        result = await self.supabase.get_products(**params)
        
        if result and result.get('data'):
            products = result['data']
            
            # Apply search query filter if provided
            if search_query:
                search_lower = search_query.lower()
                products = [
                    p for p in products
                    if search_lower in p.get('name', '').lower()
                    or search_lower in p.get('brand', '').lower()
                    or search_lower in p.get('sku', '').lower()
                ]
            
            return products[:limit]
        
        return []
    
    async def _get_comparison_candidates(
        self,
        reference_product: Dict[str, Any],
        category_id: Optional[str] = None,
        include_same_retailer: bool = False
    ) -> List[Dict[str, Any]]:
        """Get candidate products for comparison"""
        # Use category from reference product if not specified
        if not category_id and reference_product.get('category_id'):
            category_id = reference_product['category_id']
        
        # Get candidates
        candidates = await self._search_products(
            category_id=category_id,
            limit=200
        )
        
        # Filter out same retailer if needed
        if not include_same_retailer:
            ref_retailer = reference_product.get('retailer_code')
            candidates = [
                c for c in candidates
                if c.get('retailer_code') != ref_retailer
            ]
        
        # Filter out same product
        ref_id = reference_product.get('id')
        candidates = [c for c in candidates if c.get('id') != ref_id]
        
        return candidates
    
    async def _find_matches_parallel(
        self,
        reference_product: Dict[str, Any],
        candidates: List[Dict[str, Any]],
        min_confidence: float,
        category_hint: Optional[str]
    ) -> List[Tuple[Dict[str, Any], AdvancedMatchResult]]:
        """Find matches in parallel for performance"""
        loop = asyncio.get_event_loop()
        
        # Use cache key
        cache_key = f"{reference_product.get('id')}_{len(candidates)}_{min_confidence}"
        if cache_key in self._match_cache:
            return self._match_cache[cache_key]
        
        # Run matching in thread pool
        matches = await loop.run_in_executor(
            self.executor,
            self.matcher.find_best_matches,
            reference_product,
            candidates,
            min_confidence,
            50,  # Get more matches initially
            category_hint
        )
        
        # Cache results
        self._match_cache[cache_key] = matches
        
        return matches
    
    def _determine_category_hint(self, product: Dict[str, Any]) -> str:
        """Determine category hint for matching"""
        category = product.get('category', '').lower()
        name = product.get('name', '').lower()
        
        # Check for electronics
        electronics_keywords = [
            'air conditioner', 'แอร์', 'เครื่องปรับอากาศ',
            'refrigerator', 'ตู้เย็น', 'freezer', 'ตู้แช่',
            'television', 'tv', 'ทีวี', 'โทรทัศน์',
            'washing machine', 'เครื่องซักผ้า',
            'microwave', 'ไมโครเวฟ'
        ]
        
        if any(kw in category + name for kw in electronics_keywords):
            return 'electronics'
        
        # Check for appliances
        appliance_keywords = [
            'kitchen', 'ครัว', 'appliance', 'เครื่องใช้',
            'cooker', 'หม้อ', 'blender', 'ปั่น',
            'toaster', 'ปิ้ง', 'kettle', 'กาต้มน้ำ'
        ]
        
        if any(kw in category + name for kw in appliance_keywords):
            return 'appliances'
        
        return 'general'
    
    def _format_product_info(self, product: Dict[str, Any]) -> Dict[str, Any]:
        """Format product information for response"""
        return {
            'id': product.get('id'),
            'name': product.get('name'),
            'brand': product.get('brand'),
            'sku': product.get('sku'),
            'price': float(product.get('price', 0)),
            'retailer_code': product.get('retailer_code'),
            'category': product.get('category'),
            'url': product.get('url'),
            'image_url': product.get('image_url'),
            'in_stock': product.get('in_stock', True),
            'last_updated': product.get('updated_at')
        }
    
    def _format_comparisons(
        self,
        reference_product: Dict[str, Any],
        matches: List[Tuple[Dict[str, Any], AdvancedMatchResult]],
        max_results: int
    ) -> List[Dict[str, Any]]:
        """Format comparison results"""
        comparisons = []
        
        for match_product, match_result in matches[:max_results]:
            comparison = {
                'reference_product': self._format_product_info(reference_product),
                'matched_product': self._format_product_info(match_product),
                'match_confidence': round(match_result.confidence, 3),
                'match_type': match_result.match_type,
                'matched_fields': match_result.matched_fields,
                'price_comparison': self._analyze_prices(
                    reference_product,
                    match_product
                ),
                'match_details': {
                    'linguistic_scores': match_result.linguistic_scores,
                    'warnings': match_result.warnings,
                    'key_scores': {
                        'sku': match_result.details.get('sku_score', 0),
                        'brand': match_result.details.get('brand_score', 0),
                        'name': match_result.details.get('name_score', 0),
                        'specs': match_result.details.get('spec_score', 0)
                    }
                }
            }
            
            comparisons.append(comparison)
        
        return comparisons
    
    def _analyze_prices(
        self,
        product1: Dict[str, Any],
        product2: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Analyze price differences between products"""
        price1 = float(product1.get('price', 0))
        price2 = float(product2.get('price', 0))
        
        if price1 == 0 or price2 == 0:
            return {
                'comparable': False,
                'reason': 'Missing price data'
            }
        
        difference = price2 - price1
        percent_diff = (difference / price1) * 100
        
        return {
            'comparable': True,
            'price1': price1,
            'price2': price2,
            'difference': round(difference, 2),
            'percent_difference': round(percent_diff, 1),
            'cheaper_product': 'product1' if price1 < price2 else 'product2',
            'savings': abs(round(difference, 2))
        }
    
    def _deduplicate_comparisons(
        self,
        comparisons: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Remove duplicate comparisons"""
        seen = set()
        unique = []
        
        for comp in comparisons:
            # Create unique key
            ref_id = comp['reference_product']['id']
            match_id = comp['matched_product']['id']
            key = tuple(sorted([ref_id, match_id]))
            
            if key not in seen:
                seen.add(key)
                unique.append(comp)
        
        return unique
    
    def _calculate_price_difference(
        self,
        price1: Any,
        price2: Any
    ) -> Dict[str, Any]:
        """Calculate price difference safely"""
        try:
            p1 = float(price1) if price1 else 0
            p2 = float(price2) if price2 else 0
            
            if p1 == 0 or p2 == 0:
                return {'valid': False}
            
            diff = p2 - p1
            percent = (diff / p1) * 100
            
            return {
                'valid': True,
                'amount': round(diff, 2),
                'percent': round(percent, 1)
            }
        except:
            return {'valid': False}
    
    def _analyze_market_position(
        self,
        product: Dict[str, Any],
        matches: List[Tuple[Dict[str, Any], AdvancedMatchResult]]
    ) -> Dict[str, Any]:
        """Analyze product's position in market"""
        if not matches:
            return {
                'position': 'unknown',
                'comparable_products': 0
            }
        
        product_price = float(product.get('price', 0))
        if product_price == 0:
            return {
                'position': 'no_price',
                'comparable_products': 0
            }
        
        # Get prices from high-confidence matches
        match_prices = []
        for match_product, match_result in matches:
            if match_result.confidence >= 0.75 and match_product.get('price'):
                price = float(match_product['price'])
                if price > 0:
                    match_prices.append(price)
        
        if not match_prices:
            return {
                'position': 'unknown',
                'comparable_products': 0
            }
        
        # Calculate statistics
        avg_price = sum(match_prices) / len(match_prices)
        min_price = min(match_prices)
        max_price = max(match_prices)
        
        # Determine position
        position = 'average'
        if product_price < min_price:
            position = 'lowest'
        elif product_price > max_price:
            position = 'highest'
        elif product_price < avg_price * 0.9:
            position = 'below_average'
        elif product_price > avg_price * 1.1:
            position = 'above_average'
        
        percentile = sum(1 for p in match_prices if p < product_price) / len(match_prices) * 100
        
        return {
            'position': position,
            'comparable_products': len(match_prices),
            'average_market_price': round(avg_price, 2),
            'min_market_price': round(min_price, 2),
            'max_market_price': round(max_price, 2),
            'price_percentile': round(percentile, 1),
            'price_vs_average': round((product_price - avg_price) / avg_price * 100, 1)
        }
    
    def _generate_price_recommendation(
        self,
        product: Dict[str, Any],
        market_analysis: Dict[str, Any]
    ) -> Dict[str, str]:
        """Generate price recommendation based on analysis"""
        position = market_analysis.get('position', 'unknown')
        
        recommendations = {
            'lowest': {
                'summary': 'Excellent value - lowest price in market',
                'action': 'Buy now - this is the best available price'
            },
            'below_average': {
                'summary': 'Good value - below market average',
                'action': 'Good time to buy - price is competitive'
            },
            'average': {
                'summary': 'Fair pricing - at market average',
                'action': 'Standard market price - shop around for deals'
            },
            'above_average': {
                'summary': 'Premium pricing - above market average',
                'action': 'Consider alternatives - better prices available'
            },
            'highest': {
                'summary': 'Overpriced - highest in market',
                'action': 'Wait for discount or choose alternative'
            },
            'unknown': {
                'summary': 'Unable to determine market position',
                'action': 'Need more data for comparison'
            },
            'no_price': {
                'summary': 'No price information available',
                'action': 'Check retailer website for current pricing'
            }
        }
        
        return recommendations.get(position, recommendations['unknown'])
    
    def _generate_comparison_summary(
        self,
        comparison_matrix: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate summary of all comparisons"""
        if not comparison_matrix:
            return {'total_comparisons': 0}
        
        confidences = []
        match_types = {'exact': 0, 'high': 0, 'medium': 0, 'low': 0, 'none': 0}
        
        for comp_data in comparison_matrix.values():
            result = comp_data['match_result']
            confidences.append(result['confidence'])
            match_types[result['match_type']] += 1
        
        avg_confidence = sum(confidences) / len(confidences) if confidences else 0
        
        return {
            'total_comparisons': len(comparison_matrix),
            'average_confidence': round(avg_confidence, 3),
            'match_distribution': match_types,
            'high_confidence_matches': sum(
                1 for c in confidences if c >= 0.85
            ),
            'medium_confidence_matches': sum(
                1 for c in confidences if 0.70 <= c < 0.85
            ),
            'low_confidence_matches': sum(
                1 for c in confidences if c < 0.70
            )
        }