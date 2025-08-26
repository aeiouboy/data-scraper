"""
Celery background tasks for product matching
"""
import asyncio
import logging
from typing import List, Dict, Any, Optional
from uuid import UUID
from datetime import datetime
from celery import shared_task
from celery.exceptions import Retry

from src.services.matching.database_matcher import DatabaseMatcher
from src.services.matching.hybrid_matcher import HybridMatcher
from src.services.matching.batch_processor import BatchProcessor
from src.models.matching import MatchResultCreate, MatchMetadataCreate, MetadataKeys

logger = logging.getLogger(__name__)


@shared_task(
    bind=True,
    autoretry_for=(Exception,),
    retry_kwargs={'max_retries': 3, 'countdown': 60},
    soft_time_limit=240,
    time_limit=300
)
def process_product_matching(self, product_id: str, min_confidence: float = 0.5):
    """
    Background task to find and store matches for a product
    
    Args:
        product_id: Product UUID as string
        min_confidence: Minimum confidence threshold
    """
    try:
        logger.info(f"Starting product matching for {product_id}")
        
        # Convert to UUID
        product_uuid = UUID(product_id)
        
        # Run the async matching process
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            matches = loop.run_until_complete(
                _run_product_matching(product_uuid, min_confidence)
            )
            
            logger.info(f"Completed product matching for {product_id}: {len(matches)} matches found")
            
            return {
                'product_id': product_id,
                'matches_found': len(matches),
                'status': 'success',
                'timestamp': datetime.now().isoformat()
            }
            
        finally:
            loop.close()
            
    except Exception as e:
        logger.error(f"Error in product matching task for {product_id}: {e}")
        
        # Retry with exponential backoff
        if self.request.retries < 3:
            countdown = 2 ** self.request.retries * 60
            raise self.retry(countdown=countdown, exc=e)
        
        # Final failure
        return {
            'product_id': product_id,
            'status': 'failed',
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }


@shared_task(
    bind=True,
    autoretry_for=(Exception,),
    retry_kwargs={'max_retries': 2, 'countdown': 120},
    soft_time_limit=540,
    time_limit=600
)
def batch_process_matches(
    self,
    matches_data: List[Dict[str, Any]],
    operation: str = 'create'
):
    """
    Background task for batch processing of matches
    
    Args:
        matches_data: List of match data dictionaries
        operation: Operation type ('create', 'update', 'delete')
    """
    try:
        logger.info(f"Starting batch {operation} for {len(matches_data)} matches")
        
        # Run the async batch processing
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            if operation == 'create':
                result = loop.run_until_complete(
                    _run_batch_creation(matches_data)
                )
            elif operation == 'update':
                result = loop.run_until_complete(
                    _run_batch_updates(matches_data)
                )
            elif operation == 'delete':
                result = loop.run_until_complete(
                    _run_batch_deletions(matches_data)
                )
            else:
                raise ValueError(f"Unknown operation: {operation}")
            
            logger.info(f"Completed batch {operation}: {result}")
            
            return {
                'operation': operation,
                'batch_size': len(matches_data),
                'result': result,
                'status': 'success',
                'timestamp': datetime.now().isoformat()
            }
            
        finally:
            loop.close()
            
    except Exception as e:
        logger.error(f"Error in batch {operation} task: {e}")
        
        # Retry with exponential backoff
        if self.request.retries < 2:
            countdown = 2 ** self.request.retries * 120
            raise self.retry(countdown=countdown, exc=e)
        
        return {
            'operation': operation,
            'batch_size': len(matches_data),
            'status': 'failed',
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }


@shared_task(
    bind=True,
    autoretry_for=(Exception,),
    retry_kwargs={'max_retries': 3, 'countdown': 180},
    soft_time_limit=300,
    time_limit=360
)
def refresh_product_matches(
    self,
    product_id: str,
    min_confidence: float = 0.5,
    force_recalculate: bool = False
):
    """
    Background task to refresh matches for a product
    
    Args:
        product_id: Product UUID as string
        min_confidence: Minimum confidence threshold
        force_recalculate: Whether to recalculate existing matches
    """
    try:
        logger.info(f"Starting match refresh for {product_id}")
        
        product_uuid = UUID(product_id)
        
        # Run the async refresh process
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            hybrid_matcher = HybridMatcher()
            
            loop.run_until_complete(
                hybrid_matcher.refresh_product_matches(
                    product_uuid,
                    min_confidence,
                    force_recalculate
                )
            )
            
            logger.info(f"Completed match refresh for {product_id}")
            
            return {
                'product_id': product_id,
                'force_recalculate': force_recalculate,
                'status': 'success',
                'timestamp': datetime.now().isoformat()
            }
            
        finally:
            loop.close()
            
    except Exception as e:
        logger.error(f"Error in refresh matches task for {product_id}: {e}")
        
        if self.request.retries < 3:
            countdown = 2 ** self.request.retries * 180
            raise self.retry(countdown=countdown, exc=e)
        
        return {
            'product_id': product_id,
            'status': 'failed',
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }


@shared_task(
    bind=True,
    autoretry_for=(Exception,),
    retry_kwargs={'max_retries': 2, 'countdown': 60},
    soft_time_limit=120,
    time_limit=150
)
def calculate_confidence_scores(
    self,
    match_pairs: List[Dict[str, str]]
):
    """
    Background task to calculate confidence scores for product pairs
    
    Args:
        match_pairs: List of {'source_id': 'uuid', 'target_id': 'uuid'} dicts
    """
    try:
        logger.info(f"Calculating confidence scores for {len(match_pairs)} pairs")
        
        # Run the async scoring process
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            results = loop.run_until_complete(
                _run_confidence_scoring(match_pairs)
            )
            
            logger.info(f"Completed confidence scoring for {len(match_pairs)} pairs")
            
            return {
                'pairs_processed': len(match_pairs),
                'results': results,
                'status': 'success',
                'timestamp': datetime.now().isoformat()
            }
            
        finally:
            loop.close()
            
    except Exception as e:
        logger.error(f"Error in confidence scoring task: {e}")
        
        if self.request.retries < 2:
            countdown = 2 ** self.request.retries * 60
            raise self.retry(countdown=countdown, exc=e)
        
        return {
            'pairs_processed': len(match_pairs),
            'status': 'failed',
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }


