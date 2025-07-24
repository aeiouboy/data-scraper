"""
Unit tests for scraping strategies
"""
import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from scrapers.strategies.scraping_strategy import ScrapeResult
from scrapers.strategies.native_strategy import NativeStrategy
from scrapers.strategies.firecrawl_strategy import FirecrawlStrategy
from scrapers.strategies.hybrid_strategy import HybridStrategy
from scrapers.strategy_factory import StrategyFactory


@pytest.mark.unit
@pytest.mark.native
class TestNativeStrategy:
    """Test cases for native strategy"""
    
    def test_initialization(self):
        """Test native strategy initialization"""
        config = {
            'name': 'Test Retailer',
            'code': 'TEST',
            'base_url': 'https://test.com',
            'rate_limit_delay': 1.0,
            'max_concurrent': 3,
            'timeout': 30,
            'selectors': {}
        }
        
        strategy = NativeStrategy(config)
        
        assert strategy.strategy_name == 'native'
        assert strategy.retailer_code == 'TEST'
        assert strategy.retailer_name == 'Test Retailer'
    
    @pytest.mark.asyncio
    async def test_scrape_product_success(self):
        """Test successful product scraping"""
        config = {
            'name': 'Test Retailer',
            'code': 'TEST',
            'base_url': 'https://test.com',
            'selectors': {
                'product_name': ['.title'],
                'price': ['.price']
            }
        }
        
        strategy = NativeStrategy(config)
        
        # Mock engine response
        mock_result = Mock()
        mock_result.success = True
        mock_result.data = {
            'name': 'Test Product',
            'price': 1299.99,
            'url': 'https://test.com/product/123'
        }
        mock_result.metadata = {'response_time': 0.5}
        
        with patch.object(strategy.engine, 'extract_product_data', return_value=mock_result):
            result = await strategy.scrape_product('https://test.com/product/123')
            
            assert result.success is True
            assert result.data['name'] == 'Test Product'
            assert result.data['price'] == 1299.99
    
    @pytest.mark.asyncio
    async def test_scrape_product_failure(self):
        """Test failed product scraping"""
        config = {
            'name': 'Test Retailer',
            'code': 'TEST',
            'base_url': 'https://test.com',
            'selectors': {}
        }
        
        strategy = NativeStrategy(config)
        
        # Mock engine failure
        mock_result = Mock()
        mock_result.success = False
        mock_result.error = 'Page not found'
        
        with patch.object(strategy.engine, 'extract_product_data', return_value=mock_result):
            result = await strategy.scrape_product('https://test.com/product/invalid')
            
            assert result.success is False
            assert result.error == 'Page not found'
    
    @pytest.mark.asyncio
    async def test_scrape_category_success(self):
        """Test successful category scraping"""
        config = {
            'name': 'Test Retailer',
            'code': 'TEST',
            'base_url': 'https://test.com',
            'selectors': {
                'product_links': ['.product-item a'],
                'category_name': ['.category-title']
            }
        }
        
        strategy = NativeStrategy(config)
        
        # Mock engine response
        mock_result = Mock()
        mock_result.success = True
        mock_result.data = {
            'category_name': 'Electronics',
            'product_links': ['https://test.com/product/1', 'https://test.com/product/2'],
            'pagination': {'total_pages': 3}
        }
        mock_result.metadata = {'response_time': 0.8}
        
        with patch.object(strategy.engine, 'extract_category_data', return_value=mock_result):
            result = await strategy.scrape_category('https://test.com/category/electronics')
            
            assert result.success is True
            assert result.data['category_name'] == 'Electronics'
            assert len(result.data['product_links']) == 2
    
    @pytest.mark.asyncio
    async def test_scrape_search_success(self):
        """Test successful search scraping"""
        config = {
            'name': 'Test Retailer',
            'code': 'TEST',
            'base_url': 'https://test.com',
            'selectors': {
                'product_links': ['.search-result a']
            }
        }
        
        strategy = NativeStrategy(config)
        
        # Mock engine response
        mock_result = Mock()
        mock_result.success = True
        mock_result.data = {
            'product_links': ['https://test.com/product/search-1'],
            'pagination': {'total_pages': 2}
        }
        mock_result.metadata = {'response_time': 0.6}
        
        with patch.object(strategy.engine, 'extract_search_data', return_value=mock_result):
            result = await strategy.scrape_search('power tools')
            
            assert result.success is True
            assert len(result.data['product_links']) == 1
    
    @pytest.mark.asyncio
    async def test_test_connection(self):
        """Test connection testing"""
        config = {
            'name': 'Test Retailer',
            'code': 'TEST',
            'base_url': 'https://test.com',
            'selectors': {}
        }
        
        strategy = NativeStrategy(config)
        
        # Mock successful connection
        mock_result = Mock()
        mock_result.success = True
        mock_result.status_code = 200
        
        with patch.object(strategy.engine, 'make_request', return_value=mock_result):
            is_connected = await strategy.test_connection()
            
            assert is_connected is True
    
    def test_get_stats(self):
        """Test getting strategy statistics"""
        config = {
            'name': 'Test Retailer',
            'code': 'TEST',
            'base_url': 'https://test.com',
            'selectors': {}
        }
        
        strategy = NativeStrategy(config)
        
        stats = strategy.get_stats()
        
        assert 'total_requests' in stats
        assert 'successful_requests' in stats
        assert 'failed_requests' in stats
        assert 'average_response_time' in stats
    
    def test_get_strategy_info(self):
        """Test getting strategy information"""
        config = {
            'name': 'Test Retailer',
            'code': 'TEST',
            'base_url': 'https://test.com',
            'selectors': {}
        }
        
        strategy = NativeStrategy(config)
        
        info = strategy.get_strategy_info()
        
        assert info['name'] == 'native'
        assert info['retailer_code'] == 'TEST'
        assert info['retailer_name'] == 'Test Retailer'
    
    @pytest.mark.asyncio
    async def test_close(self):
        """Test strategy cleanup"""
        config = {
            'name': 'Test Retailer',
            'code': 'TEST',
            'base_url': 'https://test.com',
            'selectors': {}
        }
        
        strategy = NativeStrategy(config)
        
        # Mock engine close
        with patch.object(strategy.engine, 'close', new_callable=AsyncMock) as mock_close:
            await strategy.close()
            mock_close.assert_called_once()


