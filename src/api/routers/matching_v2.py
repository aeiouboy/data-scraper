"""
Database-driven product matching API endpoints (Version 2)
New endpoints that query database first with fallback to algorithmic matching
"""
from fastapi import APIRouter, HTTPException, Query, BackgroundTasks, Depends
from typing import List, Dict, Any, Optional
import logging
from uuid import UUID
from datetime import datetime

from src.services.matching.database_matcher import DatabaseMatcher
from src.services.matching.hybrid_matcher import HybridMatcher
from src.services.matching.batch_processor import BatchProcessor
from src.models.matching import (
    MatchResult, MatchResultCreate, MatchResultUpdate, MatchResultResponse,
    MatchStatsResponse, MatchMetadata, MatchMetadataCreate
)

logger = logging.getLogger(__name__)
router = APIRouter(tags=["matching-v2"])


# Stats and health endpoints (must come before parameterized routes)
@router.get("/matches/stats", response_model=MatchStatsResponse)
async def get_matching_statistics():
    """
    Get statistics about matching results
    """
    try:
        db_matcher = DatabaseMatcher()
        stats = await db_matcher.get_match_stats()
        return stats
        
    except Exception as e:
        logger.error(f"Error getting match statistics: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve statistics")


@router.get("/matches/health")
async def matching_health_check():
    """
    Health check endpoint for matching service
    """
    try:
        db_matcher = DatabaseMatcher()
        
        # Simple database connectivity test
        stats = await db_matcher.get_match_stats()
        
        return {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "database_connection": "ok",
            "total_matches": stats.total_matches,
            "service_version": "2.0.0"
        }
        
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {
            "status": "unhealthy",
            "timestamp": datetime.now().isoformat(),
            "error": str(e),
            "service_version": "2.0.0"
        }


# Parameterized endpoints
@router.get("/matches/{product_id}", response_model=List[MatchResultResponse])
async def get_product_matches(
    product_id: UUID,
    min_confidence: float = Query(0.5, ge=0.0, le=1.0, description="Minimum confidence threshold"),
    include_rejected: bool = Query(False, description="Include rejected matches"),
    limit: int = Query(10, ge=1, le=100, description="Maximum number of matches"),
    use_fallback: bool = Query(True, description="Use algorithmic fallback if no database matches")
):
    """
    Get matches for a specific product
    
    Queries database first, optionally falls back to algorithmic matching
    """
    try:
        db_matcher = DatabaseMatcher()
        
        # Try database first
        matches = await db_matcher.find_matches(
            product_id=product_id,
            min_confidence=min_confidence,
            include_rejected=include_rejected,
            limit=limit
        )
        
        # If no database matches and fallback enabled, try algorithmic matching
        if not matches and use_fallback:
            logger.info(f"No database matches for {product_id}, using algorithmic fallback")
            
            hybrid_matcher = HybridMatcher()
            algorithmic_matches = await hybrid_matcher.find_algorithmic_matches(
                product_id=product_id,
                min_confidence=min_confidence,
                limit=limit
            )
            
            # Store algorithmic matches in database for future use
            for match in algorithmic_matches:
                match_create = MatchResultCreate(
                    source_product_id=product_id,
                    matched_product_id=match.matched_product_id,
                    confidence_score=match.confidence_score,
                    matching_method=match.matching_method,
                    status='pending'
                )
                
                # Create metadata for algorithmic match
                metadata = [
                    MatchMetadataCreate(
                        matching_result_id=None,  # Will be set by create_match
                        metadata_key='algorithm_generated',
                        metadata_value={
                            'fallback_trigger': 'no_database_matches',
                            'algorithm_version': '2.0',
                            'created_timestamp': datetime.now().isoformat()
                        }
                    )
                ]
                
                await db_matcher.create_match(match_create, metadata)
            
            matches = algorithmic_matches
        
        return matches
        
    except Exception as e:
        logger.error(f"Error getting matches for product {product_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve matches")


@router.post("/matches", response_model=MatchResultResponse)
async def create_match(
    match_data: MatchResultCreate,
    metadata: Optional[List[MatchMetadataCreate]] = None
):
    """
    Create a new product match relationship
    """
    try:
        db_matcher = DatabaseMatcher()
        
        result = await db_matcher.create_match(match_data, metadata)
        
        if not result:
            raise HTTPException(status_code=400, detail="Failed to create match")
        
        return result
        
    except Exception as e:
        logger.error(f"Error creating match: {e}")
        raise HTTPException(status_code=500, detail="Failed to create match")


