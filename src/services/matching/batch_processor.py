"""
Batch processing service for handling bulk matching operations
Efficiently processes large batches of matching operations with error handling
"""
import asyncio
import logging
from typing import List, Dict, Any, Optional
from uuid import UUID
from datetime import datetime
import json

from src.services.matching.database_matcher import DatabaseMatcher
from src.models.matching import (
    MatchResultCreate, MatchResultResponse, MatchMetadataCreate
)

logger = logging.getLogger(__name__)


class BatchProcessor:
    """Service for processing bulk matching operations"""
    
    def __init__(self, batch_size: int = 100, max_concurrent: int = 10):
        self.db_matcher = DatabaseMatcher()
        self.batch_size = batch_size
        self.max_concurrent = max_concurrent
        self.semaphore = asyncio.Semaphore(max_concurrent)
    
    async def process_batch_creation(
        self,
        matches: List[MatchResultCreate],
        metadata_per_match: Optional[List[List[MatchMetadataCreate]]] = None
    ) -> List[Optional[MatchResultResponse]]:
        """
        Process batch creation of matches
        
        Args:
            matches: List of matches to create
            metadata_per_match: Optional metadata for each match
        
        Returns:
            List of created match results (None for failed creations)
        """
        logger.info(f"Starting batch creation of {len(matches)} matches")
        
        start_time = datetime.now()
        results = []
        successful = 0
        failed = 0
        
        try:
            # Process in smaller batches to avoid overwhelming the database
            for i in range(0, len(matches), self.batch_size):
                batch = matches[i:i + self.batch_size]
                batch_metadata = None
                
                if metadata_per_match:
                    batch_metadata = metadata_per_match[i:i + self.batch_size]
                
                # Process batch concurrently
                batch_results = await self._process_creation_batch_concurrent(
                    batch, batch_metadata
                )
                
                results.extend(batch_results)
                
                # Update counters
                batch_successful = len([r for r in batch_results if r is not None])
                batch_failed = len(batch_results) - batch_successful
                
                successful += batch_successful
                failed += batch_failed
                
                logger.info(f"Batch {i//self.batch_size + 1}: {batch_successful} success, {batch_failed} failed")
                
                # Small delay between batches
                if i + self.batch_size < len(matches):
                    await asyncio.sleep(0.1)
            
            duration = (datetime.now() - start_time).total_seconds()
            
            logger.info(
                f"Batch creation completed: {successful} successful, {failed} failed "
                f"in {duration:.2f} seconds"
            )
            
            return results
            
        except Exception as e:
            logger.error(f"Error in batch creation: {e}")
            return results
    
    async def process_batch_updates(
        self,
        updates: List[Dict[str, Any]]
    ) -> List[Optional[MatchResultResponse]]:
        """
        Process batch updates of matches
        
        Args:
            updates: List of update dictionaries with match_id and updates
        
        Returns:
            List of updated match results (None for failed updates)
        """
        logger.info(f"Starting batch update of {len(updates)} matches")
        
        start_time = datetime.now()
        results = []
        successful = 0
        failed = 0
        
        try:
            # Process in smaller batches
            for i in range(0, len(updates), self.batch_size):
                batch = updates[i:i + self.batch_size]
                
                # Process batch concurrently
                batch_results = await self._process_update_batch_concurrent(batch)
                
                results.extend(batch_results)
                
                # Update counters
                batch_successful = len([r for r in batch_results if r is not None])
                batch_failed = len(batch_results) - batch_successful
                
                successful += batch_successful
                failed += batch_failed
                
                logger.info(f"Update batch {i//self.batch_size + 1}: {batch_successful} success, {batch_failed} failed")
                
                # Small delay between batches
                if i + self.batch_size < len(updates):
                    await asyncio.sleep(0.1)
            
            duration = (datetime.now() - start_time).total_seconds()
            
            logger.info(
                f"Batch update completed: {successful} successful, {failed} failed "
                f"in {duration:.2f} seconds"
            )
            
            return results
            
        except Exception as e:
            logger.error(f"Error in batch update: {e}")
            return results
    
    async def process_batch_deletion(
        self,
        match_ids: List[UUID]
    ) -> Dict[str, Any]:
        """
        Process batch deletion of matches
        
        Args:
            match_ids: List of match IDs to delete
        
        Returns:
            Dictionary with deletion results
        """
        logger.info(f"Starting batch deletion of {len(match_ids)} matches")
        
        start_time = datetime.now()
        successful = 0
        failed = 0
        failed_ids = []
        
        try:
            # Process deletions concurrently with semaphore control
            tasks = []
            for match_id in match_ids:
                task = self._delete_single_match_with_semaphore(match_id)
                tasks.append(task)
            
            # Wait for all deletions to complete
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Process results
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    failed += 1
                    failed_ids.append(str(match_ids[i]))
                    logger.error(f"Failed to delete match {match_ids[i]}: {result}")
                elif result:
                    successful += 1
                else:
                    failed += 1
                    failed_ids.append(str(match_ids[i]))
            
            duration = (datetime.now() - start_time).total_seconds()
            
            logger.info(
                f"Batch deletion completed: {successful} successful, {failed} failed "
                f"in {duration:.2f} seconds"
            )
            
            return {
                'successful_count': successful,
                'failed_count': failed,
                'failed_ids': failed_ids,
                'duration_seconds': duration
            }
            
        except Exception as e:
            logger.error(f"Error in batch deletion: {e}")
            return {
                'successful_count': successful,
                'failed_count': failed + (len(match_ids) - successful),
                'failed_ids': failed_ids,
                'error': str(e)
            }
    
    async def _process_creation_batch_concurrent(
        self,
        matches: List[MatchResultCreate],
        metadata_per_match: Optional[List[List[MatchMetadataCreate]]] = None
    ) -> List[Optional[MatchResultResponse]]:
        """Process a batch of match creations concurrently"""
        
        tasks = []
        for i, match in enumerate(matches):
            metadata = metadata_per_match[i] if metadata_per_match else None
            task = self._create_single_match_with_semaphore(match, metadata)
            tasks.append(task)
        
        # Wait for all tasks to complete
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Convert exceptions to None
        processed_results = []
        for result in results:
            if isinstance(result, Exception):
                logger.error(f"Match creation failed: {result}")
                processed_results.append(None)
            else:
                processed_results.append(result)
        
        return processed_results
    
    async def _process_update_batch_concurrent(
        self,
        updates: List[Dict[str, Any]]
    ) -> List[Optional[MatchResultResponse]]:
        """Process a batch of match updates concurrently"""
        
        tasks = []
        for update in updates:
            match_id = UUID(update['match_id'])
            update_data = update['updates']
            task = self._update_single_match_with_semaphore(match_id, update_data)
            tasks.append(task)
        
        # Wait for all tasks to complete
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Convert exceptions to None
        processed_results = []
        for result in results:
            if isinstance(result, Exception):
                logger.error(f"Match update failed: {result}")
                processed_results.append(None)
            else:
                processed_results.append(result)
        
        return processed_results
    
    async def _create_single_match_with_semaphore(
        self,
        match: MatchResultCreate,
        metadata: Optional[List[MatchMetadataCreate]] = None
    ) -> Optional[MatchResultResponse]:
        """Create a single match with semaphore control"""
        async with self.semaphore:
            try:
                return await self.db_matcher.create_match(match, metadata)
            except Exception as e:
                logger.error(f"Error creating match: {e}")
                return None
    
    async def _update_single_match_with_semaphore(
        self,
        match_id: UUID,
        update_data: Dict[str, Any]
    ) -> Optional[MatchResultResponse]:
        """Update a single match with semaphore control"""
        async with self.semaphore:
            try:
                return await self.db_matcher.update_match(match_id, update_data)
            except Exception as e:
                logger.error(f"Error updating match {match_id}: {e}")
                return None
    
    async def _delete_single_match_with_semaphore(
        self,
        match_id: UUID
    ) -> bool:
        """Delete a single match with semaphore control"""
        async with self.semaphore:
            try:
                return await self.db_matcher.delete_match(match_id)
            except Exception as e:
                logger.error(f"Error deleting match {match_id}: {e}")
                return False
    
    def validate_batch_size(self, batch_size: int) -> bool:
        """Validate batch size is within acceptable limits"""
        return 1 <= batch_size <= 1000
    
    def estimate_processing_time(
        self,
        batch_size: int,
        operation_type: str = 'create'
    ) -> Dict[str, float]:
        """
        Estimate processing time for a batch operation
        
        Args:
            batch_size: Size of the batch
            operation_type: Type of operation ('create', 'update', 'delete')
        
        Returns:
            Dictionary with time estimates
        """
        # Base time estimates per operation (seconds)
        base_times = {
            'create': 0.1,
            'update': 0.05,
            'delete': 0.03
        }
        
        base_time = base_times.get(operation_type, 0.1)
        
        # Account for concurrency
        concurrent_factor = min(self.max_concurrent, batch_size) / batch_size
        
        # Estimated times
        sequential_time = batch_size * base_time
        concurrent_time = sequential_time * concurrent_factor
        
        # Add overhead for batching and coordination
        overhead = batch_size * 0.01
        
        return {
            'sequential_estimate_seconds': sequential_time,
            'concurrent_estimate_seconds': concurrent_time + overhead,
            'overhead_seconds': overhead,
            'operations_per_second': self.max_concurrent / base_time
        }