@shared_task
def cleanup_old_matches(days_to_keep: int = 30):
    """
    Background task to clean up old rejected matches
    
    Args:
        days_to_keep: Number of days to keep rejected matches
    """
    try:
        logger.info(f"Starting cleanup of matches older than {days_to_keep} days")
        
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            deleted_count = loop.run_until_complete(
                _run_match_cleanup(days_to_keep)
            )
            
            logger.info(f"Cleanup completed: {deleted_count} old matches deleted")
            
            return {
                'days_to_keep': days_to_keep,
                'deleted_count': deleted_count,
                'status': 'success',
                'timestamp': datetime.now().isoformat()
            }
            
        finally:
            loop.close()
            
    except Exception as e:
        logger.error(f"Error in cleanup task: {e}")
        
        return {
            'days_to_keep': days_to_keep,
            'status': 'failed',
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }


# Helper async functions

async def _run_product_matching(product_id: UUID, min_confidence: float):
    """Run product matching logic"""
    hybrid_matcher = HybridMatcher()
    
    matches = await hybrid_matcher.find_algorithmic_matches(
        product_id=product_id,
        min_confidence=min_confidence,
        limit=20
    )
    
    # Store matches in database
    db_matcher = DatabaseMatcher()
    stored_matches = []
    
    for match in matches:
        match_create = MatchResultCreate(
            source_product_id=product_id,
            matched_product_id=match.matched_product_id,
            confidence_score=match.confidence_score,
            matching_method=match.matching_method,
            status='pending'
        )
        
        # Add background task metadata
        metadata = [
            MatchMetadataCreate(
                matching_result_id=None,
                metadata_key=MetadataKeys.ALGORITHM_INFO,
                metadata_value=match.metadata[0]['metadata_value'] if match.metadata else {}
            ),
            MatchMetadataCreate(
                matching_result_id=None,
                metadata_key='background_task',
                metadata_value={
                    'task_name': 'process_product_matching',
                    'execution_timestamp': datetime.now().isoformat(),
                    'worker_info': 'celery_background'
                }
            )
        ]
        
        result = await db_matcher.create_match(match_create, metadata)
        if result:
            stored_matches.append(result)
    
    return stored_matches


async def _run_batch_creation(matches_data: List[Dict[str, Any]]):
    """Run batch match creation"""
    batch_processor = BatchProcessor()
    
    # Convert dict data to MatchResultCreate objects
    matches = []
    for match_data in matches_data:
        match = MatchResultCreate(
            source_product_id=UUID(match_data['source_product_id']),
            matched_product_id=UUID(match_data['matched_product_id']),
            confidence_score=match_data['confidence_score'],
            matching_method=match_data.get('matching_method', 'hybrid'),
            status=match_data.get('status', 'pending')
        )
        matches.append(match)
    
    results = await batch_processor.process_batch_creation(matches)
    
    return {
        'created_count': len([r for r in results if r is not None]),
        'failed_count': len([r for r in results if r is None])
    }


async def _run_batch_updates(updates_data: List[Dict[str, Any]]):
    """Run batch match updates"""
    batch_processor = BatchProcessor()
    results = await batch_processor.process_batch_updates(updates_data)
    
    return {
        'updated_count': len([r for r in results if r is not None]),
        'failed_count': len([r for r in results if r is None])
    }


async def _run_batch_deletions(deletion_data: List[Dict[str, Any]]):
    """Run batch match deletions"""
    batch_processor = BatchProcessor()
    
    # Extract match IDs
    match_ids = [UUID(item['match_id']) for item in deletion_data]
    
    result = await batch_processor.process_batch_deletion(match_ids)
    return result


async def _run_confidence_scoring(match_pairs: List[Dict[str, str]]):
    """Run confidence score calculations"""
    hybrid_matcher = HybridMatcher()
    results = []
    
    for pair in match_pairs:
        try:
            source_product = await hybrid_matcher._get_product(UUID(pair['source_id']))
            target_product = await hybrid_matcher._get_product(UUID(pair['target_id']))
            
            if source_product and target_product:
                confidence, metadata = await hybrid_matcher._calculate_match_confidence(
                    source_product, target_product
                )
                
                results.append({
                    'source_id': pair['source_id'],
                    'target_id': pair['target_id'],
                    'confidence_score': confidence,
                    'metadata': metadata
                })
            
        except Exception as e:
            logger.error(f"Error scoring pair {pair}: {e}")
            results.append({
                'source_id': pair['source_id'],
                'target_id': pair['target_id'],
                'error': str(e)
            })
    
    return results


async def _run_match_cleanup(days_to_keep: int):
    """Run cleanup of old matches"""
    from src.services.supabase_service import SupabaseService
    from datetime import datetime, timedelta
    
    db_service = SupabaseService()
    
    # Calculate cutoff date
    cutoff_date = datetime.now() - timedelta(days=days_to_keep)
    
    # Delete old rejected matches
    result = db_service.client.table('matching_results')\
        .delete()\
        .eq('status', 'rejected')\
        .lt('created_at', cutoff_date.isoformat())\
        .execute()
    
    return len(result.data) if result.data else 0