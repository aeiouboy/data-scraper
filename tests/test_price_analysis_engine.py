"""
Test suite for price analysis engine
"""
import pytest
import asyncio
from datetime import datetime, timedelta
from unittest.mock import Mock, AsyncMock, patch, MagicMock
import pandas as pd
import numpy as np

from src.services.price_analysis_engine import PriceAnalysisEngine
from src.models.matching_models import (
    PriceVolatilityLevel,
    PriceAnalysis,
    PriceTrend,
    PriceAnomaly,
    SavingsOpportunity
)
from src.services.supabase_service import SupabaseService


@pytest.fixture
def mock_supabase():
    """Create mock Supabase service"""
    mock = Mock(spec=SupabaseService)
    mock.client = Mock()
    return mock


@pytest.fixture
def price_engine(mock_supabase):
    """Create price analysis engine with mock dependencies"""
    return PriceAnalysisEngine(mock_supabase)


@pytest.fixture
def sample_price_history():
    """Generate sample price history data"""
    base_date = datetime.now() - timedelta(days=30)
    history = []
    
    # Generate 30 days of price data with some variation
    for i in range(30):
        date = base_date + timedelta(days=i)
        # Add some price variation
        base_price = 10000
        variation = np.sin(i / 5) * 500 + np.random.normal(0, 100)
        price = base_price + variation
        
        history.append({
            'price': max(price, 8000),  # Ensure positive price
            'recorded_at': date.isoformat(),
            'discount_percentage': 10 if i % 7 == 0 else 0  # Weekly sales
        })
    
    return history


@pytest.fixture
def sample_price_history_with_anomaly():
    """Generate price history with anomalies"""
    base_date = datetime.now() - timedelta(days=20)
    history = []
    
    for i in range(20):
        date = base_date + timedelta(days=i)
        base_price = 10000
        
        # Add spike on day 10
        if i == 10:
            price = 15000  # 50% spike
        elif i == 15:
            price = 7000   # 30% drop
        else:
            price = base_price + np.random.normal(0, 200)
        
        history.append({
            'price': price,
            'recorded_at': date.isoformat(),
            'discount_percentage': 0
        })
    
    return history


