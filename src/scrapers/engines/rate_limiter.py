"""
Intelligent rate limiter for native scraping with adaptive behavior
"""
import asyncio
import logging
from typing import Dict, Optional, List
from datetime import datetime, timedelta
from dataclasses import dataclass
import statistics
from collections import deque

logger = logging.getLogger(__name__)


@dataclass
class RequestMetrics:
    """Metrics for a single request"""
    timestamp: datetime
    success: bool
    response_time: float
    status_code: Optional[int] = None
    retry_count: int = 0


class RateLimiter:
    """
    Intelligent rate limiter with adaptive behavior based on server responses
    """
    
    def __init__(self, 
                 delay: float = 1.0,
                 max_concurrent: int = 5,
                 burst_size: int = 10,
                 window_size: int = 60):
        """
        Initialize rate limiter
        
        Args:
            delay: Base delay between requests in seconds
            max_concurrent: Maximum concurrent requests
            burst_size: Maximum requests in burst mode
            window_size: Window size for rate calculation in seconds
        """
        self.base_delay = delay
        self.current_delay = delay
        self.max_concurrent = max_concurrent
        self.burst_size = burst_size
        self.window_size = window_size
        
        # Concurrency control
        self._semaphore = asyncio.Semaphore(max_concurrent)
        self._request_times: deque = deque()
        self._last_request_time: Optional[datetime] = None
        
        # Adaptive behavior
        self._request_metrics: deque = deque(maxlen=100)  # Keep last 100 requests
        self._consecutive_failures = 0
        self._consecutive_successes = 0
        self._rate_limited_count = 0
        
        # Burst mode
        self._burst_tokens = burst_size
        self._last_token_refill = datetime.now()
        
        # Statistics
        self.stats = {
            'total_requests': 0,
            'successful_requests': 0,
            'failed_requests': 0,
            'rate_limited_requests': 0,
            'average_delay': delay,
            'current_delay': delay,
            'burst_requests': 0,
            'adaptive_adjustments': 0
        }
    
    async def acquire(self) -> None:
        """Acquire permission to make a request"""
        async with self._semaphore:
            await self._wait_for_rate_limit()
            self._update_request_time()
    
    async def _wait_for_rate_limit(self) -> None:
        """Wait based on current rate limiting strategy"""
        now = datetime.now()
        
        # Check if we can use burst mode
        if self._can_use_burst():
            self._use_burst_token()
            return
        
        # Calculate delay based on current strategy
        delay = self._calculate_delay(now)
        
        if delay > 0:
            logger.debug(f"Rate limiting: waiting {delay:.2f} seconds")
            await asyncio.sleep(delay)
    
    def _can_use_burst(self) -> bool:
        """Check if burst mode can be used"""
        return self._burst_tokens > 0 and self._consecutive_failures < 3
    
    def _use_burst_token(self) -> None:
        """Use a burst token"""
        self._burst_tokens -= 1
        self.stats['burst_requests'] += 1
        logger.debug(f"Used burst token, {self._burst_tokens} remaining")
    
    def _calculate_delay(self, now: datetime) -> float:
        """Calculate delay based on current conditions"""
        # Refill burst tokens if needed
        self._refill_burst_tokens(now)
        
        # Base delay
        delay = self.current_delay
        
        # Adjust for recent request frequency
        if self._last_request_time:
            time_since_last = (now - self._last_request_time).total_seconds()
            if time_since_last < delay:
                delay = delay - time_since_last
            else:
                delay = 0
        
        # Adjust for consecutive failures
        if self._consecutive_failures > 0:
            delay *= (1 + self._consecutive_failures * 0.5)
        
        # Adjust for rate limiting
        if self._rate_limited_count > 0:
            delay *= (1 + self._rate_limited_count * 2)
        
        return max(0, delay)
    
    def _refill_burst_tokens(self, now: datetime) -> None:
        """Refill burst tokens based on time passed"""
        time_since_refill = (now - self._last_token_refill).total_seconds()
        
        # Refill one token every 10 seconds
        tokens_to_add = int(time_since_refill / 10)
        
        if tokens_to_add > 0:
            self._burst_tokens = min(self.burst_size, self._burst_tokens + tokens_to_add)
            self._last_token_refill = now
    
    def _update_request_time(self) -> None:
        """Update the last request time"""
        now = datetime.now()
        self._last_request_time = now
        self._request_times.append(now)
        
        # Keep only recent requests
        cutoff_time = now - timedelta(seconds=self.window_size)
        while self._request_times and self._request_times[0] < cutoff_time:
            self._request_times.popleft()
    
    def record_request_result(self, 
                            success: bool, 
                            response_time: float,
                            status_code: Optional[int] = None,
                            retry_count: int = 0) -> None:
        """
        Record the result of a request for adaptive behavior
        
        Args:
            success: Whether the request was successful
            response_time: Time taken for the request
            status_code: HTTP status code
            retry_count: Number of retries for this request
        """
        # Record metrics
        metrics = RequestMetrics(
            timestamp=datetime.now(),
            success=success,
            response_time=response_time,
            status_code=status_code,
            retry_count=retry_count
        )
        self._request_metrics.append(metrics)
        
        # Update statistics
        self.stats['total_requests'] += 1
        
        if success:
            self.stats['successful_requests'] += 1
            self._consecutive_successes += 1
            self._consecutive_failures = 0
        else:
            self.stats['failed_requests'] += 1
            self._consecutive_failures += 1
            self._consecutive_successes = 0
        
        # Handle rate limiting
        if status_code == 429:
            self.stats['rate_limited_requests'] += 1
            self._rate_limited_count += 1
            self._handle_rate_limit()
        else:
            # Gradually reduce rate limiting penalty
            if self._rate_limited_count > 0:
                self._rate_limited_count = max(0, self._rate_limited_count - 1)
        
        # Adaptive delay adjustment
        self._adapt_delay()
    
    def _handle_rate_limit(self) -> None:
        """Handle rate limiting response"""
        # Increase delay significantly
        self.current_delay = min(self.current_delay * 2, 60)  # Max 60 seconds
        
        # Reset burst tokens
        self._burst_tokens = 0
        
        logger.warning(f"Rate limited! Increased delay to {self.current_delay:.2f} seconds")
        self.stats['adaptive_adjustments'] += 1
    
    def _adapt_delay(self) -> None:
        """Adapt delay based on recent performance"""
        if len(self._request_metrics) < 10:
            return
        
        # Get recent metrics
        recent_metrics = list(self._request_metrics)[-10:]
        success_rate = sum(1 for m in recent_metrics if m.success) / len(recent_metrics)
        avg_response_time = statistics.mean(m.response_time for m in recent_metrics)
        
        # Adjust delay based on success rate
        if success_rate > 0.9 and self._consecutive_successes > 10:
            # High success rate, we can be more aggressive
            self.current_delay = max(self.base_delay * 0.5, self.current_delay * 0.9)
            logger.debug(f"Decreased delay to {self.current_delay:.2f} seconds (high success rate)")
            self.stats['adaptive_adjustments'] += 1
        
        elif success_rate < 0.7 or avg_response_time > 10:
            # Low success rate or slow responses, be more conservative
            self.current_delay = min(self.base_delay * 3, self.current_delay * 1.2)
            logger.debug(f"Increased delay to {self.current_delay:.2f} seconds (low success rate)")
            self.stats['adaptive_adjustments'] += 1
        
        # Update statistics
        self.stats['current_delay'] = self.current_delay
        self.stats['average_delay'] = self._calculate_average_delay()
    
    def _calculate_average_delay(self) -> float:
        """Calculate average delay from recent requests"""
        if len(self._request_metrics) < 2:
            return self.current_delay
        
        # Calculate delays between consecutive requests
        delays = []
        for i in range(1, len(self._request_metrics)):
            prev_time = self._request_metrics[i-1].timestamp
            curr_time = self._request_metrics[i].timestamp
            delay = (curr_time - prev_time).total_seconds()
            delays.append(delay)
        
        return statistics.mean(delays) if delays else self.current_delay
    
    def get_current_rate(self) -> float:
        """Get current request rate (requests per second)"""
        if not self._request_times:
            return 0.0
        
        time_span = (self._request_times[-1] - self._request_times[0]).total_seconds()
        return len(self._request_times) / max(time_span, 1)
    
    def get_success_rate(self) -> float:
        """Get recent success rate"""
        if not self._request_metrics:
            return 0.0
        
        recent_metrics = list(self._request_metrics)[-20:]  # Last 20 requests
        successful = sum(1 for m in recent_metrics if m.success)
        return successful / len(recent_metrics)
    
    def get_average_response_time(self) -> float:
        """Get average response time"""
        if not self._request_metrics:
            return 0.0
        
        recent_metrics = list(self._request_metrics)[-20:]  # Last 20 requests
        return statistics.mean(m.response_time for m in recent_metrics)
    
    def increase_delay(self, factor: float = 2.0) -> None:
        """Manually increase delay (e.g., after receiving rate limit response)"""
        old_delay = self.current_delay
        self.current_delay = min(self.current_delay * factor, 60)  # Max 60 seconds
        
        logger.info(f"Manually increased delay from {old_delay:.2f} to {self.current_delay:.2f} seconds")
        self.stats['adaptive_adjustments'] += 1
    
    def decrease_delay(self, factor: float = 0.8) -> None:
        """Manually decrease delay"""
        old_delay = self.current_delay
        self.current_delay = max(self.base_delay * 0.5, self.current_delay * factor)
        
        logger.info(f"Manually decreased delay from {old_delay:.2f} to {self.current_delay:.2f} seconds")
        self.stats['adaptive_adjustments'] += 1
    
    def reset_delay(self) -> None:
        """Reset delay to base value"""
        self.current_delay = self.base_delay
        self._consecutive_failures = 0
        self._consecutive_successes = 0
        self._rate_limited_count = 0
        self._burst_tokens = self.burst_size
        
        logger.info(f"Reset delay to base value: {self.base_delay:.2f} seconds")
    
    def get_limiter_info(self) -> Dict:
        """Get detailed information about the rate limiter"""
        return {
            'base_delay': self.base_delay,
            'current_delay': self.current_delay,
            'max_concurrent': self.max_concurrent,
            'burst_size': self.burst_size,
            'burst_tokens': self._burst_tokens,
            'window_size': self.window_size,
            'consecutive_failures': self._consecutive_failures,
            'consecutive_successes': self._consecutive_successes,
            'rate_limited_count': self._rate_limited_count,
            'current_rate': self.get_current_rate(),
            'success_rate': self.get_success_rate(),
            'average_response_time': self.get_average_response_time(),
            'requests_in_window': len(self._request_times),
            'stats': self.stats
        }
    
    def get_stats(self) -> Dict:
        """Get rate limiter statistics"""
        return self.stats.copy()
    
    def export_metrics(self) -> List[Dict]:
        """Export request metrics for analysis"""
        return [
            {
                'timestamp': m.timestamp.isoformat(),
                'success': m.success,
                'response_time': m.response_time,
                'status_code': m.status_code,
                'retry_count': m.retry_count
            }
            for m in self._request_metrics
        ]
    
    def __repr__(self) -> str:
        return (f"RateLimiter(delay={self.current_delay:.2f}s, "
                f"concurrent={self.max_concurrent}, "
                f"success_rate={self.get_success_rate():.2f})")