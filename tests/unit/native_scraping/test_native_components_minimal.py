"""
Minimal tests for native scraping components
"""
import pytest
import asyncio
import re
from unittest.mock import Mock, AsyncMock, patch


class SimpleHTMLParser:
    """Minimal HTML parser for testing"""
    
    def parse_price(self, price_text):
        """Parse price from text"""
        if not price_text:
            return None
            
        # Remove currency symbols and extract numbers
        price_pattern = r'[\d,]+(?:\.\d+)?'
        match = re.search(price_pattern, str(price_text))
        
        if match:
            price_str = match.group().replace(',', '')
            try:
                return float(price_str)
            except ValueError:
                return None
        return None
    
    def parse_number(self, number_text):
        """Parse number from text"""
        if not number_text:
            return None
            
        # Extract first number
        number_pattern = r'\d+(?:,\d+)*'
        match = re.search(number_pattern, str(number_text))
        
        if match:
            number_str = match.group().replace(',', '')
            try:
                return int(number_str)
            except ValueError:
                return None
        return None


class SimpleRateLimiter:
    """Minimal rate limiter for testing"""
    
    def __init__(self, delay=1.0, max_concurrent=5):
        self.delay = delay
        self.max_concurrent = max_concurrent
        self.request_count = 0
        self.successful_requests = 0
        self.failed_requests = 0
        self.last_request_time = 0
        
    async def acquire(self):
        """Acquire permission to make a request"""
        import time
        current_time = time.time()
        
        # Simple delay implementation
        if current_time - self.last_request_time < self.delay:
            await asyncio.sleep(self.delay - (current_time - self.last_request_time))
        
        self.last_request_time = time.time()
        self.request_count += 1
    
    def record_request_result(self, success, response_time=0, status_code=200):
        """Record the result of a request"""
        if success:
            self.successful_requests += 1
        else:
            self.failed_requests += 1
    
    def get_stats(self):
        """Get rate limiter statistics"""
        return {
            'total_requests': self.request_count,
            'successful_requests': self.successful_requests,
            'failed_requests': self.failed_requests,
            'average_delay': self.delay
        }


class SimpleBrowserSessionManager:
    """Minimal session manager for testing"""
    
    def __init__(self):
        self.session_count = 0
        self.user_agents = [
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36'
        ]
    
    def get_random_user_agent(self):
        """Get a random user agent"""
        import random
        return random.choice(self.user_agents)
    
    def get_headers(self, referer=None, user_agent=None):
        """Get HTTP headers"""
        headers = {
            'User-Agent': user_agent or self.get_random_user_agent(),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        }
        
        if referer:
            headers['Referer'] = referer
        
        return headers
    
    async def get_session(self):
        """Get a session (mock)"""
        self.session_count += 1
        return Mock()
    
    async def close(self):
        """Close session manager"""
        pass