@pytest.mark.unit
@pytest.mark.native
class TestFirecrawlStrategy:
    """Test cases for firecrawl strategy"""
    
    def test_initialization(self):
        """Test firecrawl strategy initialization"""
        config = {
            'name': 'Test Retailer',
            'code': 'TEST',
            'base_url': 'https://test.com',
            'firecrawl_api_key': 'test-key',
            'selectors': {}
        }
        
        strategy = FirecrawlStrategy(config)
        
        assert strategy.strategy_name == 'firecrawl'
        assert strategy.retailer_code == 'TEST'
        assert strategy.retailer_name == 'Test Retailer'
    
    @pytest.mark.asyncio
    async def test_scrape_product_success(self):
        """Test successful product scraping with Firecrawl"""
        config = {
            'name': 'Test Retailer',
            'code': 'TEST',
            'base_url': 'https://test.com',
            'firecrawl_api_key': 'test-key',
            'selectors': {}
        }
        
        strategy = FirecrawlStrategy(config)
        
        # Mock Firecrawl response
        mock_response = {
            'metadata': {'title': 'Test Product'},
            'markdown': '# Test Product\n\n฿1,299.99\n\nTestBrand',
            'html': '<html><body>Test</body></html>'
        }
        
        with patch.object(strategy.firecrawl_client, 'scrape', return_value=mock_response):
            result = await strategy.scrape_product('https://test.com/product/123')
            
            assert result.success is True
            assert 'name' in result.data
    
    def test_get_strategy_info(self):
        """Test getting firecrawl strategy information"""
        config = {
            'name': 'Test Retailer',
            'code': 'TEST',
            'base_url': 'https://test.com',
            'firecrawl_api_key': 'test-key',
            'selectors': {}
        }
        
        strategy = FirecrawlStrategy(config)
        
        info = strategy.get_strategy_info()
        
        assert info['name'] == 'firecrawl'
        assert info['retailer_code'] == 'TEST'
        assert info['retailer_name'] == 'Test Retailer'


