"""
Hybrid matching service that combines database and algorithmic matching
Provides fallback to Brave API when database matches are insufficient
"""
import logging
from typing import List, Dict, Any, Optional, Tuple
from uuid import UUID
from datetime import datetime
import asyncio

from src.services.matching.database_matcher import DatabaseMatcher
from src.services.matching.confidence_scorer import ConfidenceScorer, ScoreComponents
from src.utils.matching.string_similarity import StringSimilarity
from src.utils.matching.brand_matcher import BrandMatcher
from src.utils.matching.sku_analyzer import SKUAnalyzer
from src.services.supabase_service import SupabaseService
from src.models.matching import (
    MatchResultCreate, MatchResultResponse, MatchingMethod, MatchStatus,
    MatchMetadataCreate, MetadataKeys
)

logger = logging.getLogger(__name__)


class HybridMatcher:
    """Hybrid matching service combining database and algorithmic approaches"""
    
    def __init__(self):
        self.db_matcher = DatabaseMatcher()
        self.db_service = SupabaseService()
        self.confidence_scorer = ConfidenceScorer()
        self.string_similarity = StringSimilarity()
        self.brand_matcher = BrandMatcher()
        self.sku_analyzer = SKUAnalyzer()
    
    async def find_matches(
        self,
        product_id: UUID,
        min_confidence: float = 0.5,
        use_database: bool = True,
        use_algorithmic: bool = True,
        limit: int = 10
    ) -> List[MatchResultResponse]:
        """
        Find matches using hybrid approach
        
        Args:
            product_id: Product to find matches for
            min_confidence: Minimum confidence threshold
            use_database: Whether to query database first
            use_algorithmic: Whether to use algorithmic fallback
            limit: Maximum matches to return
        
        Returns:
            List of match results
        """
        matches = []
        
        try:
            # Step 1: Try database matches first
            if use_database:
                db_matches = await self.db_matcher.find_matches(
                    product_id=product_id,
                    min_confidence=min_confidence,
                    limit=limit
                )
                matches.extend(db_matches)
                
                logger.info(f"Found {len(db_matches)} database matches for {product_id}")
            
            # Step 2: If insufficient matches, use algorithmic approach
            if use_algorithmic and len(matches) < limit:
                remaining_slots = limit - len(matches)
                
                algorithmic_matches = await self.find_algorithmic_matches(
                    product_id=product_id,
                    min_confidence=min_confidence,
                    limit=remaining_slots,
                    exclude_existing=matches
                )
                
                matches.extend(algorithmic_matches)
                
                logger.info(f"Added {len(algorithmic_matches)} algorithmic matches for {product_id}")
            
            # Sort by confidence and apply final limit
            matches.sort(key=lambda x: x.confidence_score, reverse=True)
            return matches[:limit]
            
        except Exception as e:
            logger.error(f"Error in hybrid matching for product {product_id}: {e}")
            return matches
    
    async def find_algorithmic_matches(
        self,
        product_id: UUID,
        min_confidence: float = 0.5,
        limit: int = 10,
        exclude_existing: Optional[List[MatchResultResponse]] = None
    ) -> List[MatchResultResponse]:
        """
        Find matches using algorithmic approach
        
        Args:
            product_id: Product to find matches for
            min_confidence: Minimum confidence threshold
            limit: Maximum matches to return
            exclude_existing: Existing matches to exclude
        
        Returns:
            List of algorithmic match results
        """
        try:
            # Get source product
            source_product = await self._get_product(product_id)
            if not source_product:
                logger.error(f"Source product {product_id} not found")
                return []
            
            # Get candidate products from different retailers
            candidates = await self._get_candidate_products(
                source_product,
                exclude_existing=exclude_existing
            )
            
            # Score each candidate
            scored_matches = []
            for candidate in candidates:
                confidence, metadata = await self._calculate_match_confidence(
                    source_product, candidate
                )
                
                if confidence >= min_confidence:
                    # Create match response (not yet stored in database)
                    match_response = MatchResultResponse(
                        id=None,  # Will be generated when stored
                        source_product_id=product_id,
                        matched_product_id=UUID(candidate['id']),
                        confidence_score=confidence,
                        matching_method=metadata.get('primary_method', MatchingMethod.HYBRID),
                        status=MatchStatus.PENDING,
                        created_at=datetime.now(),
                        updated_at=datetime.now(),
                        source_product=source_product,
                        matched_product=candidate,
                        metadata=[{
                            'metadata_key': MetadataKeys.ALGORITHM_INFO,
                            'metadata_value': metadata
                        }]
                    )
                    
                    scored_matches.append(match_response)
            
            # Sort by confidence and return top matches
            scored_matches.sort(key=lambda x: x.confidence_score, reverse=True)
            return scored_matches[:limit]
            
        except Exception as e:
            logger.error(f"Error in algorithmic matching: {e}")
            return []
    
    async def refresh_product_matches(
        self,
        product_id: UUID,
        min_confidence: float = 0.5,
        force_recalculate: bool = False
    ):
        """
        Refresh matches for a product using latest algorithms
        
        Args:
            product_id: Product to refresh matches for
            min_confidence: Minimum confidence threshold
            force_recalculate: Whether to recalculate existing matches
        """
        try:
            logger.info(f"Starting match refresh for product {product_id}")
            
            if force_recalculate:
                # Delete existing matches
                existing_matches = await self.db_matcher.find_matches(
                    product_id, min_confidence=0.0, include_rejected=True
                )
                
                for match in existing_matches:
                    await self.db_matcher.delete_match(match.id)
                
                logger.info(f"Deleted {len(existing_matches)} existing matches")
            
            # Find new matches using algorithmic approach
            new_matches = await self.find_algorithmic_matches(
                product_id=product_id,
                min_confidence=min_confidence,
                limit=20  # Higher limit for refresh
            )
            
            # Store new matches in database
            stored_count = 0
            for match in new_matches:
                match_create = MatchResultCreate(
                    source_product_id=product_id,
                    matched_product_id=match.matched_product_id,
                    confidence_score=match.confidence_score,
                    matching_method=match.matching_method,
                    status=MatchStatus.PENDING
                )
                
                # Create metadata
                metadata = [
                    MatchMetadataCreate(
                        matching_result_id=None,
                        metadata_key=MetadataKeys.ALGORITHM_INFO,
                        metadata_value=match.metadata[0]['metadata_value'] if match.metadata else {}
                    ),
                    MatchMetadataCreate(
                        matching_result_id=None,
                        metadata_key=MetadataKeys.MIGRATION_INFO,
                        metadata_value={
                            'refresh_type': 'algorithmic_refresh',
                            'force_recalculate': force_recalculate,
                            'refresh_timestamp': datetime.now().isoformat()
                        }
                    )
                ]
                
                result = await self.db_matcher.create_match(match_create, metadata)
                if result:
                    stored_count += 1
            
            logger.info(f"Stored {stored_count} new matches for product {product_id}")
            
        except Exception as e:
            logger.error(f"Error refreshing matches for product {product_id}: {e}")
    
    async def _get_product(self, product_id: UUID) -> Optional[Dict[str, Any]]:
        """Get product details from database"""
        try:
            result = self.db_service.client.table('products')\
                .select('*')\
                .eq('id', str(product_id))\
                .execute()
            
            return result.data[0] if result.data else None
            
        except Exception as e:
            logger.error(f"Error fetching product {product_id}: {e}")
            return None
    
    async def _get_candidate_products(
        self,
        source_product: Dict[str, Any],
        exclude_existing: Optional[List[MatchResultResponse]] = None
    ) -> List[Dict[str, Any]]:
        """Get candidate products for matching"""
        try:
            # Get products from different retailers
            query = self.db_service.client.table('products')\
                .select('*')\
                .neq('retailer_code', source_product['retailer_code'])
            
            # Filter by category if available
            if source_product.get('category'):
                query = query.eq('category', source_product['category'])
            
            # Limit to reasonable number for performance
            result = query.limit(1000).execute()
            candidates = result.data or []
            
            # Exclude existing matches
            if exclude_existing:
                excluded_ids = {str(match.matched_product_id) for match in exclude_existing}
                candidates = [c for c in candidates if c['id'] not in excluded_ids]
            
            return candidates
            
        except Exception as e:
            logger.error(f"Error fetching candidate products: {e}")
            return []
    
    async def _calculate_match_confidence(
        self,
        source_product: Dict[str, Any],
        candidate_product: Dict[str, Any]
    ) -> Tuple[float, Dict[str, Any]]:
        """
        Calculate comprehensive match confidence between two products
        
        Args:
            source_product: Source product data
            candidate_product: Candidate product data
        
        Returns:
            Tuple of (confidence_score, metadata)
        """
        try:
            # Initialize score components
            scores = ScoreComponents()
            metadata = {
                'algorithm_version': '2.0',
                'calculation_timestamp': datetime.now().isoformat(),
                'methods_used': []
            }
            
            # Name similarity scoring
            if source_product.get('name') and candidate_product.get('name'):
                name_analysis = self.string_similarity.calculate_name_similarity_detailed(
                    source_product['name'],
                    candidate_product['name']
                )
                scores.name_similarity = name_analysis['final_confidence']
                metadata['name_matching'] = name_analysis
                metadata['methods_used'].append('name_similarity')
            
            # Brand matching
            if source_product.get('brand') and candidate_product.get('brand'):
                brand_score = self.confidence_scorer.calculate_brand_match_score(
                    source_product['brand'],
                    candidate_product['brand'],
                    [],  # TODO: Add brand aliases
                    []
                )
                scores.brand_match = brand_score
                metadata['brand_matching'] = {
                    'brand_1': source_product['brand'],
                    'brand_2': candidate_product['brand'],
                    'score': brand_score
                }
                metadata['methods_used'].append('brand_matching')
            
            # SKU similarity
            if source_product.get('sku') and candidate_product.get('sku'):
                sku_score = self.confidence_scorer.calculate_sku_similarity_score(
                    source_product['sku'],
                    candidate_product['sku'],
                    [],  # TODO: Extract SKU patterns
                    []
                )
                scores.sku_similarity = sku_score
                metadata['sku_matching'] = {
                    'sku_1': source_product['sku'],
                    'sku_2': candidate_product['sku'],
                    'score': sku_score
                }
                metadata['methods_used'].append('sku_matching')
            
            # Specification matching
            source_specs = source_product.get('specifications', {})
            candidate_specs = candidate_product.get('specifications', {})
            if source_specs and candidate_specs:
                spec_score = self.confidence_scorer.calculate_specification_match_score(
                    source_specs,
                    candidate_specs
                )
                scores.specification_match = spec_score
                metadata['spec_matching'] = {
                    'specs_1': source_specs,
                    'specs_2': candidate_specs,
                    'score': spec_score
                }
                metadata['methods_used'].append('specification_matching')
            
            # Price proximity (if both have prices)
            source_price = source_product.get('price')
            candidate_price = candidate_product.get('price')
            if source_price and candidate_price:
                price_score = self.confidence_scorer.calculate_price_proximity_score(
                    float(source_price),
                    float(candidate_price)
                )
                scores.price_proximity = price_score
                metadata['price_matching'] = {
                    'price_1': source_price,
                    'price_2': candidate_price,
                    'score': price_score
                }
                metadata['methods_used'].append('price_proximity')
            
            # Category matching
            if (source_product.get('category') and candidate_product.get('category')):
                category_match = source_product['category'] == candidate_product['category']
                scores.category_match = 1.0 if category_match else 0.0
                metadata['category_matching'] = {
                    'category_1': source_product['category'],
                    'category_2': candidate_product['category'],
                    'exact_match': category_match
                }
                metadata['methods_used'].append('category_matching')
            
            # Retailer diversity bonus (different retailers)
            different_retailers = source_product['retailer_code'] != candidate_product['retailer_code']
            scores.retailer_diversity = 1.0 if different_retailers else 0.0
            
            # Calculate final confidence
            confidence, calculation_metadata = self.confidence_scorer.calculate_confidence(scores)
            
            # Determine primary method
            method_scores = {
                'name': scores.name_similarity,
                'brand': scores.brand_match,
                'sku': scores.sku_similarity,
                'specifications': scores.specification_match
            }
            primary_method = max(method_scores.items(), key=lambda x: x[1])[0]
            
            # Combine metadata
            metadata.update(calculation_metadata)
            metadata['primary_method'] = primary_method
            metadata['confidence_category'] = self.confidence_scorer.get_confidence_category(confidence)
            
            return confidence, metadata
            
        except Exception as e:
            logger.error(f"Error calculating match confidence: {e}")
            return 0.0, {'error': str(e)}