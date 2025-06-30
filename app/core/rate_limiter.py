"""
Rate limiting and request queuing for concurrent scrapers
"""
import asyncio
import time
import logging
from typing import Dict, Optional, Callable, Any
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from collections import defaultdict, deque
from contextlib import asynccontextmanager

logger = logging.getLogger(__name__)


@dataclass
class RateLimitConfig:
    """Configuration for rate limiting"""
    requests_per_second: float = 1.0
    requests_per_minute: int = 30
    requests_per_hour: int = 1000
    burst_size: int = 5
    cooldown_seconds: float = 1.0


@dataclass
class RequestStats:
    """Statistics for rate limiter"""
    total_requests: int = 0
    successful_requests: int = 0
    throttled_requests: int = 0
    failed_requests: int = 0
    total_wait_time: float = 0.0
    last_request_time: Optional[float] = None
    
    def get_success_rate(self) -> float:
        """Calculate success rate"""
        if self.total_requests == 0:
            return 0.0
        return self.successful_requests / self.total_requests * 100


class TokenBucket:
    """Token bucket implementation for rate limiting"""
    
    def __init__(self, rate: float, capacity: int):
        """
        Initialize token bucket
        
        Args:
            rate: Tokens per second
            capacity: Maximum bucket capacity
        """
        self.rate = rate
        self.capacity = capacity
        self.tokens = capacity
        self.last_update = time.time()
        self._lock = asyncio.Lock()
    
    async def acquire(self, tokens: int = 1) -> float:
        """
        Acquire tokens from bucket
        
        Args:
            tokens: Number of tokens to acquire
            
        Returns:
            Wait time in seconds (0 if tokens available)
        """
        async with self._lock:
            now = time.time()
            
            # Add tokens based on time elapsed
            elapsed = now - self.last_update
            self.tokens = min(self.capacity, self.tokens + elapsed * self.rate)
            self.last_update = now
            
            if self.tokens >= tokens:
                # Tokens available
                self.tokens -= tokens
                return 0.0
            else:
                # Calculate wait time
                deficit = tokens - self.tokens
                wait_time = deficit / self.rate
                return wait_time
    
    def reset(self):
        """Reset bucket to full capacity"""
        self.tokens = self.capacity
        self.last_update = time.time()


