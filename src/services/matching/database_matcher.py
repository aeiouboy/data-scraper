"""
Database-driven product matching service
Core matching logic that queries database first, with fallback to algorithmic matching
"""
import logging
from typing import List, Dict, Any, Optional, Tuple
from uuid import UUID
from datetime import datetime
import asyncio

from src.services.supabase_service import SupabaseService
from src.models.matching import (
    MatchResult, MatchResultCreate, MatchResultResponse, MatchStatsResponse,
    MatchingMethod, MatchStatus, MatchMetadata, MatchMetadataCreate, MetadataKeys
)
from src.services.matching.confidence_scorer import ConfidenceScorer
from src.utils.matching.string_similarity import StringSimilarity
from src.utils.matching.brand_matcher import BrandMatcher
from src.utils.matching.sku_analyzer import SKUAnalyzer

logger = logging.getLogger(__name__)


class DatabaseMatcher:
    """Database-driven product matching service"""
    
    def __init__(self):
        self.db_service = SupabaseService()
        self.confidence_scorer = ConfidenceScorer()
        self.string_similarity = StringSimilarity()
        self.brand_matcher = BrandMatcher()
        self.sku_analyzer = SKUAnalyzer()
    
    async def find_matches(
        self,
        product_id: UUID,
        min_confidence: float = 0.5,
        include_rejected: bool = False,
        limit: int = 10
    ) -> List[MatchResultResponse]:
        """
        Find existing matches for a product in database
        
        Args:
            product_id: ID of the product to find matches for
            min_confidence: Minimum confidence threshold
            include_rejected: Whether to include rejected matches
            limit: Maximum number of matches to return
        
        Returns:
            List of match results with product details
        """
        try:
            # Build query conditions
            conditions = [
                f"source_product_id.eq.{product_id}",
                f"confidence_score.gte.{min_confidence}"
            ]
            
            if not include_rejected:
                conditions.append("status.neq.rejected")
            
            # Query matches from database
            query = self.db_service.client.table('matching_results')\
                .select('''
                    *,
                    source_product:products!source_product_id(id, name, brand, sku, retailer_code),
                    matched_product:products!matched_product_id(id, name, brand, sku, retailer_code)
                ''')\
                .order('confidence_score', desc=True)\
                .limit(limit)
            
            # Apply conditions
            for condition in conditions:
                field, op, value = condition.split('.')
                if op == 'eq':
                    query = query.eq(field, value)
                elif op == 'neq':
                    query = query.neq(field, value)
                elif op == 'gte':
                    query = query.gte(field, float(value))
            
            result = query.execute()
            
            # Convert to response models
            matches = []
            for row in result.data:
                match_response = MatchResultResponse(
                    id=row['id'],
                    source_product_id=row['source_product_id'],
                    matched_product_id=row['matched_product_id'],
                    confidence_score=row['confidence_score'],
                    matching_method=row['matching_method'],
                    status=row['status'],
                    created_at=datetime.fromisoformat(row['created_at'].replace('Z', '+00:00')),
                    updated_at=datetime.fromisoformat(row['updated_at'].replace('Z', '+00:00')),
                    source_product=row.get('source_product'),
                    matched_product=row.get('matched_product')
                )
                matches.append(match_response)
            
            logger.info(f"Found {len(matches)} database matches for product {product_id}")
            return matches
            
        except Exception as e:
            logger.error(f"Error finding matches for product {product_id}: {e}")
            return []
    
    async def create_match(
        self,
        match_data: MatchResultCreate,
        metadata: Optional[List[MatchMetadataCreate]] = None
    ) -> Optional[MatchResultResponse]:
        """
        Create a new product match in database
        
        Args:
            match_data: Match data to create
            metadata: Optional metadata to associate with the match
        
        Returns:
            Created match result or None if failed
        """
        try:
            # Check if match already exists
            existing = await self._check_existing_match(
                match_data.source_product_id,
                match_data.matched_product_id
            )
            
            if existing:
                logger.warning(f"Match already exists between {match_data.source_product_id} and {match_data.matched_product_id}")
                return existing
            
            # Insert match result
            match_dict = match_data.dict()
            result = self.db_service.client.table('matching_results')\
                .insert(match_dict)\
                .execute()
            
            if not result.data:
                logger.error("Failed to create match - no data returned")
                return None
            
            match_row = result.data[0]
            match_id = match_row['id']
            
            # Insert metadata if provided
            if metadata:
                metadata_rows = []
                for meta in metadata:
                    meta_dict = meta.dict()
                    meta_dict['matching_result_id'] = match_id
                    metadata_rows.append(meta_dict)
                
                if metadata_rows:
                    self.db_service.client.table('matching_metadata')\
                        .insert(metadata_rows)\
                        .execute()
            
            # Return full match response
            return await self._get_match_with_details(match_id)
            
        except Exception as e:
            logger.error(f"Error creating match: {e}")
            return None
    
    async def update_match(
        self,
        match_id: UUID,
        update_data: Dict[str, Any]
    ) -> Optional[MatchResultResponse]:
        """
        Update an existing match
        
        Args:
            match_id: ID of match to update
            update_data: Fields to update
        
        Returns:
            Updated match result or None if failed
        """
        try:
            result = self.db_service.client.table('matching_results')\
                .update(update_data)\
                .eq('id', str(match_id))\
                .execute()
            
            if not result.data:
                logger.error(f"Match {match_id} not found for update")
                return None
            
            return await self._get_match_with_details(match_id)
            
        except Exception as e:
            logger.error(f"Error updating match {match_id}: {e}")
            return None
    
    async def delete_match(self, match_id: UUID) -> bool:
        """
        Delete a match and its metadata
        
        Args:
            match_id: ID of match to delete
        
        Returns:
            True if successful, False otherwise
        """
        try:
            # Delete metadata first (cascade should handle this, but being explicit)
            self.db_service.client.table('matching_metadata')\
                .delete()\
                .eq('matching_result_id', str(match_id))\
                .execute()
            
            # Delete match
            result = self.db_service.client.table('matching_results')\
                .delete()\
                .eq('id', str(match_id))\
                .execute()
            
            return len(result.data) > 0
            
        except Exception as e:
            logger.error(f"Error deleting match {match_id}: {e}")
            return False
    
    async def get_match_stats(self) -> MatchStatsResponse:
        """
        Get statistics about matches in database
        
        Returns:
            Statistics about matching results
        """
        try:
            # Get all matches to analyze
            all_matches_result = self.db_service.client.table('matching_results')\
                .select('*')\
                .execute()
            
            matches = all_matches_result.data or []
            total_matches = len(matches)
            
            if total_matches == 0:
                return MatchStatsResponse(
                    total_matches=0,
                    pending_matches=0,
                    confirmed_matches=0,
                    rejected_matches=0,
                    average_confidence=0.0,
                    methods_breakdown={},
                    top_confidence_matches=[]
                )
            
            # Count by status
            status_counts = {'pending': 0, 'confirmed': 0, 'rejected': 0}
            method_counts = {}
            confidence_scores = []
            
            for match in matches:
                # Count status
                status = match.get('status', 'pending')
                if status in status_counts:
                    status_counts[status] += 1
                
                # Count methods
                method = match.get('matching_method', 'unknown')
                method_counts[method] = method_counts.get(method, 0) + 1
                
                # Collect confidence scores
                confidence = match.get('confidence_score', 0.0)
                confidence_scores.append(float(confidence))
            
            # Calculate average confidence
            avg_confidence = sum(confidence_scores) / len(confidence_scores) if confidence_scores else 0.0
            
            # Get top confidence matches (limit to 5)
            sorted_matches = sorted(matches, key=lambda m: m.get('confidence_score', 0.0), reverse=True)[:5]
            
            top_matches = []
            for match in sorted_matches:
                # Create simplified match response without joining product details for now
                match_response = MatchResultResponse(
                    id=match['id'],
                    source_product_id=match['source_product_id'],
                    matched_product_id=match['matched_product_id'],
                    confidence_score=match['confidence_score'],
                    matching_method=match['matching_method'],
                    status=match['status'],
                    created_at=datetime.fromisoformat(match['created_at'].replace('Z', '+00:00')),
                    updated_at=datetime.fromisoformat(match['updated_at'].replace('Z', '+00:00')),
                    source_product=None,  # Skip product details to avoid complex joins
                    matched_product=None
                )
                top_matches.append(match_response)
            
            return MatchStatsResponse(
                total_matches=total_matches,
                pending_matches=status_counts['pending'],
                confirmed_matches=status_counts['confirmed'],
                rejected_matches=status_counts['rejected'],
                average_confidence=round(avg_confidence, 3),
                methods_breakdown=method_counts,
                top_confidence_matches=top_matches
            )
            
        except Exception as e:
            logger.error(f"Error getting match stats: {e}")
            return MatchStatsResponse(
                total_matches=0,
                pending_matches=0,
                confirmed_matches=0,
                rejected_matches=0,
                average_confidence=0.0,
                methods_breakdown={},
                top_confidence_matches=[]
            )
    
    async def _check_existing_match(
        self,
        source_id: UUID,
        matched_id: UUID
    ) -> Optional[MatchResultResponse]:
        """Check if a match already exists between two products"""
        try:
            result = self.db_service.client.table('matching_results')\
                .select('*')\
                .eq('source_product_id', str(source_id))\
                .eq('matched_product_id', str(matched_id))\
                .execute()
            
            if result.data:
                row = result.data[0]
                return MatchResultResponse(
                    id=row['id'],
                    source_product_id=row['source_product_id'],
                    matched_product_id=row['matched_product_id'],
                    confidence_score=row['confidence_score'],
                    matching_method=row['matching_method'],
                    status=row['status'],
                    created_at=datetime.fromisoformat(row['created_at'].replace('Z', '+00:00')),
                    updated_at=datetime.fromisoformat(row['updated_at'].replace('Z', '+00:00'))
                )
            
            return None
            
        except Exception as e:
            logger.error(f"Error checking existing match: {e}")
            return None
    
    async def _get_match_with_details(self, match_id: UUID) -> Optional[MatchResultResponse]:
        """Get match with full product and metadata details"""
        try:
            result = self.db_service.client.table('matching_results')\
                .select('''
                    *,
                    source_product:products!source_product_id(id, name, brand, sku, retailer_code),
                    matched_product:products!matched_product_id(id, name, brand, sku, retailer_code)
                ''')\
                .eq('id', str(match_id))\
                .execute()
            
            if not result.data:
                return None
            
            row = result.data[0]
            
            # Get metadata
            metadata_result = self.db_service.client.table('matching_metadata')\
                .select('*')\
                .eq('matching_result_id', str(match_id))\
                .execute()
            
            return MatchResultResponse(
                id=row['id'],
                source_product_id=row['source_product_id'],
                matched_product_id=row['matched_product_id'],
                confidence_score=row['confidence_score'],
                matching_method=row['matching_method'],
                status=row['status'],
                created_at=datetime.fromisoformat(row['created_at'].replace('Z', '+00:00')),
                updated_at=datetime.fromisoformat(row['updated_at'].replace('Z', '+00:00')),
                source_product=row.get('source_product'),
                matched_product=row.get('matched_product'),
                metadata=metadata_result.data if metadata_result.data else []
            )
            
        except Exception as e:
            logger.error(f"Error getting match details: {e}")
            return None