@pytest.mark.unit
@pytest.mark.native
class TestHybridStrategy:
    """Test cases for hybrid strategy"""
    
    def test_initialization(self):
        """Test hybrid strategy initialization"""
        config = {
            'name': 'Test Retailer',
            'code': 'TEST',
            'base_url': 'https://test.com',
            'primary_strategy': 'native',
            'fallback_strategy': 'firecrawl',
            'success_rate_threshold': 0.8,
            'response_time_threshold': 5.0,
            'fallback_after_failures': 3,
            'selectors': {}
        }
        
        strategy = HybridStrategy(config)
        
        assert strategy.strategy_name == 'hybrid'
        assert strategy.retailer_code == 'TEST'
        assert strategy.retailer_name == 'Test Retailer'
        assert strategy.primary_strategy_name == 'native'
        assert strategy.fallback_strategy_name == 'firecrawl'
    
    @pytest.mark.asyncio
    async def test_scrape_product_primary_success(self):
        """Test successful product scraping with primary strategy"""
        config = {
            'name': 'Test Retailer',
            'code': 'TEST',
            'base_url': 'https://test.com',
            'primary_strategy': 'native',
            'fallback_strategy': 'firecrawl',
            'selectors': {}
        }
        
        strategy = HybridStrategy(config)
        
        # Mock primary strategy success
        mock_result = Mock()
        mock_result.success = True
        mock_result.data = {'name': 'Test Product', 'price': 1299.99}
        mock_result.metadata = {'response_time': 0.5}
        
        with patch.object(strategy.primary_strategy, 'scrape_product', return_value=mock_result):
            result = await strategy.scrape_product('https://test.com/product/123')
            
            assert result.success is True
            assert result.data['name'] == 'Test Product'
            assert result.metadata['strategy_used'] == 'native'
    
    @pytest.mark.asyncio
    async def test_scrape_product_fallback_success(self):
        """Test successful product scraping with fallback strategy"""
        config = {
            'name': 'Test Retailer',
            'code': 'TEST',
            'base_url': 'https://test.com',
            'primary_strategy': 'native',
            'fallback_strategy': 'firecrawl',
            'selectors': {}
        }
        
        strategy = HybridStrategy(config)
        
        # Mock primary strategy failure
        mock_primary_result = Mock()
        mock_primary_result.success = False
        mock_primary_result.error = 'Primary failed'
        
        # Mock fallback strategy success
        mock_fallback_result = Mock()
        mock_fallback_result.success = True
        mock_fallback_result.data = {'name': 'Test Product', 'price': 1299.99}
        mock_fallback_result.metadata = {'response_time': 1.0}
        
        with patch.object(strategy.primary_strategy, 'scrape_product', return_value=mock_primary_result):
            with patch.object(strategy.fallback_strategy, 'scrape_product', return_value=mock_fallback_result):
                result = await strategy.scrape_product('https://test.com/product/123')
                
                assert result.success is True
                assert result.data['name'] == 'Test Product'
                assert result.metadata['strategy_used'] == 'firecrawl'
    
    @pytest.mark.asyncio
    async def test_scrape_product_both_fail(self):
        """Test product scraping when both strategies fail"""
        config = {
            'name': 'Test Retailer',
            'code': 'TEST',
            'base_url': 'https://test.com',
            'primary_strategy': 'native',
            'fallback_strategy': 'firecrawl',
            'selectors': {}
        }
        
        strategy = HybridStrategy(config)
        
        # Mock both strategies failing
        mock_primary_result = Mock()
        mock_primary_result.success = False
        mock_primary_result.error = 'Primary failed'
        
        mock_fallback_result = Mock()
        mock_fallback_result.success = False
        mock_fallback_result.error = 'Fallback failed'
        
        with patch.object(strategy.primary_strategy, 'scrape_product', return_value=mock_primary_result):
            with patch.object(strategy.fallback_strategy, 'scrape_product', return_value=mock_fallback_result):
                result = await strategy.scrape_product('https://test.com/product/123')
                
                assert result.success is False
                assert 'Primary failed' in result.error
                assert 'Fallback failed' in result.error
    
    def test_should_use_fallback_performance(self):
        """Test fallback decision based on performance"""
        config = {
            'name': 'Test Retailer',
            'code': 'TEST',
            'base_url': 'https://test.com',
            'primary_strategy': 'native',
            'fallback_strategy': 'firecrawl',
            'success_rate_threshold': 0.8,
            'response_time_threshold': 5.0,
            'selectors': {}
        }
        
        strategy = HybridStrategy(config)
        
        # Record poor performance
        for _ in range(10):
            strategy._record_request_result(False, 10.0)
        
        assert strategy._should_use_fallback() is True
    
    def test_should_use_fallback_consecutive_failures(self):
        """Test fallback decision based on consecutive failures"""
        config = {
            'name': 'Test Retailer',
            'code': 'TEST',
            'base_url': 'https://test.com',
            'primary_strategy': 'native',
            'fallback_strategy': 'firecrawl',
            'fallback_after_failures': 3,
            'selectors': {}
        }
        
        strategy = HybridStrategy(config)
        
        # Record consecutive failures
        for _ in range(3):
            strategy._record_request_result(False, 1.0)
        
        assert strategy._should_use_fallback() is True
    
    def test_get_hybrid_stats(self):
        """Test getting hybrid strategy statistics"""
        config = {
            'name': 'Test Retailer',
            'code': 'TEST',
            'base_url': 'https://test.com',
            'primary_strategy': 'native',
            'fallback_strategy': 'firecrawl',
            'selectors': {}
        }
        
        strategy = HybridStrategy(config)
        
        stats = strategy.get_hybrid_stats()
        
        assert 'primary_strategy_requests' in stats
        assert 'fallback_strategy_requests' in stats
        assert 'success_rate' in stats
        assert 'average_response_time' in stats
    
    def test_get_strategy_info(self):
        """Test getting hybrid strategy information"""
        config = {
            'name': 'Test Retailer',
            'code': 'TEST',
            'base_url': 'https://test.com',
            'primary_strategy': 'native',
            'fallback_strategy': 'firecrawl',
            'selectors': {}
        }
        
        strategy = HybridStrategy(config)
        
        info = strategy.get_strategy_info()
        
        assert info['name'] == 'hybrid'
        assert info['retailer_code'] == 'TEST'
        assert info['primary_strategy'] == 'native'
        assert info['fallback_strategy'] == 'firecrawl'


