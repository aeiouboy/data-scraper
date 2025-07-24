"""Performance tests for scraping operations."""

import pytest
import asyncio
import time
from datetime import datetime
from unittest.mock import patch, AsyncMock
from concurrent.futures import ThreadPoolExecutor
import statistics

from tests.mock_scraper_manager import ScraperManager
from src.models.product import Product
from tests.utils import PerformanceTestHelper, MockHTTPClient, ScraperTestHelper
from tests.fixtures.database import test_session


@pytest.mark.performance
@pytest.mark.slow
class TestScrapingPerformance:
    """Test scraping performance and scalability."""
    
    @pytest.fixture
    def performance_helper(self):
        """Create performance test helper."""
        return PerformanceTestHelper()
    
    @pytest.fixture
    def mock_http_client(self):
        """Create mock HTTP client with realistic delays."""
        client = MockHTTPClient()
        
        # Add realistic response times
        async def delayed_get(url, **kwargs):
            # Simulate network delay (50-200ms)
            await asyncio.sleep(0.05 + (hash(url) % 150) / 1000)
            return await client.get(url, **kwargs)
        
        client.get = delayed_get
        return client
    
    @pytest.mark.asyncio
    async def test_single_product_scraping_performance(self, performance_helper, mock_http_client):
        """Test performance of scraping a single product."""
        scraper_manager = ScraperManager()
        
        # Set up mock response
        product_html = ScraperTestHelper.generate_product_html()
        mock_http_client.set_response(
            "https://www.homepro.co.th/p/12345",
            product_html
        )
        
        # Test single product scraping
        performance_helper.start_timer("single_product")
        
        with patch('httpx.AsyncClient.get', mock_http_client.get):
            product = await scraper_manager.scrape_product("https://www.homepro.co.th/p/12345")
        
        performance_helper.stop_timer("single_product")
        
        # Assert performance
        assert product is not None
        performance_helper.assert_performance("single_product", max_duration=1.0)
    
    @pytest.mark.asyncio
    async def test_category_page_scraping_performance(self, performance_helper, mock_http_client):
        """Test performance of scraping a category page."""
        scraper_manager = ScraperManager()
        
        # Set up mock responses for category and products
        category_html = ScraperTestHelper.generate_category_html(product_count=50)
        mock_http_client.set_response(
            "https://www.homepro.co.th/c/tools",
            category_html
        )
        
        # Mock individual product pages
        for i in range(50):
            product_html = ScraperTestHelper.generate_product_html(
                name=f"Product {i}",
                sku=f"SKU{i:03d}",
                price=f"฿{1000 + i * 100}"
            )
            mock_http_client.set_response(
                f"https://www.homepro.co.th/product/{i}",
                product_html
            )
        
        performance_helper.start_timer("category_page")
        
        with patch('httpx.AsyncClient.get', mock_http_client.get):
            products = await scraper_manager.scrape_category(
                "https://www.homepro.co.th/c/tools",
                max_pages=1
            )
        
        performance_helper.stop_timer("category_page")
        
        # Assert performance
        assert len(products) == 50
        performance_helper.assert_performance("category_page", max_duration=5.0)
        
        # Calculate average time per product
        avg_time_per_product = performance_helper.get_timing("category_page") / 50
        assert avg_time_per_product < 0.1  # Should be under 100ms per product
    
    @pytest.mark.asyncio
    async def test_concurrent_scraping_performance(self, performance_helper, mock_http_client):
        """Test performance of concurrent scraping operations."""
        scraper_manager = ScraperManager()
        
        # Set up mock responses for multiple categories
        categories = ["tools", "paint", "tiles", "bathroom", "electrical"]
        for category in categories:
            category_html = ScraperTestHelper.generate_category_html(product_count=20)
            mock_http_client.set_response(
                f"https://www.homepro.co.th/c/{category}",
                category_html
            )
            
            # Mock products in each category
            for i in range(20):
                product_html = ScraperTestHelper.generate_product_html(
                    name=f"{category} Product {i}",
                    sku=f"{category.upper()}{i:03d}"
                )
                mock_http_client.set_response(
                    f"https://www.homepro.co.th/{category}/product/{i}",
                    product_html
                )
        
        performance_helper.start_timer("concurrent_scraping")
        
        # Scrape all categories concurrently
        with patch('httpx.AsyncClient.get', mock_http_client.get):
            tasks = [
                scraper_manager.scrape_category(f"https://www.homepro.co.th/c/{cat}")
                for cat in categories
            ]
            results = await asyncio.gather(*tasks)
        
        performance_helper.stop_timer("concurrent_scraping")
        
        # Assert performance
        total_products = sum(len(r) for r in results)
        assert total_products == 100  # 5 categories * 20 products
        
        # Concurrent scraping should be faster than sequential
        performance_helper.assert_performance("concurrent_scraping", max_duration=3.0)
        
        # Verify concurrency benefit
        sequential_estimate = 0.1 * total_products  # Estimated sequential time
        concurrent_time = performance_helper.get_timing("concurrent_scraping")
        assert concurrent_time < sequential_estimate * 0.5  # At least 2x faster
    
    @pytest.mark.asyncio
    async def test_rate_limiting_performance(self, performance_helper):
        """Test performance impact of rate limiting."""
        from src.scrapers.rate_limiter import RateLimiter
        
        # Test different rate limits
        rate_limits = [10, 50, 100, 200]  # requests per second
        results = {}
        
        for limit in rate_limits:
            rate_limiter = RateLimiter(max_requests_per_second=limit)
            
            performance_helper.start_timer(f"rate_limit_{limit}")
            
            # Make 100 requests
            start_time = time.time()
            for _ in range(100):
                await rate_limiter.acquire()
            
            performance_helper.stop_timer(f"rate_limit_{limit}")
            
            duration = performance_helper.get_timing(f"rate_limit_{limit}")
            actual_rate = 100 / duration
            
            results[limit] = {
                "duration": duration,
                "actual_rate": actual_rate,
                "efficiency": actual_rate / limit
            }
        
        # Verify rate limiting behavior
        for limit, result in results.items():
            # Actual rate should not exceed limit (with small tolerance)
            assert result["actual_rate"] <= limit * 1.1
            # Efficiency should be high for reasonable limits
            if limit >= 50:
                assert result["efficiency"] > 0.8
    
    @pytest.mark.asyncio
    async def test_memory_usage_during_bulk_scraping(self, test_session):
        """Test memory usage during bulk scraping operations."""
        import psutil
        import os
        
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        # Create large number of products in batches
        batch_size = 100
        total_batches = 10
        
        for batch in range(total_batches):
            products = []
            for i in range(batch_size):
                product = Product(
                    retailer_code="homepro",
                    sku=f"PERF{batch:03d}{i:03d}",
                    name=f"Performance Test Product {batch}-{i}",
                    current_price=1000.0 + i,
                    product_url=f"https://test.com/p/{batch}/{i}"
                )
                products.append(product)
            
            test_session.bulk_insert_mappings(Product, [p.__dict__ for p in products])
            test_session.commit()
            
            # Check memory growth
            current_memory = process.memory_info().rss / 1024 / 1024
            memory_growth = current_memory - initial_memory
            
            # Memory growth should be reasonable (less than 10MB per 100 products)
            assert memory_growth < (batch + 1) * 10
        
        # Final memory check
        final_memory = process.memory_info().rss / 1024 / 1024
        total_memory_growth = final_memory - initial_memory
        
        # Total memory growth should be reasonable
        assert total_memory_growth < 150  # Less than 150MB for 1000 products
    
    @pytest.mark.asyncio
    async def test_database_query_performance(self, test_session, performance_helper):
        """Test database query performance with large datasets."""
        # Create test data
        from tests.utils import DatabaseTestHelper
        
        # Create 1000 products
        products = DatabaseTestHelper.create_test_products(test_session, count=1000)
        
        # Test various query patterns
        queries = {
            "all_products": lambda: test_session.query(Product).all(),
            "filtered_by_retailer": lambda: test_session.query(Product).filter_by(
                retailer_code="homepro"
            ).all(),
            "price_range": lambda: test_session.query(Product).filter(
                Product.current_price.between(1000, 5000)
            ).all(),
            "pagination": lambda: test_session.query(Product).limit(50).offset(100).all(),
            "aggregation": lambda: test_session.query(Product).count()
        }
        
        for query_name, query_func in queries.items():
            performance_helper.start_timer(query_name)
            result = query_func()
            performance_helper.stop_timer(query_name)
            
            # All queries should complete quickly
            performance_helper.assert_performance(query_name, max_duration=0.5)
    
    @pytest.mark.asyncio
    async def test_scraping_throughput(self, mock_http_client):
        """Test maximum scraping throughput."""
        scraper_manager = ScraperManager()
        
        # Set up mock responses
        for i in range(1000):
            mock_http_client.set_response(
                f"https://test.com/product/{i}",
                ScraperTestHelper.generate_product_html(sku=f"THRU{i:04d}")
            )
        
        # Measure throughput
        start_time = time.time()
        scraped_count = 0
        duration_limit = 10.0  # 10 seconds
        
        with patch('httpx.AsyncClient.get', mock_http_client.get):
            while time.time() - start_time < duration_limit:
                # Scrape in batches
                batch_tasks = [
                    scraper_manager.scrape_product(f"https://test.com/product/{scraped_count + j}")
                    for j in range(10)
                ]
                
                results = await asyncio.gather(*batch_tasks, return_exceptions=True)
                successful = sum(1 for r in results if r and not isinstance(r, Exception))
                scraped_count += successful
                
                if scraped_count >= 1000:
                    break
        
        elapsed_time = time.time() - start_time
        throughput = scraped_count / elapsed_time
        
        # Should achieve reasonable throughput
        assert throughput > 50  # At least 50 products per second
        
        print(f"Scraping throughput: {throughput:.2f} products/second")
    
    @pytest.mark.asyncio
    async def test_response_time_percentiles(self, mock_http_client, performance_helper):
        """Test response time percentiles for quality of service."""
        scraper_manager = ScraperManager()
        response_times = []
        
        # Set up mock responses with variable delays
        for i in range(100):
            mock_http_client.set_response(
                f"https://test.com/product/{i}",
                ScraperTestHelper.generate_product_html()
            )
        
        # Collect response times
        with patch('httpx.AsyncClient.get', mock_http_client.get):
            for i in range(100):
                start = time.time()
                await scraper_manager.scrape_product(f"https://test.com/product/{i}")
                response_times.append(time.time() - start)
        
        # Calculate percentiles
        response_times.sort()
        p50 = response_times[50]
        p95 = response_times[95]
        p99 = response_times[99]
        
        # Assert SLA requirements
        assert p50 < 0.2  # 50th percentile under 200ms
        assert p95 < 0.5  # 95th percentile under 500ms
        assert p99 < 1.0  # 99th percentile under 1 second
        
        print(f"Response time percentiles - P50: {p50*1000:.0f}ms, P95: {p95*1000:.0f}ms, P99: {p99*1000:.0f}ms")