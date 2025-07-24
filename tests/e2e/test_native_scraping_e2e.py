"""
End-to-End tests for native scraping system using Playwright
"""
import pytest
import asyncio
from playwright.async_api import async_playwright, Page, Browser
from scrapers.strategy_factory import StrategyFactory
from scrapers.strategies.native_strategy import NativeStrategy


@pytest.mark.e2e
@pytest.mark.native
class TestNativeScrapingE2E:
    """End-to-end tests for native scraping system"""
    
    @pytest.fixture(scope="class")
    async def browser(self):
        """Create browser instance for testing"""
        playwright = await async_playwright().start()
        browser = await playwright.chromium.launch(headless=True)
        yield browser
        await browser.close()
        await playwright.stop()
    
    @pytest.fixture
    async def page(self, browser):
        """Create page instance for testing"""
        page = await browser.new_page()
        yield page
        await page.close()
    
    @pytest.fixture
    def sample_config(self):
        """Sample retailer configuration for E2E testing"""
        return {
            'name': 'Test Retailer',
            'code': 'TEST',
            'base_url': 'https://test-retailer.com',
            'rate_limit_delay': 0.1,
            'max_concurrent': 2,
            'timeout': 30,
            'retry_attempts': 3,
            'scraping_method': 'native',
            'selectors': {
                'product_name': ['.product-title', 'h1.title'],
                'price': ['.price', '.cost'],
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
    async def mock_server(self, page):
        """Set up mock server responses"""
        # Mock product page
        await page.route('**/product/*', lambda route: route.fulfill(
            status=200,
            content_type='text/html',
            body="""
            <html>
                <head><title>Test Product</title></head>
                <body>
                    <h1 class="product-title">High-Quality Test Product</h1>
                    <div class="price">฿1,299.99</div>
                    <div class="brand-name">TestBrand</div>
                    <div class="sku">SKU-12345</div>
                    <div class="description">This is a comprehensive test product</div>
                    <div class="stock-status">In Stock</div>
                    <div class="rating-score">4.5 out of 5 stars</div>
                    <div class="review-count">123 reviews</div>
                    <img class="product-image" src="/images/product1.jpg" alt="Product">
                </body>
            </html>
            """
        ))
        
        # Mock category page
        await page.route('**/category/*', lambda route: route.fulfill(
            status=200,
            content_type='text/html',
            body="""
            <html>
                <head><title>Electronics Category</title></head>
                <body>
                    <h1 class="category-title">Electronics</h1>
                    <div class="product-grid">
                        <div class="product-item">
                            <a href="/product/1">Product 1</a>
                        </div>
                        <div class="product-item">
                            <a href="/product/2">Product 2</a>
                        </div>
                        <div class="product-item">
                            <a href="/product/3">Product 3</a>
                        </div>
                    </div>
                    <div class="pagination">
                        <a href="/category/electronics?page=1">1</a>
                        <a href="/category/electronics?page=2">2</a>
                        <a href="/category/electronics?page=3">3</a>
                    </div>
                </body>
            </html>
            """
        ))
        
        # Mock search page
        await page.route('**/search*', lambda route: route.fulfill(
            status=200,
            content_type='text/html',
            body="""
            <html>
                <head><title>Search Results</title></head>
                <body>
                    <div class="search-results">
                        <div class="product-item">
                            <a href="/product/search-1">Search Result 1</a>
                        </div>
                        <div class="product-item">
                            <a href="/product/search-2">Search Result 2</a>
                        </div>
                    </div>
                    <div class="pagination">
                        <a href="/search?q=test&page=1">1</a>
                        <a href="/search?q=test&page=2">2</a>
                    </div>
                </body>
            </html>
            """
        ))
        
        # Mock error page
        await page.route('**/error/*', lambda route: route.fulfill(
            status=404,
            content_type='text/html',
            body="""
            <html>
                <head><title>Page Not Found</title></head>
                <body>
                    <h1>404 - Page Not Found</h1>
                    <p>The requested page could not be found.</p>
                </body>
            </html>
            """
        ))
        
        return page
    
    @pytest.mark.asyncio
    async def test_complete_product_scraping_workflow(self, sample_config, mock_server):
        """Test complete product scraping workflow end-to-end"""
        # Create strategy
        strategy = StrategyFactory.create_strategy(sample_config, 'native')
        
        # Test product scraping
        result = await strategy.scrape_product('https://test-retailer.com/product/123')
        
        # Verify results
        assert result.success is True
        assert result.data['name'] == 'High-Quality Test Product'
        assert result.data['price'] == 1299.99
        assert result.data['brand'] == 'TestBrand'
        assert result.data['sku'] == 'SKU-12345'
        assert result.data['description'] == 'This is a comprehensive test product'
        assert result.data['availability'] == 'in_stock'
        assert result.data['rating'] == 4.5
        assert result.data['reviews_count'] == 123
        assert len(result.data['images']) > 0
        
        # Verify metadata
        assert 'response_time' in result.metadata
        assert 'quality_score' in result.metadata
        assert result.metadata['response_time'] >= 0
        assert result.metadata['quality_score'] >= 0.5
        
        # Clean up
        await strategy.close()
    
    @pytest.mark.asyncio
    async def test_complete_category_scraping_workflow(self, sample_config, mock_server):
        """Test complete category scraping workflow end-to-end"""
        # Create strategy
        strategy = StrategyFactory.create_strategy(sample_config, 'native')
        
        # Test category scraping
        result = await strategy.scrape_category('https://test-retailer.com/category/electronics')
        
        # Verify results
        assert result.success is True
        assert result.data['category_name'] == 'Electronics'
        assert len(result.data['product_links']) == 3
        assert 'https://test-retailer.com/product/1' in result.data['product_links']
        assert 'https://test-retailer.com/product/2' in result.data['product_links']
        assert 'https://test-retailer.com/product/3' in result.data['product_links']
        
        # Verify pagination
        assert 'pagination' in result.data
        assert 'total_pages' in result.data['pagination']
        assert result.data['pagination']['total_pages'] == 3
        
        # Clean up
        await strategy.close()
    
    @pytest.mark.asyncio
    async def test_complete_search_workflow(self, sample_config, mock_server):
        """Test complete search workflow end-to-end"""
        # Create strategy
        strategy = StrategyFactory.create_strategy(sample_config, 'native')
        
        # Test search scraping
        result = await strategy.scrape_search('power tools')
        
        # Verify results
        assert result.success is True
        assert len(result.data['product_links']) == 2
        assert 'https://test-retailer.com/product/search-1' in result.data['product_links']
        assert 'https://test-retailer.com/product/search-2' in result.data['product_links']
        
        # Verify pagination
        assert 'pagination' in result.data
        assert 'total_pages' in result.data['pagination']
        assert result.data['pagination']['total_pages'] == 2
        
        # Clean up
        await strategy.close()
    
    @pytest.mark.asyncio
    async def test_error_handling_workflow(self, sample_config, mock_server):
        """Test error handling workflow end-to-end"""
        # Create strategy
        strategy = StrategyFactory.create_strategy(sample_config, 'native')
        
        # Test error handling
        result = await strategy.scrape_product('https://test-retailer.com/error/404')
        
        # Verify error handling
        assert result.success is False
        assert result.error is not None
        assert '404' in result.error
        
        # Check that stats are updated
        stats = strategy.get_stats()
        assert stats['failed_requests'] > 0
        
        # Clean up
        await strategy.close()
    
    @pytest.mark.asyncio
    async def test_concurrent_scraping_workflow(self, sample_config, mock_server):
        """Test concurrent scraping workflow end-to-end"""
        # Create strategy
        strategy = StrategyFactory.create_strategy(sample_config, 'native')
        
        # Test concurrent product scraping
        tasks = []
        for i in range(5):
            task = asyncio.create_task(
                strategy.scrape_product(f'https://test-retailer.com/product/{i}')
            )
            tasks.append(task)
        
        results = await asyncio.gather(*tasks)
        
        # Verify all requests succeeded
        assert len(results) == 5
        assert all(result.success for result in results)
        
        # Verify all results have expected data
        for result in results:
            assert result.data['name'] == 'High-Quality Test Product'
            assert result.data['price'] == 1299.99
            assert result.data['brand'] == 'TestBrand'
        
        # Check performance stats
        stats = strategy.get_stats()
        assert stats['successful_requests'] == 5
        assert stats['failed_requests'] == 0
        assert stats['average_response_time'] > 0
        
        # Clean up
        await strategy.close()
    
    @pytest.mark.asyncio
    async def test_rate_limiting_workflow(self, sample_config, mock_server):
        """Test rate limiting workflow end-to-end"""
        # Configure aggressive rate limiting
        sample_config['rate_limit_delay'] = 0.5
        sample_config['max_concurrent'] = 1
        
        # Create strategy
        strategy = StrategyFactory.create_strategy(sample_config, 'native')
        
        # Test rate limiting with multiple requests
        start_time = asyncio.get_event_loop().time()
        
        tasks = []
        for i in range(3):
            task = asyncio.create_task(
                strategy.scrape_product(f'https://test-retailer.com/product/{i}')
            )
            tasks.append(task)
        
        results = await asyncio.gather(*tasks)
        end_time = asyncio.get_event_loop().time()
        
        # Should have taken at least the rate limit delay
        assert end_time - start_time >= 1.0  # 3 requests * 0.5s delay (minus first)
        
        # All requests should succeed
        assert len(results) == 3
        assert all(result.success for result in results)
        
        # Clean up
        await strategy.close()
    
    @pytest.mark.asyncio
    async def test_retry_mechanism_workflow(self, sample_config, mock_server):
        """Test retry mechanism workflow end-to-end"""
        # Configure retry behavior
        sample_config['retry_attempts'] = 3
        
        # Create strategy
        strategy = StrategyFactory.create_strategy(sample_config, 'native')
        
        # Mock intermittent failures
        failure_count = 0
        
        async def intermittent_failure(route):
            nonlocal failure_count
            failure_count += 1
            
            if failure_count <= 2:
                # First two requests fail
                await route.fulfill(status=500, body="Server Error")
            else:
                # Third request succeeds
                await route.fulfill(
                    status=200,
                    content_type='text/html',
                    body="""
                    <html>
                        <body>
                            <h1 class="product-title">Retry Success Product</h1>
                            <div class="price">฿999.99</div>
                        </body>
                    </html>
                    """
                )
        
        await mock_server.route('**/retry/*', intermittent_failure)
        
        # Test retry mechanism
        result = await strategy.scrape_product('https://test-retailer.com/retry/123')
        
        # Should eventually succeed
        assert result.success is True
        assert result.data['name'] == 'Retry Success Product'
        assert result.data['price'] == 999.99
        
        # Clean up
        await strategy.close()
    
    @pytest.mark.asyncio
    async def test_session_management_workflow(self, sample_config, mock_server):
        """Test session management workflow end-to-end"""
        # Create strategy
        strategy = StrategyFactory.create_strategy(sample_config, 'native')
        
        # Test session reuse across multiple requests
        results = []
        for i in range(5):
            result = await strategy.scrape_product(f'https://test-retailer.com/product/{i}')
            results.append(result)
        
        # All requests should succeed
        assert len(results) == 5
        assert all(result.success for result in results)
        
        # Test session cleanup
        await strategy.close()
        
        # Should be able to create new strategy after cleanup
        new_strategy = StrategyFactory.create_strategy(sample_config, 'native')
        result = await new_strategy.scrape_product('https://test-retailer.com/product/test')
        assert result.success is True
        
        await new_strategy.close()
    
    @pytest.mark.asyncio
    async def test_data_extraction_accuracy(self, sample_config, mock_server):
        """Test data extraction accuracy end-to-end"""
        # Create strategy
        strategy = StrategyFactory.create_strategy(sample_config, 'native')
        
        # Test with complex HTML structure
        await mock_server.route('**/complex/*', lambda route: route.fulfill(
            status=200,
            content_type='text/html',
            body="""
            <html>
                <head><title>Complex Product</title></head>
                <body>
                    <div class="product-container">
                        <h1 class="product-title">Complex Test Product</h1>
                        <div class="price-container">
                            <span class="price">฿2,499.99</span>
                            <span class="original-price">฿3,000.00</span>
                        </div>
                        <div class="brand-info">
                            <span class="brand-name">PremiumBrand</span>
                        </div>
                        <div class="product-details">
                            <div class="sku">COMPLEX-SKU-789</div>
                            <div class="description">
                                This is a complex test product with multiple features
                                and comprehensive specifications.
                            </div>
                        </div>
                        <div class="availability">
                            <span class="stock-status">In Stock</span>
                        </div>
                        <div class="rating-section">
                            <div class="rating-score">4.8 out of 5 stars</div>
                            <div class="review-count">456 customer reviews</div>
                        </div>
                        <div class="images">
                            <img class="product-image" src="/images/complex1.jpg" alt="Product Image 1">
                            <img class="product-image" src="/images/complex2.jpg" alt="Product Image 2">
                        </div>
                    </div>
                </body>
            </html>
            """
        ))
        
        # Test complex data extraction
        result = await strategy.scrape_product('https://test-retailer.com/complex/123')
        
        # Verify accurate extraction
        assert result.success is True
        assert result.data['name'] == 'Complex Test Product'
        assert result.data['price'] == 2499.99
        assert result.data['brand'] == 'PremiumBrand'
        assert result.data['sku'] == 'COMPLEX-SKU-789'
        assert 'complex test product' in result.data['description'].lower()
        assert result.data['availability'] == 'in_stock'
        assert result.data['rating'] == 4.8
        assert result.data['reviews_count'] == 456
        assert len(result.data['images']) == 2
        
        # Clean up
        await strategy.close()
    
    @pytest.mark.asyncio
    async def test_performance_monitoring_workflow(self, sample_config, mock_server):
        """Test performance monitoring workflow end-to-end"""
        # Create strategy
        strategy = StrategyFactory.create_strategy(sample_config, 'native')
        
        # Test performance tracking
        start_time = asyncio.get_event_loop().time()
        
        # Make multiple requests
        results = []
        for i in range(10):
            result = await strategy.scrape_product(f'https://test-retailer.com/product/{i}')
            results.append(result)
        
        end_time = asyncio.get_event_loop().time()
        total_time = end_time - start_time
        
        # Verify performance metrics
        assert len(results) == 10
        assert all(result.success for result in results)
        
        # Check performance stats
        stats = strategy.get_stats()
        assert stats['total_requests'] == 10
        assert stats['successful_requests'] == 10
        assert stats['failed_requests'] == 0
        assert stats['average_response_time'] > 0
        assert stats['average_response_time'] < total_time  # Should be faster than serial
        
        # Check individual result metadata
        for result in results:
            assert 'response_time' in result.metadata
            assert 'quality_score' in result.metadata
            assert result.metadata['response_time'] >= 0
            assert result.metadata['quality_score'] >= 0.5
        
        # Clean up
        await strategy.close()
    
    @pytest.mark.asyncio
    async def test_real_world_scenario_workflow(self, sample_config, mock_server):
        """Test real-world scenario workflow end-to-end"""
        # Create strategy
        strategy = StrategyFactory.create_strategy(sample_config, 'native')
        
        # Simulate real-world mixed operations
        operations = [
            ('product', 'https://test-retailer.com/product/1'),
            ('category', 'https://test-retailer.com/category/electronics'),
            ('search', 'power tools'),
            ('product', 'https://test-retailer.com/product/2'),
            ('product', 'https://test-retailer.com/error/404'),  # Error case
            ('category', 'https://test-retailer.com/category/electronics'),
            ('product', 'https://test-retailer.com/product/3'),
        ]
        
        results = []
        for operation_type, url_or_query in operations:
            try:
                if operation_type == 'product':
                    result = await strategy.scrape_product(url_or_query)
                elif operation_type == 'category':
                    result = await strategy.scrape_category(url_or_query)
                elif operation_type == 'search':
                    result = await strategy.scrape_search(url_or_query)
                
                results.append((operation_type, result))
            except Exception as e:
                results.append((operation_type, {'error': str(e)}))
        
        # Verify mixed results
        assert len(results) == 7
        
        # Check individual results
        product_results = [r for op, r in results if op == 'product']
        category_results = [r for op, r in results if op == 'category']
        search_results = [r for op, r in results if op == 'search']
        
        # Most product results should succeed (except error case)
        successful_products = [r for r in product_results if r.success]
        assert len(successful_products) >= 3
        
        # Category results should succeed
        successful_categories = [r for r in category_results if r.success]
        assert len(successful_categories) == 2
        
        # Search results should succeed
        successful_searches = [r for r in search_results if r.success]
        assert len(successful_searches) == 1
        
        # Check final stats
        stats = strategy.get_stats()
        assert stats['total_requests'] == 7
        assert stats['successful_requests'] >= 6  # All except error case
        assert stats['failed_requests'] >= 1  # Error case
        
        # Clean up
        await strategy.close()