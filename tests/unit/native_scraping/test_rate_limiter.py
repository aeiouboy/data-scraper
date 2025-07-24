"""
Unit tests for rate limiter
"""
import pytest
import asyncio
from scrapers.engines.rate_limiter import RateLimiter


@pytest.mark.unit
@pytest.mark.native
class TestRateLimiter:
    """Test cases for rate limiter functionality"""
    
    def test_initialization(self):
        """Test rate limiter initialization"""
        limiter = RateLimiter(delay=1.0, max_concurrent=5)
        
        assert limiter.base_delay == 1.0
        assert limiter.current_delay == 1.0
        assert limiter.max_concurrent == 5
        assert limiter.burst_size == 10  # default
        assert limiter.window_size == 60  # default
    
    def test_initialization_with_custom_params(self):
        """Test initialization with custom parameters"""
        limiter = RateLimiter(
            delay=2.0,
            max_concurrent=3,
            burst_size=5,
            window_size=30
        )
        
        assert limiter.base_delay == 2.0
        assert limiter.current_delay == 2.0
        assert limiter.max_concurrent == 3
        assert limiter.burst_size == 5
        assert limiter.window_size == 30
    
    @pytest.mark.asyncio
    async def test_basic_rate_limiting(self):
        """Test basic rate limiting functionality"""
        limiter = RateLimiter(delay=0.1, max_concurrent=1)
        
        # Test that requests are delayed
        start_time = asyncio.get_event_loop().time()
        await limiter.acquire()
        await limiter.acquire()
        end_time = asyncio.get_event_loop().time()
        
        # Should take at least the delay time
        assert end_time - start_time >= 0.1
    
    @pytest.mark.asyncio
    async def test_concurrent_limiting(self):
        """Test concurrent request limiting"""
        limiter = RateLimiter(delay=0.01, max_concurrent=2)
        
        # Create multiple concurrent requests
        tasks = []
        for _ in range(5):
            task = asyncio.create_task(limiter.acquire())
            tasks.append(task)
        
        # Should complete without error
        await asyncio.gather(*tasks)
    
    @pytest.mark.asyncio
    async def test_burst_mode(self):
        """Test burst mode functionality"""
        limiter = RateLimiter(delay=0.1, max_concurrent=5, burst_size=3)
        
        # First few requests should be fast (burst mode)
        start_time = asyncio.get_event_loop().time()
        await limiter.acquire()
        await limiter.acquire()
        await limiter.acquire()
        burst_time = asyncio.get_event_loop().time() - start_time
        
        # Should be fast (burst mode)
        assert burst_time < 0.05
        
        # Next request should be slower (regular mode)
        start_time = asyncio.get_event_loop().time()
        await limiter.acquire()
        regular_time = asyncio.get_event_loop().time() - start_time
        
        # Should be slower than burst
        assert regular_time > burst_time
    
    def test_record_request_result_success(self):
        """Test recording successful request results"""
        limiter = RateLimiter(delay=1.0, max_concurrent=5)
        
        # Record successful request
        limiter.record_request_result(success=True, response_time=0.5, status_code=200)
        
        stats = limiter.get_stats()
        assert stats['total_requests'] == 1
        assert stats['successful_requests'] == 1
        assert stats['failed_requests'] == 0
        assert stats['average_delay'] > 0
    
    def test_record_request_result_failure(self):
        """Test recording failed request results"""
        limiter = RateLimiter(delay=1.0, max_concurrent=5)
        
        # Record failed request
        limiter.record_request_result(success=False, response_time=0.2, status_code=404)
        
        stats = limiter.get_stats()
        assert stats['total_requests'] == 1
        assert stats['successful_requests'] == 0
        assert stats['failed_requests'] == 1
    
    def test_record_rate_limited_request(self):
        """Test recording rate limited requests"""
        limiter = RateLimiter(delay=1.0, max_concurrent=5)
        
        # Record rate limited request
        limiter.record_request_result(success=False, response_time=0.1, status_code=429)
        
        stats = limiter.get_stats()
        assert stats['rate_limited_requests'] == 1
        
        # Current delay should be increased
        assert limiter.current_delay > limiter.base_delay
    
    def test_adaptive_delay_adjustment(self):
        """Test adaptive delay adjustment based on performance"""
        limiter = RateLimiter(delay=1.0, max_concurrent=5)
        
        # Record multiple successful requests
        for _ in range(15):
            limiter.record_request_result(success=True, response_time=0.3, status_code=200)
        
        # Should decrease delay due to high success rate
        assert limiter.current_delay <= limiter.base_delay
        
        # Record multiple failed requests
        for _ in range(10):
            limiter.record_request_result(success=False, response_time=5.0, status_code=500)
        
        # Should increase delay due to low success rate
        assert limiter.current_delay > limiter.base_delay
    
    def test_get_current_rate(self):
        """Test current rate calculation"""
        limiter = RateLimiter(delay=0.1, max_concurrent=5)
        
        # Initially should be 0
        assert limiter.get_current_rate() == 0.0
        
        # Add some request times
        import time
        current_time = time.time()
        for i in range(5):
            limiter._request_times.append(current_time - i)
        
        # Should calculate rate
        rate = limiter.get_current_rate()
        assert rate > 0
    
    def test_get_success_rate(self):
        """Test success rate calculation"""
        limiter = RateLimiter(delay=1.0, max_concurrent=5)
        
        # Initially should be 0
        assert limiter.get_success_rate() == 0.0
        
        # Record some requests
        limiter.record_request_result(success=True, response_time=0.5)
        limiter.record_request_result(success=True, response_time=0.5)
        limiter.record_request_result(success=False, response_time=0.5)
        
        # Should be 2/3 = 0.67
        success_rate = limiter.get_success_rate()
        assert abs(success_rate - 0.67) < 0.01
    
    def test_get_average_response_time(self):
        """Test average response time calculation"""
        limiter = RateLimiter(delay=1.0, max_concurrent=5)
        
        # Initially should be 0
        assert limiter.get_average_response_time() == 0.0
        
        # Record some requests
        limiter.record_request_result(success=True, response_time=0.5)
        limiter.record_request_result(success=True, response_time=1.0)
        limiter.record_request_result(success=True, response_time=0.5)
        
        # Should be average of 0.5, 1.0, 0.5 = 0.67
        avg_time = limiter.get_average_response_time()
        assert abs(avg_time - 0.67) < 0.01
    
    def test_manual_delay_adjustment(self):
        """Test manual delay adjustment"""
        limiter = RateLimiter(delay=1.0, max_concurrent=5)
        
        # Test increase delay
        original_delay = limiter.current_delay
        limiter.increase_delay(factor=2.0)
        assert limiter.current_delay == original_delay * 2.0
        
        # Test decrease delay
        limiter.decrease_delay(factor=0.5)
        assert limiter.current_delay == original_delay
        
        # Test reset delay
        limiter.increase_delay(factor=3.0)
        limiter.reset_delay()
        assert limiter.current_delay == limiter.base_delay
    
    def test_limiter_info(self):
        """Test getting limiter information"""
        limiter = RateLimiter(delay=1.0, max_concurrent=5)
        
        # Record some requests
        limiter.record_request_result(success=True, response_time=0.5)
        limiter.record_request_result(success=False, response_time=0.3)
        
        info = limiter.get_limiter_info()
        
        # Check required fields
        assert 'base_delay' in info
        assert 'current_delay' in info
        assert 'max_concurrent' in info
        assert 'burst_size' in info
        assert 'consecutive_failures' in info
        assert 'consecutive_successes' in info
        assert 'current_rate' in info
        assert 'success_rate' in info
        assert 'average_response_time' in info
        assert 'stats' in info
    
    def test_export_metrics(self):
        """Test exporting metrics"""
        limiter = RateLimiter(delay=1.0, max_concurrent=5)
        
        # Record some requests
        limiter.record_request_result(success=True, response_time=0.5, status_code=200)
        limiter.record_request_result(success=False, response_time=0.3, status_code=404)
        
        metrics = limiter.export_metrics()
        
        assert len(metrics) == 2
        assert metrics[0]['success'] == True
        assert metrics[0]['status_code'] == 200
        assert metrics[1]['success'] == False
        assert metrics[1]['status_code'] == 404
    
    def test_repr(self):
        """Test string representation"""
        limiter = RateLimiter(delay=1.0, max_concurrent=5)
        
        # Should not raise exception
        str_repr = repr(limiter)
        assert 'RateLimiter' in str_repr
        assert 'delay=' in str_repr
        assert 'concurrent=' in str_repr
    
    def test_burst_token_refill(self):
        """Test burst token refill mechanism"""
        limiter = RateLimiter(delay=1.0, max_concurrent=5, burst_size=3)
        
        # Use all burst tokens
        limiter._burst_tokens = 0
        
        # Simulate time passing
        import time
        current_time = time.time()
        limiter._last_token_refill = current_time - 30  # 30 seconds ago
        
        # Should refill tokens
        limiter._refill_burst_tokens(current_time)
        assert limiter._burst_tokens > 0
    
    def test_consecutive_failures_tracking(self):
        """Test consecutive failures tracking"""
        limiter = RateLimiter(delay=1.0, max_concurrent=5)
        
        # Record failures
        limiter.record_request_result(success=False, response_time=0.5)
        limiter.record_request_result(success=False, response_time=0.5)
        limiter.record_request_result(success=False, response_time=0.5)
        
        assert limiter._consecutive_failures == 3
        assert limiter._consecutive_successes == 0
        
        # Record success
        limiter.record_request_result(success=True, response_time=0.5)
        
        assert limiter._consecutive_failures == 0
        assert limiter._consecutive_successes == 1
    
    def test_window_size_limiting(self):
        """Test that request times are limited by window size"""
        limiter = RateLimiter(delay=1.0, max_concurrent=5, window_size=10)
        
        # Add many request times
        import time
        current_time = time.time()
        for i in range(100):
            limiter._request_times.append(current_time - i)
        
        # Update request time to trigger cleanup
        limiter._update_request_time()
        
        # Should only keep requests within window
        assert len(limiter._request_times) <= 10
    
    @pytest.mark.asyncio
    async def test_performance_with_multiple_requests(self):
        """Test performance with multiple concurrent requests"""
        limiter = RateLimiter(delay=0.01, max_concurrent=10)
        
        # Create many concurrent requests
        tasks = []
        for _ in range(50):
            task = asyncio.create_task(limiter.acquire())
            tasks.append(task)
        
        # Should complete in reasonable time
        start_time = asyncio.get_event_loop().time()
        await asyncio.gather(*tasks)
        end_time = asyncio.get_event_loop().time()
        
        # Should not take too long
        assert end_time - start_time < 5.0  # 5 seconds max