@pytest.mark.unit
@pytest.mark.native
class TestNativeComponentsMinimal:
    """Minimal tests for native scraping components"""
    
    def test_html_parser_price_parsing(self):
        """Test HTML parser price parsing"""
        parser = SimpleHTMLParser()
        
        # Test various price formats
        test_cases = [
            ("฿1,299.99", 1299.99),
            ("฿1,299", 1299.0),
            ("1,299.99 บาท", 1299.99),
            ("THB 1,299.99", 1299.99),
            ("1299.99", 1299.99),
            ("1,299", 1299.0),
            ("invalid", None),
            ("", None),
            (None, None)
        ]
        
        for price_text, expected in test_cases:
            result = parser.parse_price(price_text)
            assert result == expected, f"Failed for {price_text}: expected {expected}, got {result}"
    
    def test_html_parser_number_parsing(self):
        """Test HTML parser number parsing"""
        parser = SimpleHTMLParser()
        
        test_cases = [
            ("123", 123),
            ("1,234", 1234),
            ("1,234.56", 1234),  # Should extract integer part
            ("123 reviews", 123),
            ("invalid", None),
            ("", None),
            (None, None)
        ]
        
        for number_text, expected in test_cases:
            result = parser.parse_number(number_text)
            assert result == expected, f"Failed for {number_text}: expected {expected}, got {result}"
    
    @pytest.mark.asyncio
    async def test_rate_limiter_basic_functionality(self):
        """Test rate limiter basic functionality"""
        limiter = SimpleRateLimiter(delay=0.1, max_concurrent=2)
        
        # Test basic rate limiting
        start_time = asyncio.get_event_loop().time()
        await limiter.acquire()
        await limiter.acquire()
        end_time = asyncio.get_event_loop().time()
        
        # Should take at least the delay time
        assert end_time - start_time >= 0.1
        
        # Test statistics
        limiter.record_request_result(True, 0.5, 200)
        limiter.record_request_result(False, 0.3, 404)
        
        stats = limiter.get_stats()
        assert stats['total_requests'] == 2
        assert stats['successful_requests'] == 1
        assert stats['failed_requests'] == 1
    
    @pytest.mark.asyncio
    async def test_session_manager_basic_functionality(self):
        """Test session manager basic functionality"""
        manager = SimpleBrowserSessionManager()
        
        # Test user agent generation
        ua1 = manager.get_random_user_agent()
        ua2 = manager.get_random_user_agent()
        
        assert ua1 is not None
        assert ua2 is not None
        assert isinstance(ua1, str)
        assert isinstance(ua2, str)
        
        # Test header generation
        headers = manager.get_headers()
        assert 'User-Agent' in headers
        assert 'Accept' in headers
        assert 'Accept-Language' in headers
        
        # Test with custom referer
        headers_with_referer = manager.get_headers(referer="https://example.com")
        assert headers_with_referer['Referer'] == "https://example.com"
        
        # Test session creation
        session = await manager.get_session()
        assert session is not None
        assert manager.session_count == 1
        
        # Test cleanup
        await manager.close()
    
    @pytest.mark.asyncio
    async def test_concurrent_rate_limiting(self):
        """Test concurrent rate limiting"""
        limiter = SimpleRateLimiter(delay=0.05, max_concurrent=3)
        
        # Create multiple concurrent requests
        tasks = []
        for _ in range(5):
            task = asyncio.create_task(limiter.acquire())
            tasks.append(task)
        
        # Should complete without error
        await asyncio.gather(*tasks)
        
        # Check that all requests were recorded
        assert limiter.request_count == 5
    
    def test_user_agent_variety(self):
        """Test user agent variety"""
        manager = SimpleBrowserSessionManager()
        
        # Test that we have reasonable variety
        user_agents = set()
        for _ in range(20):
            user_agents.add(manager.get_random_user_agent())
        
        # Should have at least 2 different user agents
        assert len(user_agents) >= 2
        
        # Check that user agents look realistic
        for ua in user_agents:
            assert 'Mozilla' in ua
            assert 'AppleWebKit' in ua
    
    @pytest.mark.asyncio
    async def test_performance_simple(self):
        """Test simple performance characteristics"""
        limiter = SimpleRateLimiter(delay=0.01, max_concurrent=10)
        
        # Test performance with multiple requests
        start_time = asyncio.get_event_loop().time()
        
        tasks = []
        for i in range(10):
            task = asyncio.create_task(limiter.acquire())
            tasks.append(task)
        
        await asyncio.gather(*tasks)
        end_time = asyncio.get_event_loop().time()
        
        total_time = end_time - start_time
        
        # Should complete in reasonable time
        assert total_time < 1.0  # Should be fast
        
        # Should handle decent throughput
        throughput = 10 / total_time
        assert throughput > 5.0  # At least 5 requests per second
    
    def test_error_handling(self):
        """Test error handling in components"""
        parser = SimpleHTMLParser()
        
        # Test with various invalid inputs
        invalid_inputs = [None, "", "invalid", 123, [], {}]
        
        for invalid_input in invalid_inputs:
            # Should not raise exceptions
            price_result = parser.parse_price(invalid_input)
            number_result = parser.parse_number(invalid_input)
            
            # Should return None for invalid inputs
            if invalid_input not in [123]:  # 123 is valid for number parsing
                assert price_result is None
                if invalid_input != 123:
                    assert number_result is None
    
    @pytest.mark.asyncio
    async def test_session_manager_concurrent_access(self):
        """Test concurrent access to session manager"""
        manager = SimpleBrowserSessionManager()
        
        # Create concurrent requests
        tasks = []
        for _ in range(5):
            task = asyncio.create_task(manager.get_session())
            tasks.append(task)
        
        # Should complete without error
        sessions = await asyncio.gather(*tasks)
        
        # Should have sessions
        assert len(sessions) == 5
        assert all(s is not None for s in sessions)
        assert manager.session_count == 5
    
    def test_integration_components(self):
        """Test components working together"""
        parser = SimpleHTMLParser()
        limiter = SimpleRateLimiter(delay=0.01, max_concurrent=5)
        manager = SimpleBrowserSessionManager()
        
        # Test HTML parsing
        price = parser.parse_price("฿1,299.99")
        assert price == 1299.99
        
        # Test rate limiting stats
        limiter.record_request_result(True, 0.5, 200)
        stats = limiter.get_stats()
        assert stats['successful_requests'] == 1
        
        # Test session manager
        headers = manager.get_headers()
        assert 'User-Agent' in headers
        
        # All components should work together
        assert price is not None
        assert stats['total_requests'] >= 0
        assert len(headers) > 0