@pytest.mark.unit
@pytest.mark.native
class TestStrategyFactory:
    """Test cases for strategy factory"""
    
    def test_get_available_strategies(self):
        """Test getting available strategies"""
        strategies = StrategyFactory.get_available_strategies()
        
        assert 'native' in strategies
        assert 'firecrawl' in strategies
        assert 'hybrid' in strategies
        assert len(strategies) >= 3
    
    def test_validate_strategy_type_valid(self):
        """Test validating valid strategy types"""
        valid_strategies = ['native', 'firecrawl', 'hybrid']
        
        for strategy in valid_strategies:
            assert StrategyFactory.validate_strategy_type(strategy) is True
    
    def test_validate_strategy_type_invalid(self):
        """Test validating invalid strategy types"""
        invalid_strategies = ['selenium', 'requests', 'unknown', 'invalid']
        
        for strategy in invalid_strategies:
            assert StrategyFactory.validate_strategy_type(strategy) is False
    
    def test_create_native_strategy(self):
        """Test creating native strategy"""
        config = {
            'name': 'Test Retailer',
            'code': 'TEST',
            'base_url': 'https://test.com',
            'selectors': {}
        }
        
        strategy = StrategyFactory.create_native_strategy(config)
        
        assert isinstance(strategy, NativeStrategy)
        assert strategy.strategy_name == 'native'
    
    def test_create_firecrawl_strategy(self):
        """Test creating firecrawl strategy"""
        config = {
            'name': 'Test Retailer',
            'code': 'TEST',
            'base_url': 'https://test.com',
            'firecrawl_api_key': 'test-key',
            'selectors': {}
        }
        
        strategy = StrategyFactory.create_firecrawl_strategy(config)
        
        assert isinstance(strategy, FirecrawlStrategy)
        assert strategy.strategy_name == 'firecrawl'
    
    def test_create_hybrid_strategy(self):
        """Test creating hybrid strategy"""
        config = {
            'name': 'Test Retailer',
            'code': 'TEST',
            'base_url': 'https://test.com',
            'primary_strategy': 'native',
            'fallback_strategy': 'firecrawl',
            'selectors': {}
        }
        
        strategy = StrategyFactory.create_hybrid_strategy(config)
        
        assert isinstance(strategy, HybridStrategy)
        assert strategy.strategy_name == 'hybrid'
    
    def test_create_strategy_native(self):
        """Test creating strategy with native type"""
        config = {
            'name': 'Test Retailer',
            'code': 'TEST',
            'base_url': 'https://test.com',
            'selectors': {}
        }
        
        strategy = StrategyFactory.create_strategy(config, 'native')
        
        assert isinstance(strategy, NativeStrategy)
        assert strategy.strategy_name == 'native'
    
    def test_create_strategy_firecrawl(self):
        """Test creating strategy with firecrawl type"""
        config = {
            'name': 'Test Retailer',
            'code': 'TEST',
            'base_url': 'https://test.com',
            'firecrawl_api_key': 'test-key',
            'selectors': {}
        }
        
        strategy = StrategyFactory.create_strategy(config, 'firecrawl')
        
        assert isinstance(strategy, FirecrawlStrategy)
        assert strategy.strategy_name == 'firecrawl'
    
    def test_create_strategy_hybrid(self):
        """Test creating strategy with hybrid type"""
        config = {
            'name': 'Test Retailer',
            'code': 'TEST',
            'base_url': 'https://test.com',
            'primary_strategy': 'native',
            'fallback_strategy': 'firecrawl',
            'selectors': {}
        }
        
        strategy = StrategyFactory.create_strategy(config, 'hybrid')
        
        assert isinstance(strategy, HybridStrategy)
        assert strategy.strategy_name == 'hybrid'
    
    def test_create_strategy_invalid_type(self):
        """Test creating strategy with invalid type"""
        config = {
            'name': 'Test Retailer',
            'code': 'TEST',
            'base_url': 'https://test.com',
            'selectors': {}
        }
        
        with pytest.raises(ValueError, match="Unknown strategy type"):
            StrategyFactory.create_strategy(config, 'invalid')
    
    def test_create_strategy_from_config(self):
        """Test creating strategy from config with strategy type"""
        config = {
            'name': 'Test Retailer',
            'code': 'TEST',
            'base_url': 'https://test.com',
            'primary_strategy': 'native',
            'fallback_strategy': 'firecrawl',
            'scraping_method': 'hybrid',
            'selectors': {}
        }
        
        strategy = StrategyFactory.create_strategy_from_config(config)
        
        assert isinstance(strategy, HybridStrategy)
        assert strategy.strategy_name == 'hybrid'
    
    def test_create_strategy_from_config_default(self):
        """Test creating strategy from config with default type"""
        config = {
            'name': 'Test Retailer',
            'code': 'TEST',
            'base_url': 'https://test.com',
            'selectors': {}
        }
        
        strategy = StrategyFactory.create_strategy_from_config(config)
        
        assert isinstance(strategy, NativeStrategy)
        assert strategy.strategy_name == 'native'
    
    def test_get_strategy_recommendations(self):
        """Test getting strategy recommendations"""
        config = {
            'name': 'Test Retailer',
            'code': 'TEST',
            'base_url': 'https://test.com',
            'selectors': {}
        }
        
        recommendations = StrategyFactory.get_strategy_recommendations(config)
        
        assert isinstance(recommendations, list)
        assert len(recommendations) > 0
        assert all(rec['strategy'] in ['native', 'firecrawl', 'hybrid'] for rec in recommendations)
    
    def test_create_strategies_comparison(self):
        """Test creating multiple strategies for comparison"""
        config = {
            'name': 'Test Retailer',
            'code': 'TEST',
            'base_url': 'https://test.com',
            'firecrawl_api_key': 'test-key',
            'selectors': {}
        }
        
        strategies = StrategyFactory.create_strategies_for_comparison(config)
        
        assert len(strategies) >= 2
        assert any(s.strategy_name == 'native' for s in strategies)
        assert any(s.strategy_name == 'firecrawl' for s in strategies)