class RateLimiter:
    """
    Advanced rate limiter with multiple strategies
    Supports per-retailer, per-domain, and global limits
    """
    
    def __init__(self, global_config: Optional[RateLimitConfig] = None):
        """Initialize rate limiter"""
        self.global_config = global_config or RateLimitConfig()
        self.retailer_configs: Dict[str, RateLimitConfig] = {}
        self.domain_configs: Dict[str, RateLimitConfig] = {}
        
        # Token buckets for different scopes
        self.global_bucket = TokenBucket(
            self.global_config.requests_per_second,
            self.global_config.burst_size
        )
        self.retailer_buckets: Dict[str, TokenBucket] = {}
        self.domain_buckets: Dict[str, TokenBucket] = {}
        
        # Request history for time-window limits
        self.request_history: Dict[str, deque] = defaultdict(lambda: deque())
        
        # Statistics
        self.stats: Dict[str, RequestStats] = defaultdict(RequestStats)
        
        # Semaphores for concurrent limits
        self.concurrent_limits: Dict[str, asyncio.Semaphore] = {}
    
    def configure_retailer(self, retailer_code: str, config: RateLimitConfig):
        """Configure rate limits for a specific retailer"""
        self.retailer_configs[retailer_code] = config
        self.retailer_buckets[retailer_code] = TokenBucket(
            config.requests_per_second,
            config.burst_size
        )
        logger.info(f"Configured rate limits for retailer {retailer_code}")
    
    def configure_domain(self, domain: str, config: RateLimitConfig):
        """Configure rate limits for a specific domain"""
        self.domain_configs[domain] = config
        self.domain_buckets[domain] = TokenBucket(
            config.requests_per_second,
            config.burst_size
        )
        logger.info(f"Configured rate limits for domain {domain}")
    
    def set_concurrent_limit(self, scope: str, limit: int):
        """Set concurrent request limit for a scope"""
        self.concurrent_limits[scope] = asyncio.Semaphore(limit)
        logger.info(f"Set concurrent limit for {scope}: {limit}")
    
    async def acquire(self, 
                     retailer_code: Optional[str] = None,
                     domain: Optional[str] = None,
                     priority: str = "normal") -> float:
        """
        Acquire permission to make a request
        
        Args:
            retailer_code: Retailer identifier
            domain: Domain for the request
            priority: Request priority (low, normal, high)
            
        Returns:
            Total wait time in seconds
        """
        wait_times = []
        
        # Global rate limit
        global_wait = await self.global_bucket.acquire()
        if global_wait > 0:
            wait_times.append(global_wait)
        
        # Retailer-specific rate limit
        if retailer_code and retailer_code in self.retailer_buckets:
            retailer_wait = await self.retailer_buckets[retailer_code].acquire()
            if retailer_wait > 0:
                wait_times.append(retailer_wait)
        
        # Domain-specific rate limit
        if domain and domain in self.domain_buckets:
            domain_wait = await self.domain_buckets[domain].acquire()
            if domain_wait > 0:
                wait_times.append(domain_wait)
        
        # Check time-window limits
        window_wait = await self._check_window_limits(retailer_code, domain)
        if window_wait > 0:
            wait_times.append(window_wait)
        
        # Calculate total wait time
        total_wait = max(wait_times) if wait_times else 0.0
        
        # Apply priority adjustments
        if priority == "high" and total_wait > 0:
            total_wait *= 0.5  # High priority waits half the time
        elif priority == "low" and total_wait > 0:
            total_wait *= 2.0  # Low priority waits double
        
        # Update statistics
        scope = retailer_code or domain or "global"
        self.stats[scope].total_requests += 1
        if total_wait > 0:
            self.stats[scope].throttled_requests += 1
            self.stats[scope].total_wait_time += total_wait
        
        # Record request time
        self._record_request(retailer_code, domain)
        
        return total_wait
    
    async def _check_window_limits(self, 
                                  retailer_code: Optional[str],
                                  domain: Optional[str]) -> float:
        """Check time-window based limits"""
        now = time.time()
        scope = retailer_code or domain or "global"
        config = self._get_config(retailer_code, domain)
        
        # Clean old entries
        history = self.request_history[scope]
        minute_ago = now - 60
        hour_ago = now - 3600
        
        while history and history[0] < hour_ago:
            history.popleft()
        
        # Count recent requests
        minute_count = sum(1 for t in history if t > minute_ago)
        hour_count = len(history)
        
        # Check limits
        if minute_count >= config.requests_per_minute:
            # Need to wait until oldest request in minute window expires
            oldest_in_minute = next((t for t in history if t > minute_ago), minute_ago)
            return oldest_in_minute + 60 - now
        
        if hour_count >= config.requests_per_hour:
            # Need to wait until oldest request in hour window expires
            return history[0] + 3600 - now
        
        return 0.0
    
    def _record_request(self, retailer_code: Optional[str], domain: Optional[str]):
        """Record request timestamp"""
        now = time.time()
        scope = retailer_code or domain or "global"
        self.request_history[scope].append(now)
        self.stats[scope].last_request_time = now
    
    def _get_config(self, 
                   retailer_code: Optional[str],
                   domain: Optional[str]) -> RateLimitConfig:
        """Get appropriate config for scope"""
        if retailer_code and retailer_code in self.retailer_configs:
            return self.retailer_configs[retailer_code]
        elif domain and domain in self.domain_configs:
            return self.domain_configs[domain]
        else:
            return self.global_config
    
    @asynccontextmanager
    async def limit(self,
                   retailer_code: Optional[str] = None,
                   domain: Optional[str] = None,
                   priority: str = "normal"):
        """
        Context manager for rate-limited operations
        
        Usage:
            async with rate_limiter.limit(retailer_code="HP"):
                # Make request
                response = await scraper.scrape(url)
        """
        scope = retailer_code or domain or "global"
        
        # Acquire semaphore if concurrent limit exists
        semaphore = self.concurrent_limits.get(scope)
        if semaphore:
            await semaphore.acquire()
        
        try:
            # Wait for rate limit
            wait_time = await self.acquire(retailer_code, domain, priority)
            if wait_time > 0:
                logger.debug(f"Rate limit: waiting {wait_time:.2f}s for {scope}")
                await asyncio.sleep(wait_time)
            
            yield
            
            # Success
            self.stats[scope].successful_requests += 1
            
        except Exception as e:
            # Failure
            self.stats[scope].failed_requests += 1
            raise
        
        finally:
            # Release semaphore
            if semaphore:
                semaphore.release()
            
            # Apply cooldown
            config = self._get_config(retailer_code, domain)
            if config.cooldown_seconds > 0:
                await asyncio.sleep(config.cooldown_seconds)
    
    def get_stats(self, scope: str = "global") -> RequestStats:
        """Get statistics for a scope"""
        return self.stats.get(scope, RequestStats())
    
    def reset_stats(self, scope: Optional[str] = None):
        """Reset statistics"""
        if scope:
            self.stats[scope] = RequestStats()
        else:
            self.stats.clear()
    
    def get_all_stats(self) -> Dict[str, Dict[str, Any]]:
        """Get all statistics as dictionary"""
        result = {}
        for scope, stats in self.stats.items():
            result[scope] = {
                "total_requests": stats.total_requests,
                "successful_requests": stats.successful_requests,
                "throttled_requests": stats.throttled_requests,
                "failed_requests": stats.failed_requests,
                "success_rate": stats.get_success_rate(),
                "total_wait_time": stats.total_wait_time,
                "avg_wait_time": stats.total_wait_time / stats.throttled_requests if stats.throttled_requests > 0 else 0,
                "last_request_time": datetime.fromtimestamp(stats.last_request_time).isoformat() if stats.last_request_time else None
            }
        return result


