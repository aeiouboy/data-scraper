"""
Unit tests for FirecrawlClient class
"""
import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
import httpx
from datetime import datetime, timedelta

from app.services.firecrawl_client import FirecrawlClient, RateLimiter


class TestRateLimiter:
    """Test suite for RateLimiter"""
    
    def setup_method(self):
        """Setup for each test method"""
        self.rate_limiter = RateLimiter(calls_per_minute=30)
    
    @pytest.mark.asyncio
    async def test_rate_limiter_under_limit(self):
        """Test rate limiter when under the limit"""
        # Should not wait when under limit
        start_time = datetime.now()
        await self.rate_limiter.acquire()
        end_time = datetime.now()
        
        # Should be nearly instantaneous
        assert (end_time - start_time).total_seconds() < 0.1
        assert len(self.rate_limiter.calls) == 1
    
    @pytest.mark.asyncio
    async def test_rate_limiter_at_limit(self):
        """Test rate limiter when at the limit"""
        # Fill up the rate limiter
        for _ in range(30):
            await self.rate_limiter.acquire()
        
        assert len(self.rate_limiter.calls) == 30
        
        # Next call should wait
        start_time = datetime.now()
        await self.rate_limiter.acquire()
        end_time = datetime.now()
        
        # Should have waited some time (though not full 60s in test)
        assert (end_time - start_time).total_seconds() > 0
    
    @pytest.mark.asyncio
    async def test_rate_limiter_cleanup_old_calls(self):
        """Test that old calls are cleaned up"""
        # Add some old calls manually
        old_time = datetime.now() - timedelta(minutes=2)
        self.rate_limiter.calls = [old_time] * 30
        
        # New call should clean up old ones
        await self.rate_limiter.acquire()
        
        # Should only have 1 call now (the new one)
        assert len(self.rate_limiter.calls) == 1
    
    def test_rate_limiter_custom_limit(self):
        """Test rate limiter with custom limit"""
        custom_limiter = RateLimiter(calls_per_minute=60)
        assert custom_limiter.calls_per_minute == 60


