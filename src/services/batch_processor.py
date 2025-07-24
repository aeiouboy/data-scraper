"""
Batch Processing Service for High-Performance Product Matching
Handles large-scale product matching operations efficiently
"""

import asyncio
import logging
import time
import threading
from typing import Dict, List, Optional, Any, Callable, Generator, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from collections import deque
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor, as_completed
import multiprocessing as mp
from queue import Queue, Empty
import json
import traceback

from src.services.advanced_product_matcher import AdvancedProductMatcher
from src.services.cache_manager import CacheManager
from src.services.database_optimizer import DatabaseOptimizer
from src.services.supabase_service import SupabaseService as SupabaseClient

logger = logging.getLogger(__name__)


@dataclass
class BatchJob:
    """Batch processing job definition"""
    job_id: str
    job_type: str  # 'product_matching', 'text_normalization', 'similarity_calculation'
    data: List[Any]
    parameters: Dict[str, Any] = field(default_factory=dict)
    priority: int = 0  # Higher values = higher priority
    created_at: datetime = field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    status: str = 'pending'  # 'pending', 'running', 'completed', 'failed'
    progress: float = 0.0
    results: List[Any] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    metrics: Dict[str, Any] = field(default_factory=dict)


@dataclass
class BatchConfig:
    """Batch processing configuration"""
    max_workers: int = 4
    max_queue_size: int = 1000
    batch_size: int = 100
    chunk_size: int = 10
    timeout_seconds: int = 300
    retry_attempts: int = 3
    use_process_pool: bool = False
    enable_caching: bool = True
    enable_progress_tracking: bool = True


@dataclass
class BatchStats:
    """Batch processing statistics"""
    total_jobs: int
    pending_jobs: int
    running_jobs: int
    completed_jobs: int
    failed_jobs: int
    avg_processing_time: float
    total_items_processed: int
    throughput_items_per_second: float
    queue_utilization: float
    worker_utilization: float


