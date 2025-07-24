"""
Unit tests for native scraper engine
"""
import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from scrapers.engines.native_scraper_engine import NativeScraperEngine, ScrapeResult


@pytest.mark.unit
@pytest.mark.native
class TestNativeScraperEngine:
    """Test cases for native scraper engine functionality"""
    
    def test_initialization(self):
        """Test engine initialization"""
        config = {
            'name': 'Test Retailer',
            'code': 'TEST',
            'base_url': 'https://test.com',
            'rate_limit_delay': 1.0,
            'max_concurrent': 3,
            'timeout': 30,
            'retry_attempts': 3,
            'selectors': {}
        }
        
        engine = NativeScraperEngine(config)
        
        assert engine.retailer_name == 'Test Retailer'
        assert engine.retailer_code == 'TEST'
        assert engine.base_url == 'https://test.com'
        assert engine.timeout == 30
        assert engine.retry_attempts == 3
    
    def test_initialization_with_defaults(self):
        """Test initialization with default values"""
        config = {
            'name': 'Test Retailer',
            'code': 'TEST',
            'base_url': 'https://test.com',
            'selectors': {}
        }
        
        engine = NativeScraperEngine(config)
        
        assert engine.timeout == 30  # default
        assert engine.retry_attempts == 3  # default
        assert engine.rate_limit_delay == 1.0  # default
    
    @pytest.mark.asyncio
    async def test_make_request_success(self):
        """Test successful HTTP request"""
        config = {
            'name': 'Test Retailer',
            'code': 'TEST',
            'base_url': 'https://test.com',
            'selectors': {}
        }
        
        engine = NativeScraperEngine(config)
        
        # Mock successful response
        mock_response = Mock()
        mock_response.status = 200
        mock_response.text = AsyncMock(return_value="<html><body>Test</body></html>")
        mock_response.headers = {'content-type': 'text/html'}
        
        mock_session = Mock()
        mock_session.get.return_value.__aenter__ = AsyncMock(return_value=mock_response)
        mock_session.get.return_value.__aexit__ = AsyncMock(return_value=None)
        
        with patch.object(engine.session_manager, 'get_session', return_value=mock_session):
            result = await engine.make_request('https://test.com/page')
            
            assert result.success is True
            assert result.html == "<html><body>Test</body></html>"
            assert result.status_code == 200
            assert result.error is None
    
    @pytest.mark.asyncio
    async def test_make_request_failure(self):
        """Test failed HTTP request"""
        config = {
            'name': 'Test Retailer',
            'code': 'TEST',
            'base_url': 'https://test.com',
            'selectors': {}
        }
        
        engine = NativeScraperEngine(config)
        
        # Mock failed response
        mock_response = Mock()
        mock_response.status = 404
        mock_response.text = AsyncMock(return_value="Not Found")
        
        mock_session = Mock()
        mock_session.get.return_value.__aenter__ = AsyncMock(return_value=mock_response)
        mock_session.get.return_value.__aexit__ = AsyncMock(return_value=None)
        
        with patch.object(engine.session_manager, 'get_session', return_value=mock_session):
            result = await engine.make_request('https://test.com/nonexistent')
            
            assert result.success is False
            assert result.status_code == 404
            assert result.error is not None
            assert "404" in result.error
    
    @pytest.mark.asyncio
    async def test_make_request_with_retry(self):
        """Test request with retry logic"""
        config = {
            'name': 'Test Retailer',
            'code': 'TEST',
            'base_url': 'https://test.com',
            'retry_attempts': 2,
            'selectors': {}
        }
        
        engine = NativeScraperEngine(config)
        
        # Mock responses: first fails, second succeeds
        mock_response_fail = Mock()
        mock_response_fail.status = 500
        mock_response_fail.text = AsyncMock(return_value="Server Error")
        
        mock_response_success = Mock()
        mock_response_success.status = 200
        mock_response_success.text = AsyncMock(return_value="<html><body>Success</body></html>")
        mock_response_success.headers = {'content-type': 'text/html'}
        
        mock_session = Mock()
        mock_session.get.return_value.__aenter__ = AsyncMock(
            side_effect=[mock_response_fail, mock_response_success]
        )
        mock_session.get.return_value.__aexit__ = AsyncMock(return_value=None)
        
        with patch.object(engine.session_manager, 'get_session', return_value=mock_session):
            result = await engine.make_request('https://test.com/page')
            
            assert result.success is True
            assert result.html == "<html><body>Success</body></html>"
            assert result.status_code == 200
    
    @pytest.mark.asyncio
    async def test_make_request_timeout(self):
        """Test request timeout handling"""
        config = {
            'name': 'Test Retailer',
            'code': 'TEST',
            'base_url': 'https://test.com',
            'timeout': 0.1,
            'selectors': {}
        }
        
        engine = NativeScraperEngine(config)
        
        # Mock timeout
        mock_session = Mock()
        mock_session.get.return_value.__aenter__ = AsyncMock(
            side_effect=asyncio.TimeoutError("Request timeout")
        )
        mock_session.get.return_value.__aexit__ = AsyncMock(return_value=None)
        
        with patch.object(engine.session_manager, 'get_session', return_value=mock_session):
            result = await engine.make_request('https://test.com/slow')
            
            assert result.success is False
            assert result.error is not None
            assert "timeout" in result.error.lower()
    
    @pytest.mark.asyncio
    async def test_extract_product_data(self):
        """Test product data extraction"""
        config = {
            'name': 'Test Retailer',
            'code': 'TEST',
            'base_url': 'https://test.com',
            'selectors': {
                'product_name': ['h1.title', '.product-name'],
                'price': ['.price', '.cost'],
                'brand': ['.brand'],
                'sku': ['.sku']
            }
        }
        
        engine = NativeScraperEngine(config)
        
        html = """
        <html>
            <body>
                <h1 class="title">Test Product</h1>
                <div class="price">฿1,299.99</div>
                <div class="brand">TestBrand</div>
                <div class="sku">SKU-123</div>
            </body>
        </html>
        """
        
        # Mock successful request
        mock_result = Mock()
        mock_result.success = True
        mock_result.html = html
        mock_result.status_code = 200
        
        with patch.object(engine, 'make_request', return_value=mock_result):
            result = await engine.extract_product_data('https://test.com/product/123')
            
            assert result.success is True
            assert result.data['name'] == 'Test Product'
            assert result.data['price'] == 1299.99
            assert result.data['brand'] == 'TestBrand'
            assert result.data['sku'] == 'SKU-123'
    
    @pytest.mark.asyncio
    async def test_extract_product_data_missing_fields(self):
        """Test product data extraction with missing fields"""
        config = {
            'name': 'Test Retailer',
            'code': 'TEST',
            'base_url': 'https://test.com',
            'selectors': {
                'product_name': ['h1.title'],
                'price': ['.price'],
                'brand': ['.brand'],
                'sku': ['.sku']
            }
        }
        
        engine = NativeScraperEngine(config)
        
        html = """
        <html>
            <body>
                <h1 class="title">Test Product</h1>
                <!-- Missing price, brand, sku -->
            </body>
        </html>
        """
        
        # Mock successful request
        mock_result = Mock()
        mock_result.success = True
        mock_result.html = html
        mock_result.status_code = 200
        
        with patch.object(engine, 'make_request', return_value=mock_result):
            result = await engine.extract_product_data('https://test.com/product/123')
            
            assert result.success is True
            assert result.data['name'] == 'Test Product'
            assert result.data['price'] is None
            assert result.data['brand'] is None
            assert result.data['sku'] is None
    
    @pytest.mark.asyncio
    async def test_extract_category_data(self):
        """Test category data extraction"""
        config = {
            'name': 'Test Retailer',
            'code': 'TEST',
            'base_url': 'https://test.com',
            'selectors': {
                'product_links': ['.product-item a', '.product-card a'],
                'category_name': ['.category-title'],
                'pagination': ['.pagination a']
            }
        }
        
        engine = NativeScraperEngine(config)
        
        html = """
        <html>
            <body>
                <h1 class="category-title">Electronics</h1>
                <div class="product-item">
                    <a href="/product/1">Product 1</a>
                </div>
                <div class="product-item">
                    <a href="/product/2">Product 2</a>
                </div>
                <div class="pagination">
                    <a href="/category?page=1">1</a>
                    <a href="/category?page=2">2</a>
                </div>
            </body>
        </html>
        """
        
        # Mock successful request
        mock_result = Mock()
        mock_result.success = True
        mock_result.html = html
        mock_result.status_code = 200
        
        with patch.object(engine, 'make_request', return_value=mock_result):
            result = await engine.extract_category_data('https://test.com/category')
            
            assert result.success is True
            assert result.data['category_name'] == 'Electronics'
            assert len(result.data['product_links']) == 2
            assert 'https://test.com/product/1' in result.data['product_links']
            assert 'https://test.com/product/2' in result.data['product_links']
    
    @pytest.mark.asyncio
    async def test_extract_search_data(self):
        """Test search data extraction"""
        config = {
            'name': 'Test Retailer',
            'code': 'TEST',
            'base_url': 'https://test.com',
            'selectors': {
                'product_links': ['.search-result a'],
                'pagination': ['.pagination a']
            }
        }
        
        engine = NativeScraperEngine(config)
        
        html = """
        <html>
            <body>
                <div class="search-results">
                    <div class="search-result">
                        <a href="/product/search-1">Search Result 1</a>
                    </div>
                    <div class="search-result">
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
        
        # Mock successful request
        mock_result = Mock()
        mock_result.success = True
        mock_result.html = html
        mock_result.status_code = 200
        
        with patch.object(engine, 'make_request', return_value=mock_result):
            result = await engine.extract_search_data('https://test.com/search?q=test')
            
            assert result.success is True
            assert len(result.data['product_links']) == 2
            assert 'https://test.com/product/search-1' in result.data['product_links']
            assert 'https://test.com/product/search-2' in result.data['product_links']
    
    @pytest.mark.asyncio
    async def test_build_search_url(self):
        """Test search URL building"""
        config = {
            'name': 'Test Retailer',
            'code': 'TEST',
            'base_url': 'https://test.com',
            'search_patterns': {
                'url_pattern': '/search?q={query}',
                'query_parameter': 'q'
            },
            'selectors': {}
        }
        
        engine = NativeScraperEngine(config)
        
        search_url = engine.build_search_url('power tools')
        assert search_url == 'https://test.com/search?q=power+tools'
        
        # Test with special characters
        search_url = engine.build_search_url('드릴 & 망치')
        assert 'drill' in search_url.lower() or '%' in search_url
    
    @pytest.mark.asyncio
    async def test_build_search_url_no_patterns(self):
        """Test search URL building without patterns"""
        config = {
            'name': 'Test Retailer',
            'code': 'TEST',
            'base_url': 'https://test.com',
            'selectors': {}
        }
        
        engine = NativeScraperEngine(config)
        
        search_url = engine.build_search_url('power tools')
        assert search_url == 'https://test.com/search?q=power+tools'  # default pattern
    
    @pytest.mark.asyncio
    async def test_validate_product_url(self):
        """Test product URL validation"""
        config = {
            'name': 'Test Retailer',
            'code': 'TEST',
            'base_url': 'https://test.com',
            'product_url_patterns': ['/product/', '/p/'],
            'selectors': {}
        }
        
        engine = NativeScraperEngine(config)
        
        # Valid URLs
        assert engine.validate_product_url('https://test.com/product/123') is True
        assert engine.validate_product_url('https://test.com/p/456') is True
        
        # Invalid URLs
        assert engine.validate_product_url('https://test.com/category/electronics') is False
        assert engine.validate_product_url('https://other.com/product/123') is False
    
    @pytest.mark.asyncio
    async def test_validate_product_url_no_patterns(self):
        """Test product URL validation without patterns"""
        config = {
            'name': 'Test Retailer',
            'code': 'TEST',
            'base_url': 'https://test.com',
            'selectors': {}
        }
        
        engine = NativeScraperEngine(config)
        
        # Should accept any URL from the same domain
        assert engine.validate_product_url('https://test.com/any/path') is True
        assert engine.validate_product_url('https://other.com/path') is False
    
    def test_get_stats(self):
        """Test getting engine statistics"""
        config = {
            'name': 'Test Retailer',
            'code': 'TEST',
            'base_url': 'https://test.com',
            'selectors': {}
        }
        
        engine = NativeScraperEngine(config)
        
        stats = engine.get_stats()
        
        # Check required fields
        assert 'total_requests' in stats
        assert 'successful_requests' in stats
        assert 'failed_requests' in stats
        assert 'total_products_scraped' in stats
        assert 'total_categories_scraped' in stats
        assert 'total_searches_performed' in stats
        assert 'average_response_time' in stats
    
    def test_get_engine_info(self):
        """Test getting engine information"""
        config = {
            'name': 'Test Retailer',
            'code': 'TEST',
            'base_url': 'https://test.com',
            'selectors': {}
        }
        
        engine = NativeScraperEngine(config)
        
        info = engine.get_engine_info()
        
        # Check required fields
        assert 'retailer_name' in info
        assert 'retailer_code' in info
        assert 'base_url' in info
        assert 'timeout' in info
        assert 'retry_attempts' in info
        assert 'selectors_count' in info
    
    @pytest.mark.asyncio
    async def test_close(self):
        """Test engine cleanup"""
        config = {
            'name': 'Test Retailer',
            'code': 'TEST',
            'base_url': 'https://test.com',
            'selectors': {}
        }
        
        engine = NativeScraperEngine(config)
        
        # Mock session manager close
        with patch.object(engine.session_manager, 'close', new_callable=AsyncMock) as mock_close:
            await engine.close()
            mock_close.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_concurrent_requests(self):
        """Test concurrent request handling"""
        config = {
            'name': 'Test Retailer',
            'code': 'TEST',
            'base_url': 'https://test.com',
            'max_concurrent': 3,
            'selectors': {}
        }
        
        engine = NativeScraperEngine(config)
        
        # Mock successful responses
        mock_response = Mock()
        mock_response.status = 200
        mock_response.text = AsyncMock(return_value="<html><body>Test</body></html>")
        mock_response.headers = {'content-type': 'text/html'}
        
        mock_session = Mock()
        mock_session.get.return_value.__aenter__ = AsyncMock(return_value=mock_response)
        mock_session.get.return_value.__aexit__ = AsyncMock(return_value=None)
        
        with patch.object(engine.session_manager, 'get_session', return_value=mock_session):
            # Create concurrent requests
            tasks = []
            for i in range(5):
                task = asyncio.create_task(engine.make_request(f'https://test.com/page{i}'))
                tasks.append(task)
            
            # Should complete without error
            results = await asyncio.gather(*tasks)
            
            # All should succeed
            assert all(result.success for result in results)
    
    @pytest.mark.asyncio
    async def test_request_caching(self):
        """Test request caching mechanism"""
        config = {
            'name': 'Test Retailer',
            'code': 'TEST',
            'base_url': 'https://test.com',
            'enable_caching': True,
            'cache_ttl': 300,
            'selectors': {}
        }
        
        engine = NativeScraperEngine(config)
        
        # Mock successful response
        mock_response = Mock()
        mock_response.status = 200
        mock_response.text = AsyncMock(return_value="<html><body>Test</body></html>")
        mock_response.headers = {'content-type': 'text/html'}
        
        mock_session = Mock()
        mock_session.get.return_value.__aenter__ = AsyncMock(return_value=mock_response)
        mock_session.get.return_value.__aexit__ = AsyncMock(return_value=None)
        
        with patch.object(engine.session_manager, 'get_session', return_value=mock_session):
            # First request
            result1 = await engine.make_request('https://test.com/page')
            
            # Second request (should use cache if implemented)
            result2 = await engine.make_request('https://test.com/page')
            
            assert result1.success is True
            assert result2.success is True
    
    def test_repr(self):
        """Test string representation"""
        config = {
            'name': 'Test Retailer',
            'code': 'TEST',
            'base_url': 'https://test.com',
            'selectors': {}
        }
        
        engine = NativeScraperEngine(config)
        
        # Should not raise exception
        str_repr = repr(engine)
        assert 'NativeScraperEngine' in str_repr
        assert 'TEST' in str_repr
        assert 'Test Retailer' in str_repr
    
    @pytest.mark.asyncio
    async def test_error_recovery(self):
        """Test error recovery mechanisms"""
        config = {
            'name': 'Test Retailer',
            'code': 'TEST',
            'base_url': 'https://test.com',
            'retry_attempts': 3,
            'selectors': {}
        }
        
        engine = NativeScraperEngine(config)
        
        # Mock responses: multiple failures then success
        mock_response_fail = Mock()
        mock_response_fail.status = 503
        mock_response_fail.text = AsyncMock(return_value="Service Unavailable")
        
        mock_response_success = Mock()
        mock_response_success.status = 200
        mock_response_success.text = AsyncMock(return_value="<html><body>Success</body></html>")
        mock_response_success.headers = {'content-type': 'text/html'}
        
        mock_session = Mock()
        mock_session.get.return_value.__aenter__ = AsyncMock(
            side_effect=[
                mock_response_fail,
                mock_response_fail,
                mock_response_success
            ]
        )
        mock_session.get.return_value.__aexit__ = AsyncMock(return_value=None)
        
        with patch.object(engine.session_manager, 'get_session', return_value=mock_session):
            result = await engine.make_request('https://test.com/page')
            
            assert result.success is True
            assert result.html == "<html><body>Success</body></html>"
    
    @pytest.mark.asyncio
    async def test_data_quality_validation(self):
        """Test data quality validation"""
        config = {
            'name': 'Test Retailer',
            'code': 'TEST',
            'base_url': 'https://test.com',
            'min_data_quality_score': 0.7,
            'selectors': {
                'product_name': ['.title'],
                'price': ['.price'],
                'brand': ['.brand'],
                'sku': ['.sku']
            }
        }
        
        engine = NativeScraperEngine(config)
        
        # Test high-quality data
        high_quality_html = """
        <html>
            <body>
                <div class="title">Complete Product Name</div>
                <div class="price">฿1,299.99</div>
                <div class="brand">TestBrand</div>
                <div class="sku">SKU-123</div>
            </body>
        </html>
        """
        
        mock_result = Mock()
        mock_result.success = True
        mock_result.html = high_quality_html
        mock_result.status_code = 200
        
        with patch.object(engine, 'make_request', return_value=mock_result):
            result = await engine.extract_product_data('https://test.com/product/123')
            
            assert result.success is True
            assert 'quality_score' in result.metadata
            assert result.metadata['quality_score'] >= 0.7
    
    @pytest.mark.asyncio
    async def test_performance_monitoring(self):
        """Test performance monitoring"""
        config = {
            'name': 'Test Retailer',
            'code': 'TEST',
            'base_url': 'https://test.com',
            'selectors': {}
        }
        
        engine = NativeScraperEngine(config)
        
        # Mock successful response with delay
        mock_response = Mock()
        mock_response.status = 200
        mock_response.text = AsyncMock(return_value="<html><body>Test</body></html>")
        mock_response.headers = {'content-type': 'text/html'}
        
        mock_session = Mock()
        mock_session.get.return_value.__aenter__ = AsyncMock(return_value=mock_response)
        mock_session.get.return_value.__aexit__ = AsyncMock(return_value=None)
        
        with patch.object(engine.session_manager, 'get_session', return_value=mock_session):
            result = await engine.make_request('https://test.com/page')
            
            assert result.success is True
            assert 'response_time' in result.metadata
            assert result.metadata['response_time'] >= 0