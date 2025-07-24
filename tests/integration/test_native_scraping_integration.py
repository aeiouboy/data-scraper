"""
Integration tests for native scraping system
"""
import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from scrapers.strategy_factory import StrategyFactory
from scrapers.strategies.native_strategy import NativeStrategy
from scrapers.strategies.hybrid_strategy import HybridStrategy
from config.retailers import RETAILER_CONFIGS, RetailerType
from config.retailer_selectors import update_retailer_config_with_selectors


@pytest.mark.integration
@pytest.mark.native
class TestNativeScrapingIntegration:
    """Integration tests for native scraping system"""
    
    @pytest.fixture
    def sample_config(self):
        """Sample retailer configuration"""
        return {
            'name': 'Test Retailer',
            'code': 'TEST',
            'base_url': 'https://test-retailer.com',
            'rate_limit_delay': 0.1,
            'max_concurrent': 2,
            'timeout': 5,
            'retry_attempts': 2,
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
    
    @pytest.mark.asyncio
    async def test_strategy_creation_and_basic_operations(self, sample_config):
        """Test creating strategy and basic operations"""
        # Create native strategy
        strategy = StrategyFactory.create_strategy(sample_config, 'native')
        
        assert isinstance(strategy, NativeStrategy)
        assert strategy.strategy_name == 'native'
        assert strategy.retailer_code == 'TEST'
        
        # Test strategy info
        info = strategy.get_strategy_info()
        assert info['name'] == 'native'
        assert info['retailer_code'] == 'TEST'
        
        # Test initial stats
        stats = strategy.get_stats()
        assert stats['total_requests'] == 0
        assert stats['successful_requests'] == 0
        assert stats['failed_requests'] == 0
        
        # Clean up
        await strategy.close()
    
    @pytest.mark.asyncio
    async def test_product_scraping_workflow(self, sample_config):
        """Test complete product scraping workflow"""
        strategy = StrategyFactory.create_strategy(sample_config, 'native')
        
        # Mock successful HTTP response
        mock_response = Mock()
        mock_response.status = 200
        mock_response.text = AsyncMock(return_value="""
        <html>
            <body>
                <h1 class="product-title">Test Product</h1>
                <div class="price">฿1,299.99</div>
                <div class="brand-name">TestBrand</div>
                <div class="sku">SKU-123</div>
                <div class="description">Test product description</div>
                <div class="stock-status">In Stock</div>
                <div class="rating-score">4.5</div>
                <div class="review-count">123 reviews</div>
                <img class="product-image" src="/image1.jpg" alt="Product">
            </body>
        </html>
        """)
        mock_response.headers = {'content-type': 'text/html'}
        
        # Mock aiohttp session
        mock_session = Mock()
        mock_session.get.return_value.__aenter__ = AsyncMock(return_value=mock_response)
        mock_session.get.return_value.__aexit__ = AsyncMock(return_value=None)
        
        with patch.object(strategy.engine.session_manager, 'get_session', return_value=mock_session):
            # Test product scraping
            result = await strategy.scrape_product('https://test-retailer.com/product/123')
            
            assert result.success is True
            assert result.data['name'] == 'Test Product'
            assert result.data['price'] == 1299.99
            assert result.data['brand'] == 'TestBrand'
            assert result.data['sku'] == 'SKU-123'
            assert result.data['description'] == 'Test product description'
            assert result.data['availability'] == 'in_stock'
            assert result.data['rating'] == 4.5
            assert result.data['reviews_count'] == 123
            assert len(result.data['images']) > 0
        
        # Check updated stats
        stats = strategy.get_stats()
        assert stats['total_requests'] > 0
        assert stats['successful_requests'] > 0
        
        await strategy.close()
    
    @pytest.mark.asyncio
    async def test_category_scraping_workflow(self, sample_config):
        """Test complete category scraping workflow"""
        strategy = StrategyFactory.create_strategy(sample_config, 'native')
        
        # Mock successful HTTP response
        mock_response = Mock()
        mock_response.status = 200
        mock_response.text = AsyncMock(return_value="""
        <html>
            <body>
                <h1 class="category-title">Electronics</h1>
                <div class="products">
                    <div class="product-item">
                        <a href="/product/1">Product 1</a>
                    </div>
                    <div class="product-item">
                        <a href="/product/2">Product 2</a>
                    </div>
                </div>
                <div class="pagination">
                    <a href="/category?page=1">1</a>
                    <a href="/category?page=2">2</a>
                </div>
            </body>
        </html>
        """)
        mock_response.headers = {'content-type': 'text/html'}
        
        # Mock aiohttp session
        mock_session = Mock()
        mock_session.get.return_value.__aenter__ = AsyncMock(return_value=mock_response)
        mock_session.get.return_value.__aexit__ = AsyncMock(return_value=None)
        
        with patch.object(strategy.engine.session_manager, 'get_session', return_value=mock_session):
            # Test category scraping
            result = await strategy.scrape_category('https://test-retailer.com/category/electronics')
            
            assert result.success is True
            assert result.data['category_name'] == 'Electronics'
            assert len(result.data['product_links']) == 2
            assert 'https://test-retailer.com/product/1' in result.data['product_links']
            assert 'https://test-retailer.com/product/2' in result.data['product_links']
        
        await strategy.close()
    
    @pytest.mark.asyncio
    async def test_search_scraping_workflow(self, sample_config):
        """Test complete search scraping workflow"""
        strategy = StrategyFactory.create_strategy(sample_config, 'native')
        
        # Mock successful HTTP response
        mock_response = Mock()
        mock_response.status = 200
        mock_response.text = AsyncMock(return_value="""
        <html>
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
        """)
        mock_response.headers = {'content-type': 'text/html'}
        
        # Mock aiohttp session
        mock_session = Mock()
        mock_session.get.return_value.__aenter__ = AsyncMock(return_value=mock_response)
        mock_session.get.return_value.__aexit__ = AsyncMock(return_value=None)
        
        with patch.object(strategy.engine.session_manager, 'get_session', return_value=mock_session):
            # Test search scraping
            result = await strategy.scrape_search('power tools')
            
            assert result.success is True
            assert len(result.data['product_links']) == 2
            assert 'https://test-retailer.com/product/search-1' in result.data['product_links']
            assert 'https://test-retailer.com/product/search-2' in result.data['product_links']
        
        await strategy.close()
    
    @pytest.mark.asyncio
    async def test_error_handling_and_recovery(self, sample_config):
        """Test error handling and recovery mechanisms"""
        strategy = StrategyFactory.create_strategy(sample_config, 'native')
        
        # Mock failed HTTP response
        mock_response = Mock()
        mock_response.status = 404
        mock_response.text = AsyncMock(return_value="Not Found")
        
        # Mock aiohttp session
        mock_session = Mock()
        mock_session.get.return_value.__aenter__ = AsyncMock(return_value=mock_response)
        mock_session.get.return_value.__aexit__ = AsyncMock(return_value=None)
        
        with patch.object(strategy.engine.session_manager, 'get_session', return_value=mock_session):
            # Test product scraping failure
            result = await strategy.scrape_product('https://test-retailer.com/product/nonexistent')
            
            assert result.success is False
            assert result.error is not None
            assert '404' in result.error
        
        # Check stats reflect the failure
        stats = strategy.get_stats()
        assert stats['failed_requests'] > 0
        
        await strategy.close()
    
    @pytest.mark.asyncio
    async def test_rate_limiting_integration(self, sample_config):
        """Test rate limiting integration with strategy"""
        # Configure for aggressive rate limiting
        sample_config['rate_limit_delay'] = 0.1
        sample_config['max_concurrent'] = 1
        
        strategy = StrategyFactory.create_strategy(sample_config, 'native')
        
        # Mock successful HTTP response
        mock_response = Mock()
        mock_response.status = 200
        mock_response.text = AsyncMock(return_value="<html><body>Test</body></html>")
        mock_response.headers = {'content-type': 'text/html'}
        
        # Mock aiohttp session
        mock_session = Mock()
        mock_session.get.return_value.__aenter__ = AsyncMock(return_value=mock_response)
        mock_session.get.return_value.__aexit__ = AsyncMock(return_value=None)
        
        with patch.object(strategy.engine.session_manager, 'get_session', return_value=mock_session):
            # Test multiple concurrent requests
            start_time = asyncio.get_event_loop().time()
            
            tasks = []
            for i in range(3):
                task = asyncio.create_task(
                    strategy.scrape_product(f'https://test-retailer.com/product/{i}')
                )
                tasks.append(task)
            
            results = await asyncio.gather(*tasks)
            end_time = asyncio.get_event_loop().time()
            
            # Should have taken some time due to rate limiting
            assert end_time - start_time >= 0.1
            
            # All requests should complete
            assert len(results) == 3
        
        await strategy.close()
    
    @pytest.mark.asyncio
    async def test_hybrid_strategy_integration(self, sample_config):
        """Test hybrid strategy integration"""
        # Configure for hybrid strategy
        sample_config['scraping_method'] = 'hybrid'
        sample_config['primary_strategy'] = 'native'
        sample_config['fallback_strategy'] = 'firecrawl'
        sample_config['success_rate_threshold'] = 0.8
        sample_config['fallback_after_failures'] = 2
        
        strategy = StrategyFactory.create_strategy(sample_config, 'hybrid')
        
        assert isinstance(strategy, HybridStrategy)
        assert strategy.strategy_name == 'hybrid'
        assert strategy.primary_strategy_name == 'native'
        assert strategy.fallback_strategy_name == 'firecrawl'
        
        # Test primary strategy success
        mock_result = Mock()
        mock_result.success = True
        mock_result.data = {'name': 'Test Product', 'price': 1299.99}
        mock_result.metadata = {'response_time': 0.5}
        
        with patch.object(strategy.primary_strategy, 'scrape_product', return_value=mock_result):
            result = await strategy.scrape_product('https://test-retailer.com/product/123')
            
            assert result.success is True
            assert result.data['name'] == 'Test Product'
            assert result.metadata['strategy_used'] == 'native'
        
        # Test fallback behavior
        mock_primary_fail = Mock()
        mock_primary_fail.success = False
        mock_primary_fail.error = 'Primary failed'
        
        mock_fallback_success = Mock()
        mock_fallback_success.success = True
        mock_fallback_success.data = {'name': 'Test Product', 'price': 1299.99}
        mock_fallback_success.metadata = {'response_time': 1.0}
        
        with patch.object(strategy.primary_strategy, 'scrape_product', return_value=mock_primary_fail):
            with patch.object(strategy.fallback_strategy, 'scrape_product', return_value=mock_fallback_success):
                result = await strategy.scrape_product('https://test-retailer.com/product/123')
                
                assert result.success is True
                assert result.data['name'] == 'Test Product'
                assert result.metadata['strategy_used'] == 'firecrawl'
        
        await strategy.close()
    
    @pytest.mark.asyncio
    async def test_real_retailer_config_integration(self):
        """Test integration with real retailer configurations"""
        # Get HomePro configuration
        hp_config = RETAILER_CONFIGS[RetailerType.HOMEPRO]
        
        # Convert to dict and add selectors
        config_dict = {
            'name': hp_config.name,
            'code': hp_config.code,
            'base_url': hp_config.base_url,
            'rate_limit_delay': hp_config.rate_limit_delay,
            'max_concurrent': hp_config.max_concurrent,
            'timeout': 30,
            'retry_attempts': 3,
            'scraping_method': hp_config.scraping_method.value,
            'product_url_patterns': hp_config.product_url_patterns,
            'selectors': {}
        }
        
        # Add selectors
        config_dict = update_retailer_config_with_selectors(config_dict)
        
        # Create strategy
        strategy = StrategyFactory.create_strategy(config_dict, 'native')
        
        assert strategy.retailer_code == 'HP'
        assert strategy.retailer_name == 'HomePro'
        assert len(strategy.engine.selectors) > 0
        
        # Test URL validation
        valid_url = 'https://www.homepro.co.th/p/1234567890'
        invalid_url = 'https://www.homepro.co.th/category/tools'
        
        assert strategy.engine.validate_product_url(valid_url) is True
        assert strategy.engine.validate_product_url(invalid_url) is False
        
        await strategy.close()
    
    @pytest.mark.asyncio
    async def test_concurrent_strategy_usage(self, sample_config):
        """Test concurrent usage of multiple strategies"""
        # Create multiple strategies
        strategies = []
        for i in range(3):
            config = sample_config.copy()
            config['code'] = f'TEST{i}'
            config['name'] = f'Test Retailer {i}'
            strategy = StrategyFactory.create_strategy(config, 'native')
            strategies.append(strategy)
        
        # Mock successful responses
        mock_response = Mock()
        mock_response.status = 200
        mock_response.text = AsyncMock(return_value="<html><body>Test</body></html>")
        mock_response.headers = {'content-type': 'text/html'}
        
        mock_session = Mock()
        mock_session.get.return_value.__aenter__ = AsyncMock(return_value=mock_response)
        mock_session.get.return_value.__aexit__ = AsyncMock(return_value=None)
        
        # Test concurrent scraping
        tasks = []
        for i, strategy in enumerate(strategies):
            with patch.object(strategy.engine.session_manager, 'get_session', return_value=mock_session):
                task = asyncio.create_task(
                    strategy.scrape_product(f'https://test-retailer.com/product/{i}')
                )
                tasks.append(task)
        
        results = await asyncio.gather(*tasks)
        
        # All should succeed
        assert len(results) == 3
        assert all(result.success for result in results)
        
        # Clean up
        for strategy in strategies:
            await strategy.close()
    
    @pytest.mark.asyncio
    async def test_strategy_factory_recommendations(self, sample_config):
        """Test strategy factory recommendations"""
        # Get recommendations
        recommendations = StrategyFactory.get_strategy_recommendations(sample_config)
        
        assert isinstance(recommendations, list)
        assert len(recommendations) > 0
        
        # Check recommendation structure
        for rec in recommendations:
            assert 'strategy' in rec
            assert 'score' in rec
            assert 'reason' in rec
            assert rec['strategy'] in ['native', 'firecrawl', 'hybrid']
            assert 0 <= rec['score'] <= 1
        
        # Test creating strategies from recommendations
        for rec in recommendations[:2]:  # Test first 2 recommendations
            strategy = StrategyFactory.create_strategy(sample_config, rec['strategy'])
            assert strategy.strategy_name == rec['strategy']
            await strategy.close()
    
    @pytest.mark.asyncio
    async def test_performance_monitoring_integration(self, sample_config):
        """Test performance monitoring integration"""
        strategy = StrategyFactory.create_strategy(sample_config, 'native')
        
        # Mock responses with different performance characteristics
        responses = [
            (200, 0.1),  # Fast success
            (200, 0.5),  # Medium success
            (404, 0.2),  # Fast failure
            (500, 1.0),  # Slow failure
            (200, 0.3),  # Medium success
        ]
        
        mock_session = Mock()
        
        for status, delay in responses:
            mock_response = Mock()
            mock_response.status = status
            mock_response.text = AsyncMock(return_value="<html><body>Test</body></html>")
            mock_response.headers = {'content-type': 'text/html'}
            
            mock_session.get.return_value.__aenter__ = AsyncMock(return_value=mock_response)
            mock_session.get.return_value.__aexit__ = AsyncMock(return_value=None)
            
            with patch.object(strategy.engine.session_manager, 'get_session', return_value=mock_session):
                # Simulate delay
                await asyncio.sleep(delay / 10)  # Scale down for testing
                
                result = await strategy.scrape_product('https://test-retailer.com/product/test')
                
                # Check that metadata includes performance info
                assert 'response_time' in result.metadata
                assert result.metadata['response_time'] >= 0
        
        # Check performance stats
        stats = strategy.get_stats()
        assert stats['total_requests'] == 5
        assert stats['successful_requests'] == 3
        assert stats['failed_requests'] == 2
        assert stats['average_response_time'] >= 0
        
        await strategy.close()
    
    @pytest.mark.asyncio
    async def test_data_quality_integration(self, sample_config):
        """Test data quality validation integration"""
        strategy = StrategyFactory.create_strategy(sample_config, 'native')
        
        # Test high-quality data
        high_quality_html = """
        <html>
            <body>
                <h1 class="product-title">Complete Product Name</h1>
                <div class="price">฿1,299.99</div>
                <div class="brand-name">TestBrand</div>
                <div class="sku">SKU-123</div>
                <div class="description">Complete product description</div>
                <div class="stock-status">In Stock</div>
                <div class="rating-score">4.5</div>
                <div class="review-count">123 reviews</div>
                <img class="product-image" src="/image1.jpg" alt="Product">
            </body>
        </html>
        """
        
        mock_response = Mock()
        mock_response.status = 200
        mock_response.text = AsyncMock(return_value=high_quality_html)
        mock_response.headers = {'content-type': 'text/html'}
        
        mock_session = Mock()
        mock_session.get.return_value.__aenter__ = AsyncMock(return_value=mock_response)
        mock_session.get.return_value.__aexit__ = AsyncMock(return_value=None)
        
        with patch.object(strategy.engine.session_manager, 'get_session', return_value=mock_session):
            result = await strategy.scrape_product('https://test-retailer.com/product/123')
            
            assert result.success is True
            assert 'quality_score' in result.metadata
            assert result.metadata['quality_score'] >= 0.5  # Should be high quality
        
        await strategy.close()
    
    @pytest.mark.asyncio
    async def test_session_management_integration(self, sample_config):
        """Test session management integration"""
        strategy = StrategyFactory.create_strategy(sample_config, 'native')
        
        # Test session reuse
        mock_response = Mock()
        mock_response.status = 200
        mock_response.text = AsyncMock(return_value="<html><body>Test</body></html>")
        mock_response.headers = {'content-type': 'text/html'}
        
        mock_session = Mock()
        mock_session.get.return_value.__aenter__ = AsyncMock(return_value=mock_response)
        mock_session.get.return_value.__aexit__ = AsyncMock(return_value=None)
        
        with patch.object(strategy.engine.session_manager, 'get_session', return_value=mock_session) as mock_get_session:
            # Make multiple requests
            for i in range(3):
                await strategy.scrape_product(f'https://test-retailer.com/product/{i}')
            
            # Should have reused sessions
            assert mock_get_session.call_count == 3
        
        # Test session cleanup
        await strategy.close()
        
        # Session manager should be closed
        assert strategy.engine.session_manager is not None