"""
Comprehensive Caching Manager for Product Matching
Implements multi-level caching for optimal performance
"""

import json
import time
import logging
import hashlib
import pickle
from typing import Dict, List, Optional, Any, Union, Callable
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from collections import OrderedDict, defaultdict
from functools import wraps
import threading
from pathlib import Path
import redis
import os

logger = logging.getLogger(__name__)


@dataclass
class CacheEntry:
    """Cache entry with metadata"""
    key: str
    value: Any
    created_at: datetime
    last_accessed: datetime
    access_count: int
    expiry: Optional[datetime]
    size_bytes: int
    tags: List[str]


@dataclass
class CacheStats:
    """Cache performance statistics"""
    total_requests: int
    cache_hits: int
    cache_misses: int
    hit_rate: float
    total_size_bytes: int
    entry_count: int
    avg_access_time: float
    memory_usage_mb: float


class LRUCache:
    """Thread-safe LRU cache implementation"""
    
    def __init__(self, max_size: int = 1000, ttl_seconds: Optional[int] = None):
        self.max_size = max_size
        self.ttl_seconds = ttl_seconds
        self.cache = OrderedDict()
        self.stats = {'hits': 0, 'misses': 0, 'evictions': 0}
        self._lock = threading.RLock()
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        with self._lock:
            if key not in self.cache:
                self.stats['misses'] += 1
                return None
            
            entry = self.cache[key]
            
            # Check expiry
            if entry.expiry and datetime.now() > entry.expiry:
                del self.cache[key]
                self.stats['misses'] += 1
                return None
            
            # Move to end (most recently used)
            self.cache.move_to_end(key)
            entry.last_accessed = datetime.now()
            entry.access_count += 1
            
            self.stats['hits'] += 1
            return entry.value
    
    def put(self, key: str, value: Any, tags: List[str] = None) -> None:
        """Put value in cache"""
        with self._lock:
            now = datetime.now()
            expiry = now + timedelta(seconds=self.ttl_seconds) if self.ttl_seconds else None
            
            # Calculate size (approximate)
            try:
                size_bytes = len(pickle.dumps(value))
            except:
                size_bytes = len(str(value).encode('utf-8'))
            
            entry = CacheEntry(
                key=key,
                value=value,
                created_at=now,
                last_accessed=now,
                access_count=1,
                expiry=expiry,
                size_bytes=size_bytes,
                tags=tags or []
            )
            
            # Add to cache
            self.cache[key] = entry
            
            # Evict if necessary
            while len(self.cache) > self.max_size:
                # Remove least recently used
                oldest_key = next(iter(self.cache))
                del self.cache[oldest_key]
                self.stats['evictions'] += 1
    
    def delete(self, key: str) -> bool:
        """Delete key from cache"""
        with self._lock:
            if key in self.cache:
                del self.cache[key]
                return True
            return False
    
    def clear(self) -> None:
        """Clear all cache entries"""
        with self._lock:
            self.cache.clear()
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        with self._lock:
            total_requests = self.stats['hits'] + self.stats['misses']
            hit_rate = self.stats['hits'] / max(total_requests, 1)
            
            total_size = sum(entry.size_bytes for entry in self.cache.values())
            
            return {
                'hits': self.stats['hits'],
                'misses': self.stats['misses'],
                'evictions': self.stats['evictions'],
                'hit_rate': hit_rate,
                'size': len(self.cache),
                'total_size_bytes': total_size,
                'memory_usage_mb': total_size / (1024 * 1024)
            }