class BatchProcessor:
    """High-performance batch processor for product matching operations"""
    
    def __init__(self, config: BatchConfig = None, 
                 cache_manager: CacheManager = None,
                 db_client: SupabaseClient = None):
        """Initialize batch processor"""
        self.config = config or BatchConfig()
        self.cache_manager = cache_manager or CacheManager()
        self.db_client = db_client or SupabaseClient()
        
        # Job management
        self.job_queue = Queue(maxsize=self.config.max_queue_size)
        self.active_jobs = {}
        self.completed_jobs = deque(maxlen=1000)  # Keep last 1000 completed jobs
        
        # Worker management
        self.workers_running = False
        self.worker_threads = []
        self.executor = None
        
        # Statistics
        self.stats = {
            'jobs_submitted': 0,
            'jobs_completed': 0,
            'jobs_failed': 0,
            'total_processing_time': 0.0,
            'total_items_processed': 0,
            'start_time': time.time()
        }
        
        # Components
        self.matcher = AdvancedProductMatcher()
        self.db_optimizer = DatabaseOptimizer(self.db_client)
        
        # Job processors
        self.job_processors = {
            'product_matching': self._process_product_matching_batch,
            'text_normalization': self._process_text_normalization_batch,
            'similarity_calculation': self._process_similarity_calculation_batch,
            'database_batch_insert': self._process_database_batch_insert,
            'cache_warming': self._process_cache_warming_batch,
            'validation_batch': self._process_validation_batch
        }
    
    def start_workers(self):
        """Start worker threads"""
        if self.workers_running:
            return
        
        self.workers_running = True
        
        # Initialize executor
        if self.config.use_process_pool:
            self.executor = ProcessPoolExecutor(
                max_workers=self.config.max_workers,
                mp_context=mp.get_context('spawn')
            )
        else:
            self.executor = ThreadPoolExecutor(
                max_workers=self.config.max_workers
            )
        
        # Start worker threads
        for i in range(self.config.max_workers):
            worker_thread = threading.Thread(
                target=self._worker_loop,
                name=f"BatchWorker-{i}",
                daemon=True
            )
            worker_thread.start()
            self.worker_threads.append(worker_thread)
        
        logger.info(f"Started {self.config.max_workers} batch processing workers")
    
    def stop_workers(self):
        """Stop worker threads"""
        if not self.workers_running:
            return
        
        self.workers_running = False
        
        # Shutdown executor
        if self.executor:
            self.executor.shutdown(wait=True)
            self.executor = None
        
        # Wait for worker threads
        for thread in self.worker_threads:
            thread.join(timeout=5.0)
        
        self.worker_threads.clear()
        logger.info("Stopped batch processing workers")
    
    def submit_job(self, job_type: str, data: List[Any], 
                   parameters: Dict[str, Any] = None, priority: int = 0) -> str:
        """Submit a batch job for processing"""
        job_id = f"{job_type}_{int(time.time() * 1000)}_{len(data)}"
        
        job = BatchJob(
            job_id=job_id,
            job_type=job_type,
            data=data,
            parameters=parameters or {},
            priority=priority
        )
        
        try:
            self.job_queue.put(job, timeout=5.0)
            self.stats['jobs_submitted'] += 1
            logger.info(f"Submitted batch job {job_id} with {len(data)} items")
            return job_id
            
        except Exception as e:
            logger.error(f"Failed to submit batch job: {e}")
            return None
    
    def get_job_status(self, job_id: str) -> Optional[Dict[str, Any]]:
        """Get status of a batch job"""
        # Check active jobs
        if job_id in self.active_jobs:
            job = self.active_jobs[job_id]
            return {
                'job_id': job.job_id,
                'status': job.status,
                'progress': job.progress,
                'created_at': job.created_at.isoformat(),
                'started_at': job.started_at.isoformat() if job.started_at else None,
                'data_size': len(job.data),
                'results_count': len(job.results),
                'errors_count': len(job.errors),
                'metrics': job.metrics
            }
        
        # Check completed jobs
        for job in self.completed_jobs:
            if job.job_id == job_id:
                return {
                    'job_id': job.job_id,
                    'status': job.status,
                    'progress': job.progress,
                    'created_at': job.created_at.isoformat(),
                    'started_at': job.started_at.isoformat() if job.started_at else None,
                    'completed_at': job.completed_at.isoformat() if job.completed_at else None,
                    'data_size': len(job.data),
                    'results_count': len(job.results),
                    'errors_count': len(job.errors),
                    'metrics': job.metrics
                }
        
        return None
    
    def get_job_results(self, job_id: str) -> Optional[List[Any]]:
        """Get results of a completed batch job"""
        job_status = self.get_job_status(job_id)
        if not job_status or job_status['status'] != 'completed':
            return None
        
        # Find job in completed jobs
        for job in self.completed_jobs:
            if job.job_id == job_id:
                return job.results
        
        return None
    
    def _worker_loop(self):
        """Main worker loop"""
        while self.workers_running:
            try:
                # Get job from queue (with timeout)
                try:
                    job = self.job_queue.get(timeout=1.0)
                except Empty:
                    continue
                
                # Process job
                self._process_job(job)
                
            except Exception as e:
                logger.error(f"Worker loop error: {e}")
                traceback.print_exc()
    
    def _process_job(self, job: BatchJob):
        """Process a single batch job"""
        job.started_at = datetime.now()
        job.status = 'running'
        self.active_jobs[job.job_id] = job
        
        logger.info(f"Processing batch job {job.job_id} ({job.job_type})")
        
        try:
            # Get appropriate processor
            processor = self.job_processors.get(job.job_type)
            if not processor:
                raise ValueError(f"Unknown job type: {job.job_type}")
            
            # Process in chunks
            start_time = time.time()
            total_items = len(job.data)
            processed_items = 0
            
            # Split data into chunks
            chunks = self._split_into_chunks(job.data, self.config.chunk_size)
            
            for chunk_idx, chunk in enumerate(chunks):
                # Process chunk
                chunk_results = processor(chunk, job.parameters)
                job.results.extend(chunk_results)
                
                # Update progress
                processed_items += len(chunk)
                job.progress = processed_items / total_items
                
                # Update metrics
                elapsed_time = time.time() - start_time
                job.metrics.update({
                    'processed_items': processed_items,
                    'total_items': total_items,
                    'chunks_processed': chunk_idx + 1,
                    'total_chunks': len(chunks),
                    'elapsed_time': elapsed_time,
                    'items_per_second': processed_items / max(elapsed_time, 0.001)
                })
                
                if self.config.enable_progress_tracking:
                    logger.debug(f"Job {job.job_id}: {job.progress:.1%} complete "
                               f"({processed_items}/{total_items})")
            
            # Job completed successfully
            job.status = 'completed'
            job.completed_at = datetime.now()
            job.progress = 1.0
            
            # Update global statistics
            processing_time = time.time() - start_time
            self.stats['jobs_completed'] += 1
            self.stats['total_processing_time'] += processing_time
            self.stats['total_items_processed'] += total_items
            
            logger.info(f"Completed batch job {job.job_id} in {processing_time:.2f}s "
                       f"({total_items} items, {total_items/processing_time:.1f} items/s)")
            
        except Exception as e:
            # Job failed
            job.status = 'failed'
            job.completed_at = datetime.now()
            job.errors.append(str(e))
            
            self.stats['jobs_failed'] += 1
            logger.error(f"Batch job {job.job_id} failed: {e}")
            traceback.print_exc()
        
        finally:
            # Move job to completed queue
            self.completed_jobs.append(job)
            if job.job_id in self.active_jobs:
                del self.active_jobs[job.job_id]
    
    def _split_into_chunks(self, data: List[Any], chunk_size: int) -> List[List[Any]]:
        """Split data into chunks for processing"""
        chunks = []
        for i in range(0, len(data), chunk_size):
            chunks.append(data[i:i + chunk_size])
        return chunks
    
    def _process_product_matching_batch(self, data: List[Tuple[Dict, List[Dict]]], 
                                       parameters: Dict[str, Any]) -> List[Dict]:
        """Process batch of product matching operations"""
        results = []
        
        for source_product, target_products in data:
            try:
                # Find best matches for source product
                best_matches = []
                
                for target_product in target_products:
                    # Check cache first
                    cache_key = f"{source_product.get('id', '')}_{target_product.get('id', '')}"
                    
                    if self.config.enable_caching:
                        cached_result = self.cache_manager.get(
                            'product_matching', cache_key
                        )
                        if cached_result:
                            best_matches.append(cached_result)
                            continue
                    
                    # Calculate match
                    match_result = self.matcher.match_products(source_product, target_product)
                    
                    match_data = {
                        'source_product_id': source_product.get('id'),
                        'target_product_id': target_product.get('id'),
                        'confidence': match_result.confidence,
                        'details': match_result.details
                    }
                    
                    best_matches.append(match_data)
                    
                    # Cache result
                    if self.config.enable_caching:
                        self.cache_manager.put('product_matching', match_data, cache_key)
                
                # Sort by confidence and take top matches
                best_matches.sort(key=lambda x: x['confidence'], reverse=True)
                top_matches = best_matches[:parameters.get('max_matches', 5)]
                
                results.append({
                    'source_product_id': source_product.get('id'),
                    'matches': top_matches
                })
                
            except Exception as e:
                logger.error(f"Error matching product {source_product.get('id', 'unknown')}: {e}")
                results.append({
                    'source_product_id': source_product.get('id'),
                    'matches': [],
                    'error': str(e)
                })
        
        return results
    
    def _process_text_normalization_batch(self, data: List[str], 
                                         parameters: Dict[str, Any]) -> List[str]:
        """Process batch of text normalization operations"""
        from src.utils.text_normalizer_enhanced import EnhancedTextNormalizer
        
        normalizer = EnhancedTextNormalizer()
        results = []
        
        for text in data:
            try:
                # Check cache first
                if self.config.enable_caching:
                    cached_result = self.cache_manager.get('text_normalization', text)
                    if cached_result:
                        results.append(cached_result)
                        continue
                
                # Normalize text
                normalized = normalizer.normalize(text)
                results.append(normalized)
                
                # Cache result
                if self.config.enable_caching:
                    self.cache_manager.put('text_normalization', normalized, text)
                
            except Exception as e:
                logger.error(f"Error normalizing text '{text[:50]}...': {e}")
                results.append(text)  # Return original on error
        
        return results
    
    def _process_similarity_calculation_batch(self, data: List[Tuple[str, str]], 
                                            parameters: Dict[str, Any]) -> List[float]:
        """Process batch of similarity calculations"""
        from src.utils.fuzzy_matcher import FuzzyMatcher
        
        matcher = FuzzyMatcher()
        results = []
        
        for text1, text2 in data:
            try:
                # Check cache first
                cache_key = f"{text1}_{text2}"
                
                if self.config.enable_caching:
                    cached_result = self.cache_manager.get('fuzzy_matching', cache_key)
                    if cached_result:
                        results.append(cached_result)
                        continue
                
                # Calculate similarity
                similarity_result = matcher.calculate_similarity(text1, text2)
                similarity_score = similarity_result.similarity
                
                results.append(similarity_score)
                
                # Cache result
                if self.config.enable_caching:
                    self.cache_manager.put('fuzzy_matching', similarity_score, cache_key)
                
            except Exception as e:
                logger.error(f"Error calculating similarity: {e}")
                results.append(0.0)  # Return 0 similarity on error
        
        return results
    
    def _process_database_batch_insert(self, data: List[Dict], 
                                     parameters: Dict[str, Any]) -> List[str]:
        """Process batch database insertions"""
        table_name = parameters.get('table_name', 'products')
        
        try:
            if table_name == 'products':
                results = self.db_optimizer.batch_insert_products(
                    data, batch_size=parameters.get('batch_size', 1000)
                )
            elif table_name == 'product_matches':
                results = self.db_optimizer.batch_update_matches(
                    data, batch_size=parameters.get('batch_size', 500)
                )
            else:
                # Generic batch insert
                results = self.db_client.client.table(table_name).insert(data).execute()
                results = results.data if results.data else []
            
            return [item.get('id', '') for item in results]
            
        except Exception as e:
            logger.error(f"Batch database insert failed: {e}")
            return []
    
    def _process_cache_warming_batch(self, data: List[Dict], 
                                   parameters: Dict[str, Any]) -> List[bool]:
        """Process batch cache warming operations"""
        results = []
        category = parameters.get('category', 'product_matching')
        
        for item in data:
            try:
                cache_key = item.get('key')
                cache_value = item.get('value')
                
                if cache_key and cache_value:
                    self.cache_manager.put(category, cache_value, cache_key)
                    results.append(True)
                else:
                    results.append(False)
                    
            except Exception as e:
                logger.error(f"Cache warming error: {e}")
                results.append(False)
        
        return results
    
    def _process_validation_batch(self, data: List[Dict], 
                                parameters: Dict[str, Any]) -> List[Dict]:
        """Process batch validation operations"""
        from src.services.validation_pipeline import ValidationPipeline
        
        validator = ValidationPipeline()
        results = []
        
        for validation_item in data:
            try:
                # Validate single item
                result = validator.run_validation(
                    sample_size=validation_item.get('sample_size', 10),
                    validation_type=validation_item.get('type', 'quick')
                )
                
                results.append({
                    'validation_id': validation_item.get('id'),
                    'accuracy': result.accuracy,
                    'precision': result.precision,
                    'recall': result.recall,
                    'f1_score': result.f1_score
                })
                
            except Exception as e:
                logger.error(f"Validation error: {e}")
                results.append({
                    'validation_id': validation_item.get('id'),
                    'error': str(e)
                })
        
        return results
    
    def get_batch_stats(self) -> BatchStats:
        """Get comprehensive batch processing statistics"""
        uptime = time.time() - self.stats['start_time']
        
        # Calculate averages
        completed_jobs = self.stats['jobs_completed']
        avg_processing_time = (
            self.stats['total_processing_time'] / max(completed_jobs, 1)
        )
        
        throughput = self.stats['total_items_processed'] / max(uptime, 1)
        
        # Queue utilization
        queue_utilization = self.job_queue.qsize() / self.config.max_queue_size
        
        # Worker utilization (active jobs vs max workers)
        worker_utilization = len(self.active_jobs) / self.config.max_workers
        
        return BatchStats(
            total_jobs=self.stats['jobs_submitted'],
            pending_jobs=self.job_queue.qsize(),
            running_jobs=len(self.active_jobs),
            completed_jobs=self.stats['jobs_completed'],
            failed_jobs=self.stats['jobs_failed'],
            avg_processing_time=avg_processing_time,
            total_items_processed=self.stats['total_items_processed'],
            throughput_items_per_second=throughput,
            queue_utilization=queue_utilization,
            worker_utilization=worker_utilization
        )
    
    def optimize_configuration(self) -> Dict[str, Any]:
        """Analyze performance and suggest configuration optimizations"""
        stats = self.get_batch_stats()
        optimizations = []
        
        # Analyze queue utilization
        if stats.queue_utilization > 0.8:
            optimizations.append({
                'component': 'queue',
                'issue': 'high_queue_utilization',
                'current_value': stats.queue_utilization,
                'recommendation': 'Increase max_queue_size or add more workers'
            })
        
        # Analyze worker utilization
        if stats.worker_utilization > 0.9:
            optimizations.append({
                'component': 'workers',
                'issue': 'high_worker_utilization',
                'current_value': stats.worker_utilization,
                'recommendation': 'Increase max_workers'
            })
        elif stats.worker_utilization < 0.3:
            optimizations.append({
                'component': 'workers',
                'issue': 'low_worker_utilization',
                'current_value': stats.worker_utilization,
                'recommendation': 'Reduce max_workers to save resources'
            })
        
        # Analyze throughput
        if stats.throughput_items_per_second < 10:
            optimizations.append({
                'component': 'throughput',
                'issue': 'low_throughput',
                'current_value': stats.throughput_items_per_second,
                'recommendation': 'Increase chunk_size or optimize processing functions'
            })
        
        # Analyze average processing time
        if stats.avg_processing_time > 30:
            optimizations.append({
                'component': 'processing_time',
                'issue': 'slow_processing',
                'current_value': stats.avg_processing_time,
                'recommendation': 'Enable caching or reduce batch_size'
            })
        
        return {
            'analysis_timestamp': datetime.now().isoformat(),
            'current_stats': stats,
            'optimizations': optimizations,
            'recommendations_count': len(optimizations)
        }


