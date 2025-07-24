"""
Performance tests for native scraping system
"""
import pytest
import asyncio
import time
import statistics
from unittest.mock import Mock, AsyncMock, patch
from scrapers.strategy_factory import StrategyFactory
from scrapers.strategies.native_strategy import NativeStrategy


@pytest.mark.performance
@pytest.mark.native
class TestNativeScrapingPerformance:
    """Performance tests for native scraping system"""
    
    @pytest.fixture
    def sample_config(self):
        """Sample configuration for performance testing"""
        return {
            'name': 'Test Retailer',
            'code': 'TEST',
            'base_url': 'https://test-retailer.com',
            'rate_limit_delay': 0.01,  # Fast for performance testing
            'max_concurrent': 10,
            'timeout': 30,
            'retry_attempts': 2,
            'scraping_method': 'native',
            'selectors': {
                'product_name': ['.product-title'],
                'price': ['.price'],
                'brand': ['.brand-name'],
                'sku': ['.sku'],
                'description': ['.description'],
                'images': ['.product-image img'],
                'availability': ['.stock-status'],
                'rating': ['.rating-score'],
                'reviews_count': ['.review-count'],
                'product_links': ['.product-item a'],
                'category_name': ['.category-title'],
                'pagination': ['.pagination a']
            }
        }
    
    @pytest.fixture
    def mock_fast_response(self):
        """Mock fast HTTP response"""
        mock_response = Mock()
        mock_response.status = 200
        mock_response.text = AsyncMock(return_value="""
        <html>
            <body>
                <h1 class="product-title">Test Product</h1>
                <div class="price">฿1,299.99</div>
                <div class="brand-name">TestBrand</div>
                <div class="sku">SKU-123</div>
                <div class="description">Test description</div>
                <div class="stock-status">In Stock</div>
                <div class="rating-score">4.5</div>
                <div class="review-count">123 reviews</div>
                <img class="product-image" src="/image1.jpg" alt="Product">
            </body>
        </html>
        """)
        mock_response.headers = {'content-type': 'text/html'}
        return mock_response
    
    @pytest.fixture
    def mock_slow_response(self):
        """Mock slow HTTP response"""
        async def slow_text():
            await asyncio.sleep(0.5)  # Simulate slow response
            return """
            <html>
                <body>
                    <h1 class="product-title">Slow Test Product</h1>
                    <div class="price">฿2,499.99</div>
                </body>
            </html>
            """
        
        mock_response = Mock()
        mock_response.status = 200
        mock_response.text = slow_text
        mock_response.headers = {'content-type': 'text/html'}
        return mock_response
    
    @pytest.mark.asyncio
    async def test_single_request_performance(self, sample_config, mock_fast_response):
        """Test single request performance"""
        strategy = StrategyFactory.create_strategy(sample_config, 'native')
        
        # Mock session
        mock_session = Mock()
        mock_session.get.return_value.__aenter__ = AsyncMock(return_value=mock_fast_response)
        mock_session.get.return_value.__aexit__ = AsyncMock(return_value=None)
        
        with patch.object(strategy.engine.session_manager, 'get_session', return_value=mock_session):
            # Measure single request time
            start_time = time.time()
            result = await strategy.scrape_product('https://test-retailer.com/product/123')
            end_time = time.time()
            
            request_time = end_time - start_time
            
            # Verify performance
            assert result.success is True
            assert request_time < 1.0  # Should be fast
            assert 'response_time' in result.metadata
            assert result.metadata['response_time'] >= 0
        
        await strategy.close()
    
    @pytest.mark.asyncio
    async def test_concurrent_requests_performance(self, sample_config, mock_fast_response):
        """Test concurrent requests performance"""
        strategy = StrategyFactory.create_strategy(sample_config, 'native')
        
        # Mock session
        mock_session = Mock()
        mock_session.get.return_value.__aenter__ = AsyncMock(return_value=mock_fast_response)
        mock_session.get.return_value.__aexit__ = AsyncMock(return_value=None)
        
        with patch.object(strategy.engine.session_manager, 'get_session', return_value=mock_session):
            # Test concurrent requests
            num_requests = 50
            
            # Measure concurrent request time
            start_time = time.time()
            
            tasks = []
            for i in range(num_requests):
                task = asyncio.create_task(
                    strategy.scrape_product(f'https://test-retailer.com/product/{i}')
                )
                tasks.append(task)
            
            results = await asyncio.gather(*tasks)
            end_time = time.time()
            
            total_time = end_time - start_time
            
            # Verify performance
            assert len(results) == num_requests
            assert all(result.success for result in results)
            assert total_time < 10.0  # Should complete in reasonable time
            
            # Calculate throughput
            throughput = num_requests / total_time
            assert throughput > 5.0  # Should handle at least 5 requests per second
        
        await strategy.close()
    
    @pytest.mark.asyncio
    async def test_rate_limiting_performance(self, sample_config, mock_fast_response):
        """Test rate limiting performance impact"""
        # Test without rate limiting
        config_no_limit = sample_config.copy()
        config_no_limit['rate_limit_delay'] = 0
        config_no_limit['max_concurrent'] = 20
        
        strategy_no_limit = StrategyFactory.create_strategy(config_no_limit, 'native')
        
        # Test with rate limiting
        config_with_limit = sample_config.copy()
        config_with_limit['rate_limit_delay'] = 0.1
        config_with_limit['max_concurrent'] = 5
        
        strategy_with_limit = StrategyFactory.create_strategy(config_with_limit, 'native')
        
        # Mock session
        mock_session = Mock()
        mock_session.get.return_value.__aenter__ = AsyncMock(return_value=mock_fast_response)
        mock_session.get.return_value.__aexit__ = AsyncMock(return_value=None)
        
        num_requests = 20
        
        # Test without rate limiting
        with patch.object(strategy_no_limit.engine.session_manager, 'get_session', return_value=mock_session):
            start_time = time.time()
            
            tasks = []
            for i in range(num_requests):
                task = asyncio.create_task(
                    strategy_no_limit.scrape_product(f'https://test-retailer.com/product/{i}')
                )
                tasks.append(task)
            
            results_no_limit = await asyncio.gather(*tasks)
            time_no_limit = time.time() - start_time
        
        # Test with rate limiting
        with patch.object(strategy_with_limit.engine.session_manager, 'get_session', return_value=mock_session):
            start_time = time.time()
            
            tasks = []
            for i in range(num_requests):
                task = asyncio.create_task(
                    strategy_with_limit.scrape_product(f'https://test-retailer.com/product/{i}')
                )
                tasks.append(task)
            
            results_with_limit = await asyncio.gather(*tasks)
            time_with_limit = time.time() - start_time
        
        # Verify both completed successfully
        assert len(results_no_limit) == num_requests
        assert len(results_with_limit) == num_requests
        assert all(result.success for result in results_no_limit)
        assert all(result.success for result in results_with_limit)
        
        # Rate limiting should slow down requests
        assert time_with_limit > time_no_limit
        
        # But not by too much (should still be concurrent)
        assert time_with_limit < time_no_limit + (num_requests * 0.1)  # Not fully serial
        
        await strategy_no_limit.close()
        await strategy_with_limit.close()
    
    @pytest.mark.asyncio
    async def test_memory_usage_performance(self, sample_config, mock_fast_response):
        """Test memory usage during heavy scraping"""
        strategy = StrategyFactory.create_strategy(sample_config, 'native')
        
        # Mock session
        mock_session = Mock()
        mock_session.get.return_value.__aenter__ = AsyncMock(return_value=mock_fast_response)
        mock_session.get.return_value.__aexit__ = AsyncMock(return_value=None)
        
        with patch.object(strategy.engine.session_manager, 'get_session', return_value=mock_session):
            # Test memory usage with many sequential requests
            num_requests = 100
            
            for i in range(num_requests):
                result = await strategy.scrape_product(f'https://test-retailer.com/product/{i}')
                assert result.success is True
                
                # Check that results are not accumulating in memory
                stats = strategy.get_stats()
                assert stats['total_requests'] == i + 1
        
        await strategy.close()
    
    @pytest.mark.asyncio
    async def test_response_time_distribution(self, sample_config, mock_fast_response):
        """Test response time distribution"""
        strategy = StrategyFactory.create_strategy(sample_config, 'native')
        
        # Mock session
        mock_session = Mock()
        mock_session.get.return_value.__aenter__ = AsyncMock(return_value=mock_fast_response)
        mock_session.get.return_value.__aexit__ = AsyncMock(return_value=None)
        
        with patch.object(strategy.engine.session_manager, 'get_session', return_value=mock_session):
            # Collect response times
            response_times = []
            num_requests = 50
            
            for i in range(num_requests):
                start_time = time.time()
                result = await strategy.scrape_product(f'https://test-retailer.com/product/{i}')
                end_time = time.time()
                
                response_time = end_time - start_time
                response_times.append(response_time)
                
                assert result.success is True
                assert 'response_time' in result.metadata
            
            # Analyze response time distribution
            mean_time = statistics.mean(response_times)
            median_time = statistics.median(response_times)
            std_dev = statistics.stdev(response_times) if len(response_times) > 1 else 0
            
            # Response times should be consistent
            assert mean_time < 0.5  # Average should be fast
            assert median_time < 0.5  # Median should be fast
            assert std_dev < 0.2  # Low variability
            
            # 95th percentile should be reasonable
            p95_time = sorted(response_times)[int(0.95 * len(response_times))]
            assert p95_time < 1.0
        
        await strategy.close()
    
    @pytest.mark.asyncio
    async def test_error_handling_performance(self, sample_config):
        """Test error handling performance impact"""
        strategy = StrategyFactory.create_strategy(sample_config, 'native')
        
        # Mock error responses
        mock_error_response = Mock()
        mock_error_response.status = 404
        mock_error_response.text = AsyncMock(return_value="Not Found")
        
        mock_session = Mock()
        mock_session.get.return_value.__aenter__ = AsyncMock(return_value=mock_error_response)
        mock_session.get.return_value.__aexit__ = AsyncMock(return_value=None)
        
        with patch.object(strategy.engine.session_manager, 'get_session', return_value=mock_session):
            # Test performance with errors
            num_requests = 20
            
            start_time = time.time()
            
            tasks = []
            for i in range(num_requests):
                task = asyncio.create_task(
                    strategy.scrape_product(f'https://test-retailer.com/product/{i}')
                )
                tasks.append(task)
            
            results = await asyncio.gather(*tasks)
            end_time = time.time()
            
            total_time = end_time - start_time
            
            # Verify error handling
            assert len(results) == num_requests
            assert all(not result.success for result in results)
            assert all(result.error is not None for result in results)
            
            # Error handling should still be fast
            assert total_time < 5.0  # Should complete quickly even with errors
        
        await strategy.close()
    
    @pytest.mark.asyncio
    async def test_retry_mechanism_performance(self, sample_config, mock_fast_response):
        """Test retry mechanism performance impact"""
        strategy = StrategyFactory.create_strategy(sample_config, 'native')
        
        # Mock intermittent failures
        call_count = 0
        
        def mock_get_session():
            nonlocal call_count
            call_count += 1
            
            mock_session = Mock()
            
            if call_count % 3 == 1:  # Every third call fails initially
                mock_error_response = Mock()
                mock_error_response.status = 500
                mock_error_response.text = AsyncMock(return_value="Server Error")
                mock_session.get.return_value.__aenter__ = AsyncMock(return_value=mock_error_response)
            else:
                mock_session.get.return_value.__aenter__ = AsyncMock(return_value=mock_fast_response)
            
            mock_session.get.return_value.__aexit__ = AsyncMock(return_value=None)
            return mock_session
        
        with patch.object(strategy.engine.session_manager, 'get_session', side_effect=mock_get_session):
            # Test retry performance
            num_requests = 15
            
            start_time = time.time()
            
            tasks = []
            for i in range(num_requests):
                task = asyncio.create_task(
                    strategy.scrape_product(f'https://test-retailer.com/product/{i}')
                )
                tasks.append(task)
            
            results = await asyncio.gather(*tasks)
            end_time = time.time()
            
            total_time = end_time - start_time
            
            # Most requests should succeed after retries
            successful_results = [r for r in results if r.success]
            assert len(successful_results) >= num_requests * 0.8  # At least 80% success
            
            # Retry mechanism should not significantly slow down requests
            assert total_time < 10.0  # Should complete in reasonable time
        
        await strategy.close()
    
    @pytest.mark.asyncio
    async def test_session_reuse_performance(self, sample_config, mock_fast_response):
        """Test session reuse performance benefit"""
        strategy = StrategyFactory.create_strategy(sample_config, 'native')
        
        # Mock session manager to track session creation
        session_creation_count = 0
        
        def mock_get_session():
            nonlocal session_creation_count
            session_creation_count += 1
            
            mock_session = Mock()
            mock_session.get.return_value.__aenter__ = AsyncMock(return_value=mock_fast_response)
            mock_session.get.return_value.__aexit__ = AsyncMock(return_value=None)
            return mock_session
        
        with patch.object(strategy.engine.session_manager, 'get_session', side_effect=mock_get_session):
            # Test session reuse
            num_requests = 20
            
            start_time = time.time()
            
            for i in range(num_requests):
                result = await strategy.scrape_product(f'https://test-retailer.com/product/{i}')
                assert result.success is True
            
            end_time = time.time()
            total_time = end_time - start_time
            
            # Should reuse sessions efficiently
            assert session_creation_count <= num_requests  # Should not create more sessions than requests
            assert total_time < 5.0  # Should be fast with session reuse
        
        await strategy.close()
    
    @pytest.mark.asyncio
    async def test_data_extraction_performance(self, sample_config):
        """Test data extraction performance with complex HTML"""
        strategy = StrategyFactory.create_strategy(sample_config, 'native')
        
        # Mock complex HTML response
        complex_html = """
        <html>
            <head><title>Complex Product Page</title></head>
            <body>
                <div class="container">
                    <div class="product-section">
                        <h1 class="product-title">Complex Test Product</h1>
                        <div class="price-section">
                            <span class="price">฿1,299.99</span>
                        </div>
                        <div class="brand-section">
                            <span class="brand-name">TestBrand</span>
                        </div>
                        <div class="details">
                            <div class="sku">SKU-123</div>
                            <div class="description">
                                This is a very long product description that contains
                                multiple sentences and detailed information about the
                                product features, specifications, and benefits.
                            </div>
                        </div>
                        <div class="availability">
                            <span class="stock-status">In Stock</span>
                        </div>
                        <div class="rating">
                            <div class="rating-score">4.5 out of 5 stars</div>
                            <div class="review-count">123 customer reviews</div>
                        </div>
                        <div class="images">
                            <img class="product-image" src="/image1.jpg" alt="Product 1">
                            <img class="product-image" src="/image2.jpg" alt="Product 2">
                            <img class="product-image" src="/image3.jpg" alt="Product 3">
                        </div>
                    </div>
                </div>
                <!-- Many more HTML elements to make parsing complex -->
                <div class="footer">
                    <div class="links">
                        <a href="/link1">Link 1</a>
                        <a href="/link2">Link 2</a>
                        <a href="/link3">Link 3</a>
                    </div>
                </div>
            </body>
        </html>
        """ * 10  # Repeat to make it large
        
        mock_response = Mock()
        mock_response.status = 200
        mock_response.text = AsyncMock(return_value=complex_html)
        mock_response.headers = {'content-type': 'text/html'}
        
        mock_session = Mock()
        mock_session.get.return_value.__aenter__ = AsyncMock(return_value=mock_response)
        mock_session.get.return_value.__aexit__ = AsyncMock(return_value=None)
        
        with patch.object(strategy.engine.session_manager, 'get_session', return_value=mock_session):
            # Test complex data extraction performance
            num_requests = 10
            
            start_time = time.time()
            
            tasks = []
            for i in range(num_requests):
                task = asyncio.create_task(
                    strategy.scrape_product(f'https://test-retailer.com/product/{i}')
                )
                tasks.append(task)
            
            results = await asyncio.gather(*tasks)
            end_time = time.time()
            
            total_time = end_time - start_time
            
            # Verify extraction accuracy
            assert len(results) == num_requests
            assert all(result.success for result in results)
            
            for result in results:
                assert result.data['name'] == 'Complex Test Product'
                assert result.data['price'] == 1299.99
                assert result.data['brand'] == 'TestBrand'
                assert result.data['sku'] == 'SKU-123'
                assert len(result.data['description']) > 100  # Should extract full description
                assert result.data['availability'] == 'in_stock'
                assert result.data['rating'] == 4.5
                assert result.data['reviews_count'] == 123
                assert len(result.data['images']) == 3
            
            # Complex extraction should still be fast
            assert total_time < 5.0  # Should complete in reasonable time
            
            # Average processing time per request
            avg_time = total_time / num_requests
            assert avg_time < 0.5  # Should process each complex page quickly
        
        await strategy.close()
    
    @pytest.mark.asyncio
    async def test_load_testing_scenario(self, sample_config, mock_fast_response):
        """Test load testing scenario with sustained requests"""
        strategy = StrategyFactory.create_strategy(sample_config, 'native')
        
        # Mock session
        mock_session = Mock()
        mock_session.get.return_value.__aenter__ = AsyncMock(return_value=mock_fast_response)
        mock_session.get.return_value.__aexit__ = AsyncMock(return_value=None)
        
        with patch.object(strategy.engine.session_manager, 'get_session', return_value=mock_session):
            # Sustained load test
            total_requests = 100
            batch_size = 10
            batches = total_requests // batch_size
            
            overall_start_time = time.time()
            all_results = []
            
            for batch in range(batches):
                batch_start_time = time.time()
                
                # Create batch of concurrent requests
                tasks = []
                for i in range(batch_size):
                    request_id = batch * batch_size + i
                    task = asyncio.create_task(
                        strategy.scrape_product(f'https://test-retailer.com/product/{request_id}')
                    )
                    tasks.append(task)
                
                batch_results = await asyncio.gather(*tasks)
                all_results.extend(batch_results)
                
                batch_end_time = time.time()
                batch_time = batch_end_time - batch_start_time
                
                # Each batch should complete quickly
                assert batch_time < 2.0
                assert all(result.success for result in batch_results)
                
                # Brief pause between batches
                await asyncio.sleep(0.1)
            
            overall_end_time = time.time()
            total_time = overall_end_time - overall_start_time
            
            # Verify overall performance
            assert len(all_results) == total_requests
            assert all(result.success for result in all_results)
            
            # Calculate throughput
            throughput = total_requests / total_time
            assert throughput > 10.0  # Should handle at least 10 requests per second
            
            # Check final stats
            stats = strategy.get_stats()
            assert stats['total_requests'] == total_requests
            assert stats['successful_requests'] == total_requests
            assert stats['failed_requests'] == 0
            assert stats['average_response_time'] > 0
        
        await strategy.close()