"""
Redis caching configuration for matching performance optimization
"""
import os
import redis
import json
import logging
from typing import Any, Optional, Dict, List
from datetime import datetime, timedelta
from contextlib import contextmanager

logger = logging.getLogger(__name__)

# Redis connection settings
REDIS_URL = os.getenv('REDIS_URL', 'redis://localhost:6379/1')  # Use DB 1 for cache
REDIS_MAX_CONNECTIONS = int(os.getenv('REDIS_MAX_CONNECTIONS', '20'))

# Cache TTL settings (in seconds)
CACHE_TTL = {
    'match_results': 3600,      # 1 hour
    'product_matches': 1800,    # 30 minutes
    'confidence_scores': 7200,  # 2 hours
    'match_stats': 300,         # 5 minutes
    'product_details': 600,     # 10 minutes
    'algorithmic_matches': 1800, # 30 minutes
    'batch_operations': 60,     # 1 minute
}

# Cache key prefixes
CACHE_KEYS = {
    'match_results': 'match:result:',
    'product_matches': 'match:product:',
    'confidence_scores': 'match:confidence:',
    'match_stats': 'match:stats',
    'product_details': 'product:details:',
    'algorithmic_matches': 'match:algo:',
    'batch_status': 'batch:status:',
}


class CacheManager:
    """Redis cache manager for matching operations"""
    
    def __init__(self):
        self.connection_pool = redis.ConnectionPool.from_url(
            REDIS_URL,
            max_connections=REDIS_MAX_CONNECTIONS,
            decode_responses=True
        )
        self.redis_client = redis.Redis(connection_pool=self.connection_pool)
        
    @contextmanager
    def get_client(self):
        """Context manager for Redis client"""
        try:
            yield self.redis_client
        except redis.ConnectionError as e:
            logger.error(f"Redis connection error: {e}")
            raise
        except Exception as e:
            logger.error(f"Redis operation error: {e}")
            raise
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache with JSON deserialization"""
        try:
            with self.get_client() as client:
                value = client.get(key)
                if value:
                    return json.loads(value)
                return None
        except Exception as e:
            logger.error(f"Cache get error for key {key}: {e}")
            return None
    
    def set(
        self,
        key: str,
        value: Any,
        ttl: Optional[int] = None,
        nx: bool = False
    ) -> bool:
        """Set value in cache with JSON serialization"""
        try:
            with self.get_client() as client:
                serialized_value = json.dumps(value, default=str)
                return client.set(key, serialized_value, ex=ttl, nx=nx)
        except Exception as e:
            logger.error(f"Cache set error for key {key}: {e}")
            return False
    
    def delete(self, *keys: str) -> int:
        """Delete keys from cache"""
        try:
            with self.get_client() as client:
                return client.delete(*keys)
        except Exception as e:
            logger.error(f"Cache delete error: {e}")
            return 0
    
    def exists(self, key: str) -> bool:
        """Check if key exists in cache"""
        try:
            with self.get_client() as client:
                return client.exists(key) > 0
        except Exception as e:
            logger.error(f"Cache exists error for key {key}: {e}")
            return False
    
    def invalidate_pattern(self, pattern: str) -> int:
        """Invalidate all keys matching pattern"""
        try:
            with self.get_client() as client:
                keys = client.keys(pattern)
                if keys:
                    return client.delete(*keys)
                return 0
        except Exception as e:
            logger.error(f"Cache invalidate pattern error for {pattern}: {e}")
            return 0
    
    def get_cache_info(self) -> Dict[str, Any]:
        """Get cache statistics"""
        try:
            with self.get_client() as client:
                info = client.info()
                return {
                    'connected_clients': info.get('connected_clients', 0),
                    'used_memory_human': info.get('used_memory_human', 'unknown'),
                    'keyspace_hits': info.get('keyspace_hits', 0),
                    'keyspace_misses': info.get('keyspace_misses', 0),
                    'hit_rate': self._calculate_hit_rate(info),
                    'total_keys': self._count_total_keys(client),
                    'cache_prefixes': list(CACHE_KEYS.keys())
                }
        except Exception as e:
            logger.error(f"Error getting cache info: {e}")
            return {'error': str(e)}
    
    def _calculate_hit_rate(self, info: Dict) -> float:
        """Calculate cache hit rate"""
        hits = info.get('keyspace_hits', 0)
        misses = info.get('keyspace_misses', 0)
        total = hits + misses
        return round(hits / total * 100, 2) if total > 0 else 0.0
    
    def _count_total_keys(self, client) -> int:
        """Count total keys in cache"""
        try:
            db_info = client.info('keyspace')
            db_key = f'db{client.connection_pool.connection_kwargs.get("db", 0)}'
            if db_key in db_info:
                return db_info[db_key]['keys']
            return 0
        except Exception:
            return 0


class MatchingCache:
    """Specialized cache for matching operations"""
    
    def __init__(self):
        self.cache = CacheManager()
    
    def get_product_matches(self, product_id: str) -> Optional[List[Dict[str, Any]]]:
        """Get cached product matches"""
        key = f"{CACHE_KEYS['product_matches']}{product_id}"
        return self.cache.get(key)
    
    def set_product_matches(
        self,
        product_id: str,
        matches: List[Dict[str, Any]],
        ttl: Optional[int] = None
    ) -> bool:
        """Cache product matches"""
        key = f"{CACHE_KEYS['product_matches']}{product_id}"
        ttl = ttl or CACHE_TTL['product_matches']
        return self.cache.set(key, matches, ttl)
    
    def get_match_result(self, match_id: str) -> Optional[Dict[str, Any]]:
        """Get cached match result"""
        key = f"{CACHE_KEYS['match_results']}{match_id}"
        return self.cache.get(key)
    
    def set_match_result(
        self,
        match_id: str,
        match_data: Dict[str, Any],
        ttl: Optional[int] = None
    ) -> bool:
        """Cache match result"""
        key = f"{CACHE_KEYS['match_results']}{match_id}"
        ttl = ttl or CACHE_TTL['match_results']
        return self.cache.set(key, match_data, ttl)
    
    def get_confidence_score(
        self,
        source_id: str,
        target_id: str
    ) -> Optional[Dict[str, Any]]:
        """Get cached confidence score"""
        key = f"{CACHE_KEYS['confidence_scores']}{source_id}:{target_id}"
        return self.cache.get(key)
    
    def set_confidence_score(
        self,
        source_id: str,
        target_id: str,
        score_data: Dict[str, Any],
        ttl: Optional[int] = None
    ) -> bool:
        """Cache confidence score"""
        key = f"{CACHE_KEYS['confidence_scores']}{source_id}:{target_id}"
        ttl = ttl or CACHE_TTL['confidence_scores']
        return self.cache.set(key, score_data, ttl)
    
    def get_match_stats(self) -> Optional[Dict[str, Any]]:
        """Get cached match statistics"""
        key = CACHE_KEYS['match_stats']
        return self.cache.get(key)
    
    def set_match_stats(
        self,
        stats: Dict[str, Any],
        ttl: Optional[int] = None
    ) -> bool:
        """Cache match statistics"""
        key = CACHE_KEYS['match_stats']
        ttl = ttl or CACHE_TTL['match_stats']
        return self.cache.set(key, stats, ttl)
    
    def get_product_details(self, product_id: str) -> Optional[Dict[str, Any]]:
        """Get cached product details"""
        key = f"{CACHE_KEYS['product_details']}{product_id}"
        return self.cache.get(key)
    
    def set_product_details(
        self,
        product_id: str,
        product_data: Dict[str, Any],
        ttl: Optional[int] = None
    ) -> bool:
        """Cache product details"""
        key = f"{CACHE_KEYS['product_details']}{product_id}"
        ttl = ttl or CACHE_TTL['product_details']
        return self.cache.set(key, product_data, ttl)
    
    def invalidate_product_matches(self, product_id: str) -> int:
        """Invalidate all cached matches for a product"""
        patterns = [
            f"{CACHE_KEYS['product_matches']}{product_id}",
            f"{CACHE_KEYS['confidence_scores']}{product_id}:*",
            f"{CACHE_KEYS['confidence_scores']}*:{product_id}",
            f"{CACHE_KEYS['algorithmic_matches']}{product_id}"
        ]
        
        total_deleted = 0
        for pattern in patterns:
            total_deleted += self.cache.invalidate_pattern(pattern)
        
        return total_deleted
    
    def invalidate_match_stats(self) -> bool:
        """Invalidate cached match statistics"""
        return self.cache.delete(CACHE_KEYS['match_stats']) > 0
    
    def warm_cache_for_product(self, product_id: str) -> Dict[str, bool]:
        """Pre-warm cache for a product (to be called during off-peak hours)"""
        # This would be implemented to pre-load commonly accessed data
        # For now, just return a placeholder
        return {
            'product_matches': False,
            'product_details': False,
            'confidence_scores': False
        }
    
    def get_cache_status(self) -> Dict[str, Any]:
        """Get cache status and statistics"""
        cache_info = self.cache.get_cache_info()
        
        # Count keys by prefix
        key_counts = {}
        try:
            with self.cache.get_client() as client:
                for prefix_name, prefix in CACHE_KEYS.items():
                    keys = client.keys(f"{prefix}*")
                    key_counts[prefix_name] = len(keys)
        except Exception as e:
            logger.error(f"Error counting cache keys: {e}")
            key_counts = {k: 0 for k in CACHE_KEYS.keys()}
        
        cache_info['key_counts_by_type'] = key_counts
        cache_info['ttl_settings'] = CACHE_TTL
        
        return cache_info


# Global cache instance
matching_cache = MatchingCache()


def get_matching_cache() -> MatchingCache:
    """Get global matching cache instance"""
    return matching_cache


def clear_all_matching_cache() -> Dict[str, int]:
    """Clear all matching-related cache entries"""
    deleted_counts = {}
    
    for prefix_name, prefix in CACHE_KEYS.items():
        pattern = f"{prefix}*"
        deleted = matching_cache.cache.invalidate_pattern(pattern)
        deleted_counts[prefix_name] = deleted
    
    return deleted_counts


def health_check() -> Dict[str, Any]:
    """Health check for cache system"""
    try:
        # Test basic operations
        test_key = "health_check_test"
        test_value = {"timestamp": datetime.now().isoformat()}
        
        # Test set
        set_success = matching_cache.cache.set(test_key, test_value, 10)
        
        # Test get
        retrieved_value = matching_cache.cache.get(test_key)
        get_success = retrieved_value == test_value
        
        # Test delete
        delete_success = matching_cache.cache.delete(test_key) > 0
        
        return {
            'status': 'healthy' if all([set_success, get_success, delete_success]) else 'unhealthy',
            'operations': {
                'set': set_success,
                'get': get_success,
                'delete': delete_success
            },
            'cache_info': matching_cache.get_cache_status()
        }
        
    except Exception as e:
        return {
            'status': 'unhealthy',
            'error': str(e)
        }