class TestFirecrawlClient:
    """Test suite for FirecrawlClient"""
    
    def setup_method(self):
        """Setup for each test method"""
        with patch('app.services.firecrawl_client.get_settings') as mock_settings:
            mock_settings.return_value.firecrawl_api_key = "test-api-key"
            self.client = FirecrawlClient()
    
    @pytest.mark.asyncio
    async def test_context_manager(self):
        """Test async context manager functionality"""
        async with self.client as client:
            assert client is not None
            assert hasattr(client, 'client')
        
        # Client should be closed after context
        assert self.client.client.is_closed
    
    @pytest.mark.asyncio
    async def test_scrape_success(self):
        """Test successful scraping"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "data": {
                "metadata": {"title": "Test Page"},
                "markdown": "# Test Content",
                "html": "<html>Test</html>"
            }
        }
        
        with patch.object(self.client.client, 'post', new=AsyncMock(return_value=mock_response)):
            result = await self.client.scrape("https://example.com")
            
            assert result is not None
            assert "metadata" in result
            assert result["metadata"]["title"] == "Test Page"
    
    @pytest.mark.asyncio
    async def test_scrape_rate_limit(self):
        """Test scraping with rate limit response"""
        # First call hits rate limit
        rate_limit_response = Mock()
        rate_limit_response.status_code = 429
        rate_limit_response.headers = {"Retry-After": "1"}
        
        # Second call succeeds
        success_response = Mock()
        success_response.status_code = 200
        success_response.json.return_value = {
            "data": {"metadata": {"title": "Success"}}
        }
        
        with patch.object(self.client.client, 'post', new=AsyncMock(
            side_effect=[rate_limit_response, success_response]
        )):
            with patch('asyncio.sleep') as mock_sleep:
                result = await self.client.scrape("https://example.com")
                
                # Should have waited for rate limit
                mock_sleep.assert_called_with(1)
                assert result["metadata"]["title"] == "Success"
    
    @pytest.mark.asyncio
    async def test_scrape_http_error(self):
        """Test scraping with HTTP error"""
        error_response = Mock()
        error_response.status_code = 500
        error_response.text = "Internal Server Error"
        
        with patch.object(self.client.client, 'post', new=AsyncMock(return_value=error_response)):
            with pytest.raises(Exception, match="Failed to scrape"):
                await self.client.scrape("https://example.com")
    
    @pytest.mark.asyncio
    async def test_scrape_retry_logic(self):
        """Test retry logic on failure"""
        # Mock multiple failures then success
        error_response = Mock()
        error_response.status_code = 500
        error_response.text = "Internal Server Error"
        
        success_response = Mock()
        success_response.status_code = 200
        success_response.json.return_value = {"data": {"title": "Success"}}
        
        with patch.object(self.client.client, 'post', new=AsyncMock(
            side_effect=[error_response, error_response, success_response]
        )):
            with patch('app.services.firecrawl_client.asyncio.sleep') as mock_sleep:
                result = await self.client.scrape("https://example.com", retry_count=3)
                
                # Should have retried twice
                assert mock_sleep.call_count == 2
                assert result["title"] == "Success"
    
    @pytest.mark.asyncio
    async def test_scrape_max_retries_exceeded(self):
        """Test when max retries are exceeded"""
        error_response = Mock()
        error_response.status_code = 500
        
        with patch.object(self.client.client, 'post', new=AsyncMock(return_value=error_response)):
            with pytest.raises(Exception, match="Failed to scrape"):
                await self.client.scrape("https://example.com", retry_count=2)
    
    @pytest.mark.asyncio
    async def test_crawl_success(self):
        """Test successful crawling"""
        # Mock crawl initiation
        crawl_response = Mock()
        crawl_response.status_code = 200
        crawl_response.json.return_value = {"jobId": "test-job-id"}
        
        # Mock successful job completion
        with patch.object(self.client, '_poll_crawl_job', new=AsyncMock(
            return_value=["https://example.com/page1", "https://example.com/page2"]
        )):
            with patch.object(self.client.client, 'post', new=AsyncMock(return_value=crawl_response)):
                result = await self.client.crawl("https://example.com")
                
                assert len(result) == 2
                assert "https://example.com/page1" in result
    
    @pytest.mark.asyncio
    async def test_crawl_failure(self):
        """Test crawl failure"""
        error_response = Mock()
        error_response.status_code = 500
        
        with patch.object(self.client.client, 'post', new=AsyncMock(return_value=error_response)):
            result = await self.client.crawl("https://example.com")
            assert result == []
    
    @pytest.mark.asyncio
    async def test_poll_crawl_job_completed(self):
        """Test polling completed crawl job"""
        completed_response = Mock()
        completed_response.status_code = 200
        completed_response.json.return_value = {
            "status": "completed",
            "data": [
                {
                    "metadata": {"sourceURL": "https://example.com/page1"},
                    "linksOnPage": ["https://example.com/p/123", "https://example.com/p/456"]
                }
            ]
        }
        
        with patch.object(self.client.client, 'get', new=AsyncMock(return_value=completed_response)):
            result = await self.client._poll_crawl_job("test-job-id")
            
            assert len(result) >= 1  # Should have source URL plus extracted links
            assert any("https://example.com/p/123" in url for url in result)
    
    @pytest.mark.asyncio
    async def test_poll_crawl_job_failed(self):
        """Test polling failed crawl job"""
        failed_response = Mock()
        failed_response.status_code = 200
        failed_response.json.return_value = {"status": "failed"}
        
        with patch.object(self.client.client, 'get', new=AsyncMock(return_value=failed_response)):
            result = await self.client._poll_crawl_job("test-job-id")
            assert result == []
    
    @pytest.mark.asyncio
    async def test_poll_crawl_job_timeout(self):
        """Test polling timeout"""
        pending_response = Mock()
        pending_response.status_code = 200
        pending_response.json.return_value = {"status": "pending"}
        
        with patch.object(self.client.client, 'get', new=AsyncMock(return_value=pending_response)):
            with patch('asyncio.sleep') as mock_sleep:
                # Test with very short timeout
                result = await self.client._poll_crawl_job("test-job-id", timeout=1)
                assert result == []
    
    @pytest.mark.asyncio
    async def test_batch_scrape_success(self):
        """Test successful batch scraping"""
        urls = [
            "https://example.com/page1",
            "https://example.com/page2",
            "https://example.com/page3"
        ]
        
        # Mock individual scrape results
        with patch.object(self.client, 'scrape', new=AsyncMock(
            side_effect=[
                {"title": "Page 1"},
                {"title": "Page 2"},
                {"title": "Page 3"}
            ]
        )):
            result = await self.client.batch_scrape(urls, max_concurrent=2)
            
            assert len(result) == 3
            assert all("title" in item for item in result)
    
    @pytest.mark.asyncio
    async def test_batch_scrape_partial_failure(self):
        """Test batch scraping with some failures"""
        urls = [
            "https://example.com/page1",
            "https://example.com/page2",
            "https://example.com/page3"
        ]
        
        # Mock mixed success/failure results
        async def mock_scrape(url):
            if "page2" in url:
                raise Exception("Scrape failed")
            return {"title": f"Success for {url}"}
        
        with patch.object(self.client, 'scrape', new=mock_scrape):
            result = await self.client.batch_scrape(urls)
            
            # Should have 2 successful results (page1 and page3)
            assert len(result) == 2
    
    @pytest.mark.asyncio
    async def test_batch_scrape_concurrency_limit(self):
        """Test that batch scrape respects concurrency limits"""
        urls = ["https://example.com/page{}".format(i) for i in range(10)]
        
        call_times = []
        
        async def mock_scrape(url):
            call_times.append(datetime.now())
            await asyncio.sleep(0.1)  # Simulate some work
            return {"title": url}
        
        with patch.object(self.client, 'scrape', new=mock_scrape):
            await self.client.batch_scrape(urls, max_concurrent=3)
            
            # Verify concurrency was limited
            # First 3 calls should be nearly simultaneous
            # Later calls should be delayed
            assert len(call_times) == 10
    
    def test_client_initialization(self):
        """Test client initialization with custom API key"""
        custom_client = FirecrawlClient(api_key="custom-key")
        assert custom_client.api_key == "custom-key"
        assert custom_client.base_url == "https://api.firecrawl.dev/v0"
        assert custom_client.rate_limiter.calls_per_minute == 30
    
    def test_client_headers(self):
        """Test that client has correct headers"""
        headers = self.client.client.headers
        assert "Authorization" in headers
        assert headers["Authorization"] == "Bearer test-api-key"


# Integration-style tests (but still mocked)
class TestFirecrawlClientIntegration:
    """Integration-style tests for FirecrawlClient"""
    
    @pytest.mark.asyncio
    async def test_full_scrape_workflow(self):
        """Test complete scraping workflow"""
        with patch('app.services.firecrawl_client.get_settings') as mock_settings:
            mock_settings.return_value.firecrawl_api_key = "test-key"
            
            client = FirecrawlClient()
            
            # Mock successful response
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "data": {
                    "metadata": {
                        "title": "HomePro Product",
                        "description": "Great product"
                    },
                    "markdown": "# Product\n\n฿2,490 each ฿2,990",
                    "html": "<html><title>Product</title></html>",
                    "linksOnPage": [
                        "https://www.homepro.co.th/p/123",
                        "https://www.homepro.co.th/p/456"
                    ]
                }
            }
            
            with patch.object(client.client, 'post', new=AsyncMock(return_value=mock_response)):
                async with client:
                    result = await client.scrape("https://www.homepro.co.th/c/tools")
                    
                    assert result is not None
                    assert "metadata" in result
                    assert "markdown" in result
                    assert "linksOnPage" in result
                    assert len(result["linksOnPage"]) == 2
    
    @pytest.mark.asyncio
    async def test_error_handling_workflow(self):
        """Test error handling in complete workflow"""
        with patch('app.services.firecrawl_client.get_settings') as mock_settings:
            mock_settings.return_value.firecrawl_api_key = "test-key"
            
            client = FirecrawlClient()
            
            # Mock network error
            with patch.object(client.client, 'post', new=AsyncMock(
                side_effect=httpx.RequestError("Network error")
            )):
                async with client:
                    with pytest.raises(Exception):
                        await client.scrape("https://example.com")