# Example usage and testing
if __name__ == "__main__":
    # Test batch processor
    processor = BatchProcessor()
    
    print("⚡ Batch Processor Demo")
    print("=" * 50)
    
    # Start workers
    processor.start_workers()
    
    try:
        # Test text normalization batch
        text_data = [
            "MITSUBISHI แอร์ติดผนัง รุ่น MSY-KP13VF",
            "Samsung Smart TV 55 นิ้ว",
            "LG ตู้เย็น 300 ลิตร",
            "Panasonic เครื่องซักผ้า 8 กิโลกรัม"
        ]
        
        job_id = processor.submit_job('text_normalization', text_data)
        print(f"Submitted text normalization job: {job_id}")
        
        # Test similarity calculation batch
        similarity_data = [
            ("Samsung TV", "ซัมซุง ทีวี"),
            ("LG Refrigerator", "แอลจี ตู้เย็น"),
            ("Mitsubishi Air", "มิตซูบิชิ แอร์")
        ]
        
        similarity_job_id = processor.submit_job('similarity_calculation', similarity_data)
        print(f"Submitted similarity calculation job: {similarity_job_id}")
        
        # Wait for jobs to complete
        print("Waiting for jobs to complete...")
        time.sleep(5)
        
        # Check job status
        for job_id in [job_id, similarity_job_id]:
            if job_id:
                status = processor.get_job_status(job_id)
                if status:
                    print(f"\nJob {job_id}:")
                    print(f"  Status: {status['status']}")
                    print(f"  Progress: {status['progress']:.1%}")
                    print(f"  Results: {status['results_count']}")
                    print(f"  Metrics: {status['metrics']}")
                    
                    if status['status'] == 'completed':
                        results = processor.get_job_results(job_id)
                        print(f"  Sample result: {results[0] if results else 'None'}")
        
        # Get batch statistics
        stats = processor.get_batch_stats()
        print(f"\nBatch Processing Statistics:")
        print(f"  Total jobs: {stats.total_jobs}")
        print(f"  Completed: {stats.completed_jobs}")
        print(f"  Failed: {stats.failed_jobs}")
        print(f"  Avg processing time: {stats.avg_processing_time:.2f}s")
        print(f"  Throughput: {stats.throughput_items_per_second:.1f} items/s")
        print(f"  Queue utilization: {stats.queue_utilization:.1%}")
        print(f"  Worker utilization: {stats.worker_utilization:.1%}")
        
        # Get optimization recommendations
        optimization_report = processor.optimize_configuration()
        print(f"\nOptimization Recommendations: {optimization_report['recommendations_count']}")
        for opt in optimization_report['optimizations']:
            print(f"  {opt['component']}: {opt['issue']} - {opt['recommendation']}")
        
    finally:
        # Stop workers
        processor.stop_workers()
    
    print("\n✅ Batch processor demo completed")