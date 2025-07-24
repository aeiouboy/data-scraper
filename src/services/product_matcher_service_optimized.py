"""
Optimized Product Matcher Service
Integrates the optimized matcher with the existing API infrastructure
"""
import logging
import asyncio
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import asdict
import time
from concurrent.futures import ThreadPoolExecutor
import json

from src.utils.product_matcher_optimized import OptimizedProductMatcher, OptimizedMatchResult
from src.services.supabase_service import SupabaseService

logger = logging.getLogger(__name__)

class OptimizedProductMatcherService:
    """Service layer for optimized product matching"""
    
    def __init__(self):
        self.matcher = OptimizedProductMatcher()
        self.supabase = SupabaseService()
        
        # Configuration for matching service
        self.config = {
            'batch_size': 100,           # Products to process in one batch
            'max_workers': 4,            # Thread pool size
            'confidence_thresholds': {
                'auto_accept': 0.85,     # Automatically accept matches above this
                'manual_review': 0.45,   # Require manual review between this and auto_accept
                'auto_reject': 0.25      # Automatically reject below this
            },
            'max_matches_per_product': 10,
            'cache_duration': 3600,      # Cache results for 1 hour
            'progressive_matching': True  # Use progressive matching algorithm
        }
        
        # Cache for recent matching results
        self._match_cache = {}
        
    async def match_products_batch(
        self,
        products: List[Dict[str, Any]],
        candidates: List[Dict[str, Any]],
        category_hint: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Match a batch of products against candidates using optimized algorithms
        
        Args:
            products: List of products to find matches for
            candidates: List of candidate products to match against
            category_hint: Optional category hint for better matching
            
        Returns:
            Dictionary with matching results and statistics
        """
        start_time = time.time()
        logger.info(f"Starting batch matching for {len(products)} products against {len(candidates)} candidates")
        
        results = {
            'total_products': len(products),
            'total_candidates': len(candidates),
            'matches': [],
            'statistics': {
                'matches_found': 0,
                'high_confidence': 0,
                'medium_confidence': 0,
                'low_confidence': 0,
                'auto_accepted': 0,
                'manual_review': 0,
                'auto_rejected': 0,
                'processing_time': 0,
                'average_confidence': 0
            },
            'performance_metrics': {
                'products_per_second': 0,
                'matches_per_second': 0,
                'cache_hits': 0,
                'cache_misses': 0
            }
        }
        
        # Process products in batches with thread pool
        with ThreadPoolExecutor(max_workers=self.config['max_workers']) as executor:
            # Create chunks for batch processing
            product_chunks = [
                products[i:i + self.config['batch_size']]
                for i in range(0, len(products), self.config['batch_size'])
            ]
            
            # Process each chunk
            all_matches = []
            cache_hits = 0
            cache_misses = 0
            
            for chunk_idx, product_chunk in enumerate(product_chunks):
                logger.info(f"Processing batch {chunk_idx + 1}/{len(product_chunks)}")
                
                # Submit matching tasks to thread pool
                future_to_product = {
                    executor.submit(
                        self._match_single_product_optimized,
                        product,
                        candidates,
                        category_hint
                    ): product
                    for product in product_chunk
                }
                
                # Collect results
                for future in future_to_product:
                    try:
                        product = future_to_product[future]
                        match_result = future.result(timeout=30)  # 30 second timeout per product
                        
                        if match_result['cache_hit']:
                            cache_hits += 1
                        else:
                            cache_misses += 1
                        
                        if match_result['matches']:
                            all_matches.append({
                                'product_id': product.get('id'),
                                'product_name': product.get('name'),
                                'matches': match_result['matches'],
                                'best_match': match_result['best_match'],
                                'match_summary': match_result['summary']
                            })
                        
                    except Exception as e:
                        logger.error(f"Error matching product {product.get('id', 'unknown')}: {str(e)}")
                        continue
        
        # Process and categorize all matches
        total_confidence = 0
        match_count = 0
        
        for product_matches in all_matches:
            for match in product_matches['matches']:
                confidence = match['confidence']
                total_confidence += confidence
                match_count += 1
                
                # Categorize by confidence
                if confidence >= 0.8:
                    results['statistics']['high_confidence'] += 1
                elif confidence >= 0.5:
                    results['statistics']['medium_confidence'] += 1
                else:
                    results['statistics']['low_confidence'] += 1
                
                # Categorize by action needed
                if confidence >= self.config['confidence_thresholds']['auto_accept']:
                    results['statistics']['auto_accepted'] += 1
                elif confidence >= self.config['confidence_thresholds']['manual_review']:
                    results['statistics']['manual_review'] += 1
                else:
                    results['statistics']['auto_rejected'] += 1
        
        # Calculate final statistics
        processing_time = time.time() - start_time
        results['matches'] = all_matches
        results['statistics']['matches_found'] = match_count
        results['statistics']['processing_time'] = processing_time
        results['statistics']['average_confidence'] = total_confidence / match_count if match_count > 0 else 0
        
        # Performance metrics
        results['performance_metrics']['products_per_second'] = len(products) / processing_time if processing_time > 0 else 0
        results['performance_metrics']['matches_per_second'] = match_count / processing_time if processing_time > 0 else 0
        results['performance_metrics']['cache_hits'] = cache_hits
        results['performance_metrics']['cache_misses'] = cache_misses
        
        logger.info(f"Batch matching completed in {processing_time:.2f}s. Found {match_count} matches for {len(all_matches)} products")
        
        return results
    
    def _match_single_product_optimized(
        self,
        product: Dict[str, Any],
        candidates: List[Dict[str, Any]],
        category_hint: Optional[str] = None
    ) -> Dict[str, Any]:
        """Match a single product against candidates using optimized matcher"""
        
        product_id = product.get('id', 'unknown')
        cache_key = self._generate_cache_key(product, candidates, category_hint)
        
        # Check cache first
        if cache_key in self._match_cache:
            cache_result = self._match_cache[cache_key]
            if time.time() - cache_result['timestamp'] < self.config['cache_duration']:
                return {
                    'matches': cache_result['matches'],
                    'best_match': cache_result['best_match'],
                    'summary': cache_result['summary'],
                    'cache_hit': True
                }
        
        # Perform matching
        matches = self.matcher.find_best_matches_optimized(
            product,
            candidates,
            min_confidence=self.config['confidence_thresholds']['auto_reject'],
            max_results=self.config['max_matches_per_product'],
            category_hint=category_hint
        )
        
        # Process results
        processed_matches = []
        best_match = None
        best_confidence = 0
        
        for candidate, match_result in matches:
            match_data = {
                'candidate_id': candidate.get('id'),
                'candidate_name': candidate.get('name'),
                'candidate_brand': candidate.get('brand'),
                'candidate_retailer': candidate.get('retailer_code'),
                'candidate_price': candidate.get('price'),
                'confidence': match_result.confidence,
                'match_type': match_result.match_type,
                'matched_fields': match_result.matched_fields,
                'warnings': match_result.warnings,
                'details': {
                    'sku_score': match_result.details.get('sku_score', 0),
                    'brand_score': match_result.details.get('brand_score', 0),
                    'name_score': match_result.details.get('name_score', 0),
                    'spec_score': match_result.details.get('spec_score', 0),
                    'category_score': match_result.details.get('category_score', 0),
                    'tier': match_result.details.get('tier', 'unknown')
                },
                'progressive_scores': match_result.progressive_scores,
                'linguistic_scores': match_result.linguistic_scores,
                'action_required': self._determine_action_required(match_result.confidence)
            }
            
            processed_matches.append(match_data)
            
            if match_result.confidence > best_confidence:
                best_confidence = match_result.confidence
                best_match = match_data
        
        # Create summary
        summary = {
            'total_matches': len(processed_matches),
            'best_confidence': best_confidence,
            'confidence_distribution': {
                'high': len([m for m in processed_matches if m['confidence'] >= 0.8]),
                'medium': len([m for m in processed_matches if 0.5 <= m['confidence'] < 0.8]),
                'low': len([m for m in processed_matches if m['confidence'] < 0.5])
            },
            'match_quality': 'excellent' if best_confidence >= 0.9 else 'good' if best_confidence >= 0.7 else 'fair' if best_confidence >= 0.5 else 'poor',
            'recommendation': self._get_matching_recommendation(processed_matches)
        }
        
        # Cache results
        cache_result = {
            'matches': processed_matches,
            'best_match': best_match,
            'summary': summary,
            'timestamp': time.time()
        }
        self._match_cache[cache_key] = cache_result
        
        return {
            'matches': processed_matches,
            'best_match': best_match,
            'summary': summary,
            'cache_hit': False
        }
    
    def _determine_action_required(self, confidence: float) -> str:
        """Determine what action is required based on confidence"""
        if confidence >= self.config['confidence_thresholds']['auto_accept']:
            return 'auto_accept'
        elif confidence >= self.config['confidence_thresholds']['manual_review']:
            return 'manual_review'
        else:
            return 'auto_reject'
    
    def _get_matching_recommendation(self, matches: List[Dict[str, Any]]) -> str:
        """Get recommendation based on matching results"""
        if not matches:
            return "No matches found. Consider relaxing matching criteria or checking product data quality."
        
        best_match = max(matches, key=lambda x: x['confidence'])
        auto_accept_count = len([m for m in matches if m['action_required'] == 'auto_accept'])
        manual_review_count = len([m for m in matches if m['action_required'] == 'manual_review'])
        
        if auto_accept_count > 0:
            return f"Found {auto_accept_count} high-confidence match(es). Ready for automatic processing."
        elif manual_review_count > 0:
            return f"Found {manual_review_count} potential match(es) requiring manual review. Best confidence: {best_match['confidence']:.3f}"
        else:
            return f"Found {len(matches)} low-confidence match(es). Consider improving product data or relaxing thresholds."
    
    def _generate_cache_key(
        self,
        product: Dict[str, Any],
        candidates: List[Dict[str, Any]],
        category_hint: Optional[str]
    ) -> str:
        """Generate cache key for matching results"""
        # Create a stable hash of the input parameters
        import hashlib
        
        product_key = f"{product.get('id', '')}-{product.get('name', '')}-{product.get('sku', '')}"
        candidates_key = '-'.join(sorted([c.get('id', '') for c in candidates[:10]]))  # Limit to first 10 for performance
        category_key = category_hint or 'none'
        
        combined_key = f"{product_key}-{candidates_key}-{category_key}"
        return hashlib.md5(combined_key.encode()).hexdigest()
    
    async def get_matching_suggestions(
        self,
        product_id: str,
        limit: int = 10,
        min_confidence: float = 0.3
    ) -> Dict[str, Any]:
        """Get matching suggestions for a specific product"""
        
        try:
            # Get product from database
            product_data = await self.supabase.get_product_by_id(product_id)
            if not product_data:
                return {'error': f'Product {product_id} not found'}
            
            # Get potential candidates (exclude same retailer)
            candidates = await self.supabase.get_products_for_matching(
                exclude_retailer=product_data.get('retailer_code'),
                category=product_data.get('category'),
                limit=1000  # Large pool for better matching
            )
            
            if not candidates:
                return {'error': 'No candidates found for matching'}
            
            # Perform matching
            result = self._match_single_product_optimized(
                product_data,
                candidates,
                category_hint=product_data.get('category')
            )
            
            # Filter by minimum confidence
            filtered_matches = [
                match for match in result['matches']
                if match['confidence'] >= min_confidence
            ][:limit]
            
            return {
                'product': {
                    'id': product_data.get('id'),
                    'name': product_data.get('name'),
                    'brand': product_data.get('brand'),
                    'retailer': product_data.get('retailer_code')
                },
                'suggestions': filtered_matches,
                'summary': result['summary'],
                'metadata': {
                    'total_candidates': len(candidates),
                    'total_matches': len(result['matches']),
                    'filtered_matches': len(filtered_matches),
                    'min_confidence': min_confidence,
                    'cache_hit': result['cache_hit']
                }
            }
            
        except Exception as e:
            logger.error(f"Error getting matching suggestions for product {product_id}: {str(e)}")
            return {'error': str(e)}
    
    async def create_price_comparison(
        self,
        product_ids: List[str],
        confidence_threshold: float = 0.6
    ) -> Dict[str, Any]:
        """Create price comparison from matched products"""
        
        try:
            # Get products
            products = []
            for product_id in product_ids:
                product_data = await self.supabase.get_product_by_id(product_id)
                if product_data:
                    products.append(product_data)
            
            if len(products) < 2:
                return {'error': 'Need at least 2 products for comparison'}
            
            # Verify products are actually matches
            primary_product = products[0]
            comparison_results = []
            
            for other_product in products[1:]:
                if self.config['progressive_matching']:
                    match_result = self.matcher.match_products_progressive(primary_product, other_product)
                else:
                    match_result = self.matcher.match_products(primary_product, other_product)
                
                if match_result.confidence >= confidence_threshold:
                    comparison_results.append({
                        'product': other_product,
                        'match_confidence': match_result.confidence,
                        'match_details': match_result.details
                    })
            
            if not comparison_results:
                return {'error': f'No products meet confidence threshold of {confidence_threshold}'}
            
            # Create price comparison
            price_comparison = {
                'primary_product': primary_product,
                'matched_products': comparison_results,
                'price_analysis': self._analyze_prices([primary_product] + [r['product'] for r in comparison_results]),
                'confidence_threshold_used': confidence_threshold,
                'created_at': time.time()
            }
            
            # Save to database
            comparison_id = await self.supabase.create_price_comparison_v2(price_comparison)
            price_comparison['id'] = comparison_id
            
            return price_comparison
            
        except Exception as e:
            logger.error(f"Error creating price comparison: {str(e)}")
            return {'error': str(e)}
    
    def _analyze_prices(self, products: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze prices across matched products"""
        
        prices = []
        retailer_prices = {}
        
        for product in products:
            price = product.get('price')
            retailer = product.get('retailer_code', 'unknown')
            
            if price and price > 0:
                prices.append(float(price))
                retailer_prices[retailer] = {
                    'price': float(price),
                    'product_name': product.get('name', ''),
                    'product_id': product.get('id', '')
                }
        
        if not prices:
            return {'error': 'No valid prices found'}
        
        min_price = min(prices)
        max_price = max(prices)
        avg_price = sum(prices) / len(prices)
        price_variance = (max_price - min_price) / avg_price if avg_price > 0 else 0
        
        # Find best and worst deals
        best_deal = min(retailer_prices.items(), key=lambda x: x[1]['price'])
        worst_deal = max(retailer_prices.items(), key=lambda x: x[1]['price'])
        
        savings = worst_deal[1]['price'] - best_deal[1]['price']
        savings_percentage = (savings / worst_deal[1]['price']) * 100 if worst_deal[1]['price'] > 0 else 0
        
        return {
            'price_range': {
                'min': min_price,
                'max': max_price,
                'average': avg_price,
                'variance': price_variance
            },
            'best_deal': {
                'retailer': best_deal[0],
                'price': best_deal[1]['price'],
                'product_name': best_deal[1]['product_name'],
                'savings': savings,
                'savings_percentage': savings_percentage
            },
            'worst_deal': {
                'retailer': worst_deal[0],
                'price': worst_deal[1]['price'],
                'product_name': worst_deal[1]['product_name']
            },
            'retailer_comparison': retailer_prices,
            'total_products': len(products),
            'analysis_date': time.time()
        }
    
    def get_service_statistics(self) -> Dict[str, Any]:
        """Get service performance statistics"""
        return {
            'cache_size': len(self._match_cache),
            'configuration': self.config,
            'matcher_info': {
                'type': 'OptimizedProductMatcher',
                'thresholds': self.matcher.thresholds,
                'progressive_tiers': list(self.matcher.progressive_tiers.keys()),
                'enhanced_brands': len(self.matcher.enhanced_brand_mapping)
            }
        }
    
    def clear_cache(self) -> None:
        """Clear the matching cache"""
        self._match_cache.clear()
        logger.info("Matching cache cleared")
    
    def update_configuration(self, new_config: Dict[str, Any]) -> None:
        """Update service configuration"""
        self.config.update(new_config)
        logger.info(f"Configuration updated: {new_config}")

# Example usage and testing
async def test_optimized_service():
    """Test function for the optimized service"""
    service = OptimizedProductMatcherService()
    
    # Example test data
    test_products = [
        {
            'id': '1',
            'name': 'Mitsubishi Electric MSY-JP13VF Inverter 12000 BTU',
            'brand': 'Mitsubishi Electric',
            'sku': 'MSY-JP13VF',
            'category': 'air conditioner',
            'price': 18900,
            'retailer_code': 'HP'
        }
    ]
    
    test_candidates = [
        {
            'id': '2',
            'name': 'มิตซูบิชิ อิเล็กทริก แอร์ 12000 บีทียู อินเวอร์เตอร์ รุ่น MSY-JP13VF',
            'brand': 'มิตซูบิชิ',
            'sku': 'MSY-JP13VF',
            'category': 'เครื่องปรับอากาศ',
            'price': 19200,
            'retailer_code': 'TWD'
        },
        {
            'id': '3',
            'name': 'LG Dual Cool Inverter 18000 BTU WiFi Smart AC',
            'brand': 'LG',
            'sku': 'AC18DL-B1',
            'category': 'air conditioner',
            'price': 29500,
            'retailer_code': 'GH'
        }
    ]
    
    # Test batch matching
    results = await service.match_products_batch(test_products, test_candidates)
    print(f"Batch matching results: {json.dumps(results, indent=2, default=str)}")
    
    # Test service statistics
    stats = service.get_service_statistics()
    print(f"Service statistics: {json.dumps(stats, indent=2, default=str)}")

if __name__ == "__main__":
    asyncio.run(test_optimized_service())