class RedisCache:
    """Redis-based distributed cache"""
    
    def __init__(self, host: str = 'localhost', port: int = 6379, 
                 db: int = 0, password: str = None, key_prefix: str = 'ris_cache:'):
        self.key_prefix = key_prefix
        self.stats = {'hits': 0, 'misses': 0}
        
        try:
            self.redis_client = redis.Redis(
                host=host, 
                port=port, 
                db=db, 
                password=password,
                decode_responses=False,  # We'll handle encoding ourselves
                socket_timeout=5.0,
                socket_connect_timeout=5.0
            )
            # Test connection
            self.redis_client.ping()
            self.available = True
            logger.info(f"Redis cache connected to {host}:{port}")
        except Exception as e:
            logger.warning(f"Redis not available: {e}")
            self.redis_client = None
            self.available = False
    
    def _make_key(self, key: str) -> str:
        """Make Redis key with prefix"""
        return f"{self.key_prefix}{key}"
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from Redis cache"""
        if not self.available:
            return None
        
        try:
            redis_key = self._make_key(key)
            data = self.redis_client.get(redis_key)
            
            if data is None:
                self.stats['misses'] += 1
                return None
            
            # Deserialize
            value = pickle.loads(data)
            self.stats['hits'] += 1
            return value
            
        except Exception as e:
            logger.error(f"Redis get error: {e}")
            self.stats['misses'] += 1
            return None
    
    def put(self, key: str, value: Any, ttl_seconds: Optional[int] = None) -> None:
        """Put value in Redis cache"""
        if not self.available:
            return
        
        try:
            redis_key = self._make_key(key)
            data = pickle.dumps(value)
            
            if ttl_seconds:
                self.redis_client.setex(redis_key, ttl_seconds, data)
            else:
                self.redis_client.set(redis_key, data)
                
        except Exception as e:
            logger.error(f"Redis put error: {e}")
    
    def delete(self, key: str) -> bool:
        """Delete key from Redis cache"""
        if not self.available:
            return False
        
        try:
            redis_key = self._make_key(key)
            return bool(self.redis_client.delete(redis_key))
        except Exception as e:
            logger.error(f"Redis delete error: {e}")
            return False
    
    def clear_pattern(self, pattern: str) -> int:
        """Clear keys matching pattern"""
        if not self.available:
            return 0
        
        try:
            redis_pattern = self._make_key(pattern)
            keys = self.redis_client.keys(redis_pattern)
            if keys:
                return self.redis_client.delete(*keys)
            return 0
        except Exception as e:
            logger.error(f"Redis clear pattern error: {e}")
            return 0
    
    def get_stats(self) -> Dict[str, Any]:
        """Get Redis cache statistics"""
        stats = {
            'hits': self.stats['hits'],
            'misses': self.stats['misses'],
            'available': self.available
        }
        
        if self.available:
            try:
                info = self.redis_client.info('memory')
                stats.update({
                    'memory_usage_bytes': info.get('used_memory', 0),
                    'memory_usage_mb': info.get('used_memory', 0) / (1024 * 1024),
                    'connected_clients': self.redis_client.info('clients').get('connected_clients', 0)
                })
            except Exception as e:
                logger.error(f"Redis stats error: {e}")
        
        return stats


class CacheManager:
    """Multi-level cache manager for product matching"""
    
    def __init__(self, config: Dict[str, Any] = None):
        """Initialize cache manager"""
        self.config = config or self._default_config()
        
        # Initialize cache layers
        self.l1_cache = LRUCache(
            max_size=self.config['l1_cache']['max_size'],
            ttl_seconds=self.config['l1_cache']['ttl_seconds']
        )
        
        self.l2_cache = RedisCache(
            host=self.config['redis']['host'],
            port=self.config['redis']['port'],
            db=self.config['redis']['db'],
            password=self.config['redis'].get('password'),
            key_prefix=self.config['redis']['key_prefix']
        )
        
        # Cache categories for different use cases
        self.cache_categories = {
            'text_normalization': {'ttl': 3600, 'level': 'l1'},      # 1 hour
            'fuzzy_matching': {'ttl': 1800, 'level': 'l1'},         # 30 minutes
            'semantic_similarity': {'ttl': 3600, 'level': 'l2'},     # 1 hour, distributed
            'product_matching': {'ttl': 900, 'level': 'l2'},        # 15 minutes, distributed
            'database_queries': {'ttl': 300, 'level': 'l2'},        # 5 minutes, distributed
            'brand_normalization': {'ttl': 7200, 'level': 'l1'},    # 2 hours
            'sku_extraction': {'ttl': 3600, 'level': 'l1'},         # 1 hour
            'confidence_calculation': {'ttl': 600, 'level': 'l1'},   # 10 minutes
        }
        
        # Statistics
        self.stats = defaultdict(int)
        self._start_time = time.time()
    
    def _default_config(self) -> Dict[str, Any]:
        """Default cache configuration"""
        return {
            'l1_cache': {
                'max_size': 10000,
                'ttl_seconds': 3600
            },
            'redis': {
                'host': os.getenv('REDIS_HOST', 'localhost'),
                'port': int(os.getenv('REDIS_PORT', '6379')),
                'db': int(os.getenv('REDIS_DB', '0')),
                'password': os.getenv('REDIS_PASSWORD'),
                'key_prefix': 'ris_cache:'
            },
            'persistence': {
                'enabled': True,
                'directory': 'cache_data',
                'max_file_size_mb': 100
            }
        }
    
    def _make_cache_key(self, category: str, *args, **kwargs) -> str:
        """Generate cache key"""
        # Create deterministic key from arguments
        key_data = {
            'category': category,
            'args': args,
            'kwargs': sorted(kwargs.items()) if kwargs else None
        }
        
        key_string = json.dumps(key_data, sort_keys=True, default=str)
        key_hash = hashlib.md5(key_string.encode()).hexdigest()
        
        return f"{category}:{key_hash[:16]}"
    
    def get(self, category: str, *args, **kwargs) -> Optional[Any]:
        """Get value from appropriate cache layer"""
        cache_key = self._make_cache_key(category, *args, **kwargs)
        cache_config = self.cache_categories.get(category, {'level': 'l1'})
        
        # Try L1 cache first
        value = self.l1_cache.get(cache_key)
        if value is not None:
            self.stats[f'{category}_l1_hits'] += 1
            return value
        
        # Try L2 cache if configured
        if cache_config['level'] == 'l2':
            value = self.l2_cache.get(cache_key)
            if value is not None:
                # Populate L1 cache
                self.l1_cache.put(cache_key, value)
                self.stats[f'{category}_l2_hits'] += 1
                return value
        
        self.stats[f'{category}_misses'] += 1
        return None
    
    def put(self, category: str, value: Any, *args, **kwargs) -> None:
        """Put value in appropriate cache layer"""
        cache_key = self._make_cache_key(category, *args, **kwargs)
        cache_config = self.cache_categories.get(category, {'level': 'l1', 'ttl': 3600})
        
        # Always put in L1 cache
        self.l1_cache.put(cache_key, value)
        
        # Put in L2 cache if configured
        if cache_config['level'] == 'l2':
            self.l2_cache.put(cache_key, value, cache_config.get('ttl'))
        
        self.stats[f'{category}_puts'] += 1
    
    def delete(self, category: str, *args, **kwargs) -> None:
        """Delete value from all cache layers"""
        cache_key = self._make_cache_key(category, *args, **kwargs)
        
        self.l1_cache.delete(cache_key)
        self.l2_cache.delete(cache_key)
        
        self.stats[f'{category}_deletes'] += 1
    
    def invalidate_category(self, category: str) -> None:
        """Invalidate all entries in a category"""
        # For L2 cache (Redis), use pattern matching
        pattern = f"{category}:*"
        cleared_count = self.l2_cache.clear_pattern(pattern)
        
        # For L1 cache, we'd need to iterate (expensive)
        # In practice, categories would have TTL
        
        logger.info(f"Invalidated {cleared_count} entries for category {category}")
        self.stats[f'{category}_invalidations'] += 1
    
    def cache_function(self, category: str, ttl_seconds: Optional[int] = None):
        """Decorator to cache function results"""
        def decorator(func: Callable) -> Callable:
            @wraps(func)
            def wrapper(*args, **kwargs):
                # Check cache first
                cached_result = self.get(category, func.__name__, *args, **kwargs)
                if cached_result is not None:
                    return cached_result
                
                # Execute function
                start_time = time.perf_counter()
                result = func(*args, **kwargs)
                execution_time = time.perf_counter() - start_time
                
                # Cache result
                self.put(category, result, func.__name__, *args, **kwargs)
                
                # Log performance
                self.stats[f'{category}_function_calls'] += 1
                self.stats[f'{category}_total_time'] += execution_time
                
                return result
            
            return wrapper
        return decorator
    
    def get_comprehensive_stats(self) -> CacheStats:
        """Get comprehensive cache statistics"""
        l1_stats = self.l1_cache.get_stats()
        l2_stats = self.l2_cache.get_stats()
        
        # Calculate totals
        total_hits = l1_stats['hits'] + l2_stats['hits']
        total_misses = l1_stats['misses'] + l2_stats['misses']
        total_requests = total_hits + total_misses
        
        hit_rate = total_hits / max(total_requests, 1)
        
        # Calculate average access time
        total_function_time = sum(
            self.stats[key] for key in self.stats 
            if key.endswith('_total_time')
        )
        total_function_calls = sum(
            self.stats[key] for key in self.stats 
            if key.endswith('_function_calls')
        )
        avg_access_time = total_function_time / max(total_function_calls, 1)
        
        return CacheStats(
            total_requests=total_requests,
            cache_hits=total_hits,
            cache_misses=total_misses,
            hit_rate=hit_rate,
            total_size_bytes=l1_stats['total_size_bytes'] + l2_stats.get('memory_usage_bytes', 0),
            entry_count=l1_stats['size'],
            avg_access_time=avg_access_time,
            memory_usage_mb=l1_stats['memory_usage_mb'] + l2_stats.get('memory_usage_mb', 0)
        )
    
    def get_detailed_stats(self) -> Dict[str, Any]:
        """Get detailed statistics breakdown"""
        uptime = time.time() - self._start_time
        
        # Category-specific stats
        category_stats = {}
        for category in self.cache_categories.keys():
            hits = self.stats.get(f'{category}_l1_hits', 0) + self.stats.get(f'{category}_l2_hits', 0)
            misses = self.stats.get(f'{category}_misses', 0)
            total = hits + misses
            
            category_stats[category] = {
                'hits': hits,
                'misses': misses,
                'hit_rate': hits / max(total, 1),
                'puts': self.stats.get(f'{category}_puts', 0),
                'deletes': self.stats.get(f'{category}_deletes', 0),
                'function_calls': self.stats.get(f'{category}_function_calls', 0),
                'avg_time': (
                    self.stats.get(f'{category}_total_time', 0) / 
                    max(self.stats.get(f'{category}_function_calls', 1), 1)
                )
            }
        
        return {
            'uptime_seconds': uptime,
            'l1_cache': self.l1_cache.get_stats(),
            'l2_cache': self.l2_cache.get_stats(),
            'categories': category_stats,
            'overall': asdict(self.get_comprehensive_stats())
        }
    
    def warm_up_cache(self, warm_up_data: Dict[str, List[Dict]] = None):
        """Warm up cache with common data"""
        if not warm_up_data:
            return
        
        logger.info("Starting cache warm-up")
        
        for category, data_items in warm_up_data.items():
            for item in data_items:
                # Simulate putting common queries in cache
                self.put(category, item.get('result'), **item.get('params', {}))
        
        logger.info(f"Cache warm-up completed for {len(warm_up_data)} categories")
    
    def clear_all_caches(self):
        """Clear all cache layers"""
        self.l1_cache.clear()
        
        # Clear Redis cache with pattern
        for category in self.cache_categories.keys():
            self.l2_cache.clear_pattern(f"{category}:*")
        
        # Reset statistics
        self.stats.clear()
        self._start_time = time.time()
        
        logger.info("All caches cleared")
    
    def optimize_cache_configuration(self) -> Dict[str, Any]:
        """Analyze usage patterns and suggest cache optimizations"""
        stats = self.get_detailed_stats()
        optimizations = []
        
        # Analyze hit rates by category
        for category, cat_stats in stats['categories'].items():
            hit_rate = cat_stats['hit_rate']
            
            if hit_rate < 0.5:
                optimizations.append({
                    'category': category,
                    'issue': 'low_hit_rate',
                    'current_hit_rate': hit_rate,
                    'recommendation': 'Increase TTL or cache size for this category'
                })
            elif hit_rate > 0.95:
                optimizations.append({
                    'category': category,
                    'issue': 'potentially_over_cached',
                    'current_hit_rate': hit_rate,
                    'recommendation': 'Consider reducing TTL to save memory'
                })
        
        # Analyze memory usage
        total_memory = stats['overall']['memory_usage_mb']
        if total_memory > 512:  # 512MB threshold
            optimizations.append({
                'category': 'memory',
                'issue': 'high_memory_usage',
                'current_memory_mb': total_memory,
                'recommendation': 'Consider reducing cache sizes or TTLs'
            })
        
        # Analyze average access time
        overall_avg_time = stats['overall']['avg_access_time']
        if overall_avg_time > 0.01:  # 10ms threshold
            optimizations.append({
                'category': 'performance',
                'issue': 'slow_cache_access',
                'current_avg_time': overall_avg_time,
                'recommendation': 'Consider optimizing cache key generation or serialization'
            })
        
        return {
            'analysis_timestamp': datetime.now().isoformat(),
            'current_stats': stats,
            'optimizations': optimizations,
            'recommendations_count': len(optimizations)
        }


# Example usage and testing
if __name__ == "__main__":
    # Test cache manager
    cache_manager = CacheManager()
    
    print("💾 Cache Manager Demo")
    print("=" * 50)
    
    # Test caching decorator
    @cache_manager.cache_function('text_normalization')
    def normalize_text(text: str) -> str:
        """Dummy text normalization function"""
        time.sleep(0.01)  # Simulate processing time
        return text.lower().strip()
    
    @cache_manager.cache_function('fuzzy_matching')
    def calculate_similarity(text1: str, text2: str) -> float:
        """Dummy similarity calculation"""
        time.sleep(0.02)  # Simulate processing time
        return len(set(text1) & set(text2)) / len(set(text1) | set(text2))
    
    # Test cached functions
    print("Testing cached functions...")
    
    # First calls (cache misses)
    start_time = time.time()
    result1 = normalize_text("  Hello World  ")
    result2 = calculate_similarity("hello", "world")
    first_time = time.time() - start_time
    
    # Second calls (cache hits)
    start_time = time.time()
    result1_cached = normalize_text("  Hello World  ")
    result2_cached = calculate_similarity("hello", "world")
    second_time = time.time() - start_time
    
    print(f"  First calls (cache miss): {first_time:.4f}s")
    print(f"  Second calls (cache hit): {second_time:.4f}s")
    print(f"  Speedup: {first_time / max(second_time, 0.0001):.1f}x")
    
    # Test manual caching
    print("\nTesting manual cache operations...")
    
    cache_manager.put('product_matching', {'confidence': 0.85}, 'product1', 'product2')
    cached_match = cache_manager.get('product_matching', 'product1', 'product2')
    
    print(f"  Cached match result: {cached_match}")
    
    # Get comprehensive statistics
    stats = cache_manager.get_comprehensive_stats()
    
    print(f"\nCache Statistics:")
    print(f"  Total requests: {stats.total_requests}")
    print(f"  Cache hits: {stats.cache_hits}")
    print(f"  Cache misses: {stats.cache_misses}")
    print(f"  Hit rate: {stats.hit_rate:.1%}")
    print(f"  Memory usage: {stats.memory_usage_mb:.2f} MB")
    print(f"  Average access time: {stats.avg_access_time:.4f}s")
    
    # Get detailed stats
    detailed_stats = cache_manager.get_detailed_stats()
    
    print(f"\nDetailed Statistics:")
    print(f"  L1 Cache hit rate: {detailed_stats['l1_cache']['hit_rate']:.1%}")
    print(f"  L2 Cache available: {detailed_stats['l2_cache']['available']}")
    
    for category, cat_stats in detailed_stats['categories'].items():
        if cat_stats['hits'] > 0 or cat_stats['misses'] > 0:
            print(f"  {category}: {cat_stats['hit_rate']:.1%} hit rate "
                  f"({cat_stats['hits']} hits, {cat_stats['misses']} misses)")
    
    # Test optimization analysis
    print(f"\nCache Optimization Analysis:")
    optimization_report = cache_manager.optimize_cache_configuration()
    
    print(f"  Recommendations: {optimization_report['recommendations_count']}")
    for opt in optimization_report['optimizations']:
        print(f"    {opt['category']}: {opt['issue']} - {opt['recommendation']}")
    
    print("\n✅ Cache manager demo completed")