@router.put("/matches/{match_id}", response_model=MatchResultResponse)
async def update_match(
    match_id: UUID,
    update_data: MatchResultUpdate
):
    """
    Update an existing match
    """
    try:
        db_matcher = DatabaseMatcher()
        
        # Convert to dict, excluding None values
        update_dict = {
            k: v for k, v in update_data.dict().items() 
            if v is not None
        }
        
        if not update_dict:
            raise HTTPException(status_code=400, detail="No update data provided")
        
        result = await db_matcher.update_match(match_id, update_dict)
        
        if not result:
            raise HTTPException(status_code=404, detail="Match not found")
        
        return result
        
    except Exception as e:
        logger.error(f"Error updating match {match_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to update match")


@router.delete("/matches/{match_id}")
async def delete_match(match_id: UUID):
    """
    Delete a match and its metadata
    """
    try:
        db_matcher = DatabaseMatcher()
        
        success = await db_matcher.delete_match(match_id)
        
        if not success:
            raise HTTPException(status_code=404, detail="Match not found")
        
        return {"message": "Match deleted successfully"}
        
    except Exception as e:
        logger.error(f"Error deleting match {match_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete match")


@router.post("/matches/batch")
async def create_matches_batch(
    matches: List[MatchResultCreate],
    background_tasks: BackgroundTasks,
    metadata_per_match: Optional[List[List[MatchMetadataCreate]]] = None
):
    """
    Create multiple matches in batch
    """
    try:
        if len(matches) > 1000:
            raise HTTPException(status_code=400, detail="Batch size too large (max 1000)")
        
        batch_processor = BatchProcessor()
        
        # Process in background for large batches
        if len(matches) > 100:
            background_tasks.add_task(
                batch_processor.process_batch_creation,
                matches,
                metadata_per_match
            )
            
            return {
                "message": f"Batch creation started for {len(matches)} matches",
                "status": "processing",
                "batch_size": len(matches)
            }
        else:
            # Process immediately for small batches
            results = await batch_processor.process_batch_creation(
                matches, metadata_per_match
            )
            
            return {
                "message": f"Batch creation completed",
                "status": "completed",
                "created_count": len([r for r in results if r is not None]),
                "failed_count": len([r for r in results if r is None]),
                "results": results
            }
        
    except Exception as e:
        logger.error(f"Error creating batch matches: {e}")
        raise HTTPException(status_code=500, detail="Failed to create batch matches")


@router.put("/matches/batch")
async def update_matches_batch(
    updates: List[Dict[str, Any]],  # [{"match_id": UUID, "updates": {...}}]
    background_tasks: BackgroundTasks
):
    """
    Update multiple matches in batch
    
    Expected format: [{"match_id": "uuid", "updates": {"status": "confirmed", ...}}]
    """
    try:
        if len(updates) > 1000:
            raise HTTPException(status_code=400, detail="Batch size too large (max 1000)")
        
        batch_processor = BatchProcessor()
        
        # Validate input format
        for update in updates:
            if "match_id" not in update or "updates" not in update:
                raise HTTPException(
                    status_code=400, 
                    detail="Each update must have 'match_id' and 'updates' fields"
                )
        
        # Process in background for large batches
        if len(updates) > 100:
            background_tasks.add_task(
                batch_processor.process_batch_updates,
                updates
            )
            
            return {
                "message": f"Batch update started for {len(updates)} matches",
                "status": "processing",
                "batch_size": len(updates)
            }
        else:
            # Process immediately for small batches
            results = await batch_processor.process_batch_updates(updates)
            
            return {
                "message": "Batch update completed",
                "status": "completed",
                "updated_count": len([r for r in results if r is not None]),
                "failed_count": len([r for r in results if r is None]),
                "results": results
            }
        
    except Exception as e:
        logger.error(f"Error updating batch matches: {e}")
        raise HTTPException(status_code=500, detail="Failed to update batch matches")


@router.post("/matches/{product_id}/refresh")
async def refresh_product_matches(
    product_id: UUID,
    background_tasks: BackgroundTasks,
    min_confidence: float = Query(0.5, ge=0.0, le=1.0),
    force_recalculate: bool = Query(False, description="Force recalculation of existing matches")
):
    """
    Refresh matches for a product using latest algorithms
    """
    try:
        hybrid_matcher = HybridMatcher()
        
        # Run refresh in background
        background_tasks.add_task(
            hybrid_matcher.refresh_product_matches,
            product_id,
            min_confidence,
            force_recalculate
        )
        
        return {
            "message": f"Match refresh started for product {product_id}",
            "status": "processing",
            "min_confidence": min_confidence,
            "force_recalculate": force_recalculate
        }
        
    except Exception as e:
        logger.error(f"Error refreshing matches for product {product_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to refresh matches")