class RequestQueue:
    """
    Priority queue for managing scraping requests
    """
    
    def __init__(self, max_size: int = 1000):
        """Initialize request queue"""
        self.max_size = max_size
        self.queues = {
            "high": asyncio.Queue(),
            "normal": asyncio.Queue(),
            "low": asyncio.Queue()
        }
        self.processing = set()
        self.completed = deque(maxlen=1000)
        self.failed = deque(maxlen=100)
    
    async def put(self, request: Dict[str, Any], priority: str = "normal"):
        """Add request to queue"""
        if priority not in self.queues:
            priority = "normal"
        
        queue = self.queues[priority]
        if queue.qsize() >= self.max_size:
            raise ValueError(f"Queue full for priority {priority}")
        
        request["queued_at"] = time.time()
        request["priority"] = priority
        await queue.put(request)
    
    async def get(self) -> Optional[Dict[str, Any]]:
        """Get next request from queue (priority order)"""
        # Check high priority first
        for priority in ["high", "normal", "low"]:
            queue = self.queues[priority]
            if not queue.empty():
                request = await queue.get()
                request["dequeued_at"] = time.time()
                request["queue_time"] = request["dequeued_at"] - request["queued_at"]
                self.processing.add(request.get("id", id(request)))
                return request
        
        return None
    
    def mark_completed(self, request_id: str, success: bool = True):
        """Mark request as completed"""
        if request_id in self.processing:
            self.processing.remove(request_id)
        
        completed_record = {
            "id": request_id,
            "completed_at": time.time(),
            "success": success
        }
        
        if success:
            self.completed.append(completed_record)
        else:
            self.failed.append(completed_record)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get queue statistics"""
        return {
            "queued": {
                "high": self.queues["high"].qsize(),
                "normal": self.queues["normal"].qsize(),
                "low": self.queues["low"].qsize(),
                "total": sum(q.qsize() for q in self.queues.values())
            },
            "processing": len(self.processing),
            "completed": len(self.completed),
            "failed": len(self.failed),
            "success_rate": len(self.completed) / (len(self.completed) + len(self.failed)) * 100 if (len(self.completed) + len(self.failed)) > 0 else 0
        }


# Global rate limiter instance
global_rate_limiter = RateLimiter()

# Configure defaults for retailers
global_rate_limiter.configure_retailer("HP", RateLimitConfig(
    requests_per_second=2.0,
    requests_per_minute=60,
    requests_per_hour=2000,
    burst_size=10,
    cooldown_seconds=0.5
))

global_rate_limiter.configure_retailer("TWD", RateLimitConfig(
    requests_per_second=1.5,
    requests_per_minute=45,
    requests_per_hour=1500,
    burst_size=8,
    cooldown_seconds=0.7
))

global_rate_limiter.configure_retailer("GH", RateLimitConfig(
    requests_per_second=0.5,
    requests_per_minute=20,
    requests_per_hour=1000,
    burst_size=5,
    cooldown_seconds=2.0
))

global_rate_limiter.configure_retailer("DH", RateLimitConfig(
    requests_per_second=1.0,
    requests_per_minute=30,
    requests_per_hour=1200,
    burst_size=5,
    cooldown_seconds=1.0
))

global_rate_limiter.configure_retailer("BT", RateLimitConfig(
    requests_per_second=0.7,
    requests_per_minute=25,
    requests_per_hour=1000,
    burst_size=3,
    cooldown_seconds=1.5
))

global_rate_limiter.configure_retailer("MH", RateLimitConfig(
    requests_per_second=0.5,
    requests_per_minute=20,
    requests_per_hour=800,
    burst_size=3,
    cooldown_seconds=2.0
))

# Set concurrent limits
global_rate_limiter.set_concurrent_limit("HP", 5)
global_rate_limiter.set_concurrent_limit("TWD", 3)
global_rate_limiter.set_concurrent_limit("GH", 4)
global_rate_limiter.set_concurrent_limit("DH", 5)
global_rate_limiter.set_concurrent_limit("BT", 3)
global_rate_limiter.set_concurrent_limit("MH", 3)