class TestPriceAnalysisEngine:
    """Test PriceAnalysisEngine class"""
    
    @pytest.mark.asyncio
    async def test_analyze_price_history_basic(self, price_engine, mock_supabase, sample_price_history):
        """Test basic price history analysis"""
        # Mock price history retrieval
        mock_supabase.client.table.return_value.select.return_value.eq.return_value.gte.return_value.order.return_value.execute.return_value.data = sample_price_history
        
        with patch.object(price_engine, '_get_price_history', return_value=sample_price_history):
            result = await price_engine.analyze_price_history('product-1', 30)
        
        assert 'statistics' in result
        assert 'volatility' in result
        assert 'trends' in result
        assert 'anomalies' in result
        
        # Check statistics
        stats = result['statistics']
        assert 'current' in stats
        assert 'mean' in stats
        assert 'median' in stats
        assert 'std' in stats
        assert 'min' in stats
        assert 'max' in stats
        assert stats['min'] <= stats['mean'] <= stats['max']
    
    @pytest.mark.asyncio
    async def test_analyze_price_history_empty(self, price_engine):
        """Test analysis with no price history"""
        with patch.object(price_engine, '_get_price_history', return_value=[]):
            result = await price_engine.analyze_price_history('product-1', 30)
        
        assert result == price_engine._empty_analysis()
        assert result['volatility']['level'] == PriceVolatilityLevel.STABLE
        assert result['trends'] == []
        assert result['anomalies'] == []
    
    def test_calculate_volatility(self, price_engine):
        """Test volatility calculation"""
        # Stable prices
        stable_prices = pd.Series([1000, 1010, 990, 1005, 995])
        volatility = price_engine._calculate_volatility(stable_prices)
        
        assert volatility['level'] == PriceVolatilityLevel.STABLE
        assert volatility['coefficient_of_variation'] < 0.05
        
        # High volatility prices
        volatile_prices = pd.Series([1000, 1500, 800, 1600, 900])
        volatility = price_engine._calculate_volatility(volatile_prices)
        
        assert volatility['level'] in [PriceVolatilityLevel.HIGH, PriceVolatilityLevel.EXTREME]
        assert volatility['coefficient_of_variation'] > 0.2
    
    def test_analyze_trends(self, price_engine):
        """Test trend analysis"""
        # Create upward trend
        dates = pd.date_range(start='2024-01-01', periods=10, freq='D')
        prices = [1000 + i * 100 for i in range(10)]  # Increasing prices
        df = pd.DataFrame({'price': prices}, index=dates)
        
        trends = price_engine._analyze_trends(df)
        
        # Should have daily trend
        daily_trend = next((t for t in trends if t.period == 'daily'), None)
        assert daily_trend is not None
        assert daily_trend.direction == 'up'
        assert daily_trend.change_percentage > 0
        
        # Create downward trend
        prices_down = [2000 - i * 100 for i in range(10)]
        df_down = pd.DataFrame({'price': prices_down}, index=dates)
        
        trends_down = price_engine._analyze_trends(df_down)
        daily_trend_down = next((t for t in trends_down if t.period == 'daily'), None)
        assert daily_trend_down.direction == 'down'
        assert daily_trend_down.change_percentage < 0
    
    def test_detect_anomalies(self, price_engine):
        """Test anomaly detection"""
        dates = pd.date_range(start='2024-01-01', periods=20, freq='D')
        prices = [10000] * 20
        # Add anomalies
        prices[10] = 15000  # Spike
        prices[15] = 7000   # Drop
        
        df = pd.DataFrame({'price': prices}, index=dates)
        
        anomalies = price_engine._detect_anomalies(df)
        
        assert len(anomalies) >= 2
        
        # Check spike detection
        spike = next((a for a in anomalies if a.anomaly_type == 'spike'), None)
        assert spike is not None
        assert spike.actual_price == 15000
        assert spike.severity in ['medium', 'high']
        
        # Check drop detection
        drop = next((a for a in anomalies if a.anomaly_type == 'drop'), None)
        assert drop is not None
        assert drop.actual_price == 7000
    
    def test_classify_volatility(self, price_engine):
        """Test volatility classification"""
        assert price_engine._classify_volatility(0.03) == PriceVolatilityLevel.STABLE
        assert price_engine._classify_volatility(0.07) == PriceVolatilityLevel.LOW
        assert price_engine._classify_volatility(0.15) == PriceVolatilityLevel.MODERATE
        assert price_engine._classify_volatility(0.30) == PriceVolatilityLevel.HIGH
        assert price_engine._classify_volatility(0.50) == PriceVolatilityLevel.EXTREME
    
    @pytest.mark.asyncio
    async def test_analyze_match_group_prices(self, price_engine, mock_supabase):
        """Test match group price analysis"""
        # Mock product mappings
        mock_supabase.client.table.return_value.select.return_value.eq.return_value.execute.return_value.data = [
            {'product_id': '1', 'retailer_code': 'HP'},
            {'product_id': '2', 'retailer_code': 'TWD'}
        ]
        
        # Mock product prices
        with patch.object(mock_supabase.client, 'table') as mock_table:
            # First call for mappings
            mock_table.return_value.select.return_value.eq.return_value.execute.return_value.data = [
                {'product_id': '1', 'retailer_code': 'HP'},
                {'product_id': '2', 'retailer_code': 'TWD'}
            ]
            
            # Second call for products
            mock_table.return_value.select.return_value.in_.return_value.execute.return_value.data = [
                {
                    'id': '1',
                    'retailer_code': 'HP',
                    'current_price': 12000.0,
                    'name': 'Product from HP'
                },
                {
                    'id': '2',
                    'retailer_code': 'TWD',
                    'current_price': 10000.0,
                    'name': 'Product from TWD'
                }
            ]
            
            result = await price_engine.analyze_match_group_prices('match-group-1')
        
        assert result.current_best_price == 10000.0
        assert result.current_best_retailer == 'TWD'
        assert result.savings_opportunity is not None
        assert result.savings_opportunity.amount == 2000.0
        assert result.savings_opportunity.percentage == pytest.approx(16.67, rel=0.01)
        assert result.volatility == PriceVolatilityLevel.LOW
    
    @pytest.mark.asyncio
    async def test_analyze_match_group_prices_no_data(self, price_engine, mock_supabase):
        """Test match group analysis with no data"""
        mock_supabase.client.table.return_value.select.return_value.eq.return_value.execute.return_value.data = []
        
        result = await price_engine.analyze_match_group_prices('match-group-1')
        
        assert result.current_best_price == 0
        assert result.current_best_retailer == "Unknown"
        assert result.savings_opportunity is None
        assert result.volatility == PriceVolatilityLevel.STABLE
    
    @pytest.mark.asyncio
    async def test_analyze_market_volatility(self, price_engine, mock_supabase):
        """Test market volatility analysis"""
        # Mock products
        mock_supabase.client.table.return_value.select.return_value.limit.return_value.execute.return_value.data = [
            {
                'id': '1',
                'category': 'Electronics',
                'brand': 'Samsung',
                'retailer_code': 'HP'
            },
            {
                'id': '2',
                'category': 'Electronics',
                'brand': 'LG',
                'retailer_code': 'TWD'
            }
        ]
        
        # Mock price history for each product
        price_history = [
            {'price': 10000, 'recorded_at': datetime.now().isoformat()},
            {'price': 10500, 'recorded_at': (datetime.now() - timedelta(days=1)).isoformat()},
            {'price': 9800, 'recorded_at': (datetime.now() - timedelta(days=2)).isoformat()}
        ]
        
        with patch.object(price_engine, '_get_price_history', return_value=price_history):
            result = await price_engine.analyze_market_volatility(category='Electronics', days=30)
        
        assert 'by_category' in result
        assert 'by_retailer' in result
        assert 'by_brand' in result
        assert 'market_summary' in result
        
        # Check category analysis
        assert 'Electronics' in result['by_category']
        cat_data = result['by_category']['Electronics']
        assert 'avg_volatility' in cat_data
        assert 'volatility_level' in cat_data
        assert 'product_count' in cat_data
    
    def test_detect_seasonality_weekly(self, price_engine):
        """Test weekly seasonality detection"""
        # Create data with weekly pattern
        dates = pd.date_range(start='2024-01-01', periods=28, freq='D')
        prices = []
        
        for i in range(28):
            day_of_week = i % 7
            # Higher prices on weekends (days 5, 6)
            if day_of_week in [5, 6]:
                price = 11000 + np.random.normal(0, 50)
            else:
                price = 10000 + np.random.normal(0, 50)
            prices.append(price)
        
        df = pd.DataFrame({'price': prices}, index=dates)
        
        with patch('statsmodels.tsa.seasonal.seasonal_decompose') as mock_decompose:
            # Mock decomposition result
            mock_result = MagicMock()
            mock_result.seasonal = pd.Series([100 if i % 7 in [5, 6] else -100 for i in range(28)])
            mock_decompose.return_value = mock_result
            
            seasonality = price_engine._detect_seasonality(df)
        
        assert seasonality is not None
        assert seasonality['has_seasonality'] == True
        assert seasonality['pattern'] == 'weekly'
    
    def test_detect_seasonality_insufficient_data(self, price_engine):
        """Test seasonality detection with insufficient data"""
        dates = pd.date_range(start='2024-01-01', periods=10, freq='D')
        prices = [10000] * 10
        df = pd.DataFrame({'price': prices}, index=dates)
        
        seasonality = price_engine._detect_seasonality(df)
        assert seasonality is None
    
    @pytest.mark.asyncio
    async def test_forecast_prices(self, price_engine):
        """Test price forecasting"""
        # Create historical data
        dates = pd.date_range(start='2024-01-01', periods=30, freq='D')
        # Upward trend with some noise
        prices = [10000 + i * 50 + np.random.normal(0, 100) for i in range(30)]
        df = pd.DataFrame({'price': prices}, index=dates)
        
        with patch('statsmodels.tsa.holtwinters.ExponentialSmoothing') as mock_model_class:
            # Mock the model
            mock_model = MagicMock()
            mock_fitted = MagicMock()
            mock_fitted.forecast.return_value = pd.Series([10000, 10100, 10200, 10300, 10400, 10500, 10600])
            mock_fitted.fittedvalues = pd.Series(prices)
            mock_model.fit.return_value = mock_fitted
            mock_model_class.return_value = mock_model
            
            forecast = price_engine._forecast_prices(df, days_ahead=7)
        
        assert forecast is not None
        assert 'forecast_values' in forecast
        assert 'lower_bound' in forecast
        assert 'upper_bound' in forecast
        assert 'forecast_dates' in forecast
        assert len(forecast['forecast_values']) == 7
        assert forecast['confidence_level'] == 0.95
        assert forecast['method'] == 'holt_winters'
    
    def test_forecast_prices_insufficient_data(self, price_engine):
        """Test forecasting with insufficient data"""
        dates = pd.date_range(start='2024-01-01', periods=5, freq='D')
        prices = [10000] * 5
        df = pd.DataFrame({'price': prices}, index=dates)
        
        forecast = price_engine._forecast_prices(df)
        assert forecast is None
    
    @pytest.mark.asyncio
    async def test_get_price_history(self, price_engine, mock_supabase):
        """Test price history retrieval"""
        expected_data = [
            {'price': 10000, 'recorded_at': '2024-01-01', 'discount_percentage': 0},
            {'price': 10500, 'recorded_at': '2024-01-02', 'discount_percentage': 10}
        ]
        
        mock_supabase.client.table.return_value.select.return_value.eq.return_value.gte.return_value.order.return_value.execute.return_value.data = expected_data
        
        history = await price_engine._get_price_history('product-1', 30)
        
        assert history == expected_data
        mock_supabase.client.table.assert_called_with('price_history')
    
    @pytest.mark.asyncio
    async def test_error_handling(self, price_engine, mock_supabase):
        """Test error handling in various methods"""
        # Test analyze_price_history error
        with patch.object(price_engine, '_get_price_history', side_effect=Exception("Database error")):
            result = await price_engine.analyze_price_history('product-1', 30)
            assert result == price_engine._empty_analysis()
        
        # Test analyze_match_group_prices error
        mock_supabase.client.table.side_effect = Exception("Database error")
        result = await price_engine.analyze_match_group_prices('match-group-1')
        assert result == price_engine._empty_price_analysis()
        
        # Test analyze_market_volatility error
        result = await price_engine.analyze_market_volatility()
        assert 'error' in result