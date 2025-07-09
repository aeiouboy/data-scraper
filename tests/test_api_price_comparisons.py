"""
Test suite for price comparison API endpoints
"""
import pytest
from fastapi.testclient import TestClient
from datetime import datetime
from unittest.mock import Mock, AsyncMock, patch
import json

from src.main import app
from src.models.matching_models import (
    ProductMatchGroup,
    CanonicalProduct,
    MatchedProduct,
    ConfidenceBreakdown,
    PriceAnalysis,
    MatchMetadata,
    PriceVolatilityLevel,
    SavingsOpportunity,
    MatchFeature,
    PriceTrend,
    MatchingResponse
)
from src.services.supabase_service import SupabaseService
from src.services.advanced_product_matcher import AdvancedProductMatcher
from src.services.price_analysis_engine import PriceAnalysisEngine


client = TestClient(app)


@pytest.fixture
def mock_supabase():
    """Mock Supabase service"""
    with patch('app.api.routers.price_comparisons_v2.SupabaseService') as mock:
        instance = Mock()
        mock.return_value = instance
        yield instance


@pytest.fixture
def mock_matcher():
    """Mock product matcher"""
    with patch('app.api.routers.price_comparisons_v2.AdvancedProductMatcher') as mock:
        instance = Mock()
        mock.return_value = instance
        yield instance


@pytest.fixture
def mock_price_engine():
    """Mock price analysis engine"""
    with patch('app.api.routers.price_comparisons_v2.PriceAnalysisEngine') as mock:
        instance = Mock()
        mock.return_value = instance
        yield instance


@pytest.fixture
def sample_match_group():
    """Create sample match group for testing"""
    canonical = CanonicalProduct(
        normalized_name="samsung 55 inch 4k smart tv",
        brand="Samsung",
        category="Electronics",
        product_type="television",
        key_features=["4K", "55 inch", "Smart TV"]
    )
    
    confidence = ConfidenceBreakdown(
        overall=0.85,
        name_match=0.9,
        brand_match=1.0,
        spec_match=0.8,
        price_consistency=0.75,
        user_validation=0.0
    )
    
    matched_products = [
        MatchedProduct(
            product_id="prod-1",
            retailer_code="HP",
            retailer_name="HomePro",
            product_name="Samsung 55\" 4K Smart TV UN55TU8000",
            current_price=25000.0,
            url="https://homepro.com/tv1",
            last_updated=datetime.now()
        ),
        MatchedProduct(
            product_id="prod-2",
            retailer_code="TWD",
            retailer_name="Thai Watsadu",
            product_name="Samsung Smart TV 55 inch 4K",
            current_price=23000.0,
            url="https://thaiwatsadu.com/tv1",
            last_updated=datetime.now()
        )
    ]
    
    savings = SavingsOpportunity(
        amount=2000.0,
        percentage=8.0,
        best_retailer="TWD",
        compared_to_retailers=["HP"],
        confidence=0.95
    )
    
    price_analysis = PriceAnalysis(
        current_best_price=23000.0,
        current_best_retailer="TWD",
        savings_opportunity=savings,
        volatility=PriceVolatilityLevel.LOW,
        volatility_score=0.08,
        last_updated=datetime.now()
    )
    
    metadata = MatchMetadata(
        algorithm_version="2.0",
        match_features=[
            MatchFeature(
                name="brand_match",
                value=1.0,
                weight=0.25,
                matched=True,
                similarity_score=1.0
            )
        ],
        processing_time_ms=150,
        created_at=datetime.now()
    )
    
    return ProductMatchGroup(
        id="mg_12345",
        canonical_product=canonical,
        matched_products=matched_products,
        confidence=confidence,
        match_metadata=metadata,
        price_analysis=price_analysis,
        created_at=datetime.now(),
        updated_at=datetime.now()
    )


class TestPriceComparisonAPI:
    """Test price comparison API endpoints"""
    
    def test_get_price_comparisons_basic(self, mock_supabase):
        """Test basic price comparisons endpoint"""
        # Mock database response
        mock_supabase.client.table.return_value.select.return_value.execute.return_value.data = [
            {
                'id': 'mg_1',
                'canonical_name': 'Samsung TV',
                'canonical_brand': 'Samsung',
                'category': 'Electronics',
                'confidence_score': 0.85,
                'retailer_count': 2,
                'min_price': 23000,
                'max_price': 25000,
                'savings_amount': 2000,
                'savings_percentage': 8.0,
                'best_retailer': 'TWD',
                'volatility_level': 'low',
                'created_at': datetime.now().isoformat()
            }
        ]
        mock_supabase.client.table.return_value.select.return_value.execute.return_value.count = 1
        
        response = client.get("/api/v1/price-comparisons")
        
        assert response.status_code == 200
        data = response.json()
        assert 'groups' in data
        assert 'total' in data
        assert len(data['groups']) == 1
        assert data['total'] == 1
    
    def test_get_price_comparisons_with_filters(self, mock_supabase):
        """Test price comparisons with filters"""
        mock_supabase.client.table.return_value.select.return_value.eq.return_value.gte.return_value.order.return_value.range.return_value.execute.return_value.data = []
        mock_supabase.client.table.return_value.select.return_value.eq.return_value.gte.return_value.order.return_value.range.return_value.execute.return_value.count = 0
        
        response = client.get("/api/v1/price-comparisons", params={
            'category': 'Electronics',
            'min_confidence': 0.8,
            'has_savings': True,
            'sort_by': 'savings_amount',
            'limit': 20,
            'offset': 0
        })
        
        assert response.status_code == 200
        data = response.json()
        assert data['groups'] == []
        assert data['total'] == 0
    
    def test_get_price_comparison_detail(self, mock_supabase):
        """Test get single price comparison detail"""
        # Mock match group
        mock_supabase.client.table.return_value.select.return_value.eq.return_value.single.return_value.execute.return_value.data = {
            'id': 'mg_123',
            'canonical_name': 'Samsung TV',
            'canonical_brand': 'Samsung',
            'category': 'Electronics',
            'key_features': ['4K', '55 inch'],
            'created_at': datetime.now().isoformat()
        }
        
        # Mock confidence
        mock_supabase.client.table.return_value.select.return_value.eq.return_value.single.return_value.execute.side_effect = [
            Mock(data={'id': 'mg_123'}),  # Match group
            Mock(data={'overall_score': 0.85}),  # Confidence
            Mock(data=[  # Products
                {'product_id': '1', 'retailer_code': 'HP'},
                {'product_id': '2', 'retailer_code': 'TWD'}
            ]),
            Mock(data=[  # Product details
                {
                    'id': '1',
                    'name': 'Samsung TV HP',
                    'current_price': 25000,
                    'retailer_code': 'HP',
                    'url': 'https://hp.com/tv'
                },
                {
                    'id': '2',
                    'name': 'Samsung TV TWD',
                    'current_price': 23000,
                    'retailer_code': 'TWD',
                    'url': 'https://twd.com/tv'
                }
            ])
        ]
        
        response = client.get("/api/v1/price-comparisons/mg_123")
        
        assert response.status_code == 200
        data = response.json()
        assert data['id'] == 'mg_123'
        assert 'canonical_product' in data
        assert 'matched_products' in data
        assert 'confidence' in data
        assert 'price_analysis' in data
    
    def test_get_price_comparison_not_found(self, mock_supabase):
        """Test get non-existent price comparison"""
        mock_supabase.client.table.return_value.select.return_value.eq.return_value.single.return_value.execute.return_value.data = None
        
        response = client.get("/api/v1/price-comparisons/mg_999")
        
        assert response.status_code == 404
        assert response.json()['detail'] == "Match group not found"
    
    @pytest.mark.asyncio
    async def test_run_matching(self, mock_supabase, mock_matcher, sample_match_group):
        """Test run matching endpoint"""
        # Mock matcher response
        mock_matcher.match_products = AsyncMock(return_value=[sample_match_group])
        
        # Mock product search
        mock_supabase.search_products = AsyncMock(return_value={
            'products': [
                {
                    'id': '1',
                    'name': 'Samsung TV',
                    'retailer_code': 'HP',
                    'current_price': 25000
                },
                {
                    'id': '2',
                    'name': 'Samsung TV',
                    'retailer_code': 'TWD',
                    'current_price': 23000
                }
            ]
        })
        
        response = client.post("/api/v1/price-comparisons/match", json={
            'category': 'Electronics',
            'min_confidence': 0.7
        })
        
        assert response.status_code == 200
        data = response.json()
        assert 'match_groups' in data
        assert data['total_groups'] >= 0
        assert data['total_products'] >= 0
        assert 'processing_time_ms' in data
    
    def test_get_price_trends(self, mock_price_engine):
        """Test get price trends endpoint"""
        mock_price_engine.analyze_price_history = AsyncMock(return_value={
            'statistics': {
                'current': 10000,
                'mean': 10500,
                'min': 9000,
                'max': 12000
            },
            'volatility': {
                'level': 'low',
                'score': 0.08
            },
            'trends': [
                {
                    'period': 'weekly',
                    'direction': 'up',
                    'change_percentage': 5.0,
                    'average_price': 10000,
                    'min_price': 9500,
                    'max_price': 10500,
                    'volatility_score': 0.05
                }
            ],
            'anomalies': [],
            'seasonality': None,
            'forecast': None
        })
        
        response = client.get("/api/v1/price-comparisons/products/prod-123/trends")
        
        assert response.status_code == 200
        data = response.json()
        assert 'statistics' in data
        assert 'volatility' in data
        assert 'trends' in data
        assert len(data['trends']) > 0
    
    def test_get_market_volatility(self, mock_price_engine):
        """Test market volatility analysis endpoint"""
        mock_price_engine.analyze_market_volatility = AsyncMock(return_value={
            'by_category': {
                'Electronics': {
                    'avg_volatility': 0.12,
                    'std_volatility': 0.05,
                    'product_count': 150,
                    'volatility_level': 'moderate'
                }
            },
            'by_retailer': {
                'HP': {
                    'avg_volatility': 0.10,
                    'product_count': 80,
                    'volatility_level': 'low'
                }
            },
            'market_summary': {
                'total_products_analyzed': 300,
                'avg_market_volatility': 0.11,
                'most_volatile_category': 'Electronics',
                'most_stable_category': 'Furniture'
            }
        })
        
        response = client.get("/api/v1/price-comparisons/volatility", params={
            'category': 'Electronics',
            'days': 30
        })
        
        assert response.status_code == 200
        data = response.json()
        assert 'by_category' in data
        assert 'by_retailer' in data
        assert 'market_summary' in data
    
    def test_update_match_confidence(self, mock_supabase):
        """Test update match confidence endpoint"""
        # Mock existing confidence
        mock_supabase.client.table.return_value.select.return_value.eq.return_value.single.return_value.execute.return_value.data = {
            'id': 'conf-123',
            'user_validation': 0.0
        }
        
        # Mock update
        mock_supabase.client.table.return_value.update.return_value.eq.return_value.execute.return_value.data = [{
            'id': 'conf-123',
            'user_validation': 0.9
        }]
        
        response = client.put("/api/v1/price-comparisons/mg_123/confidence", json={
            'user_validation': 0.9,
            'feedback': 'correct_match'
        })
        
        assert response.status_code == 200
        data = response.json()
        assert data['user_validation'] == 0.9
    
    def test_get_savings_opportunities(self, mock_supabase):
        """Test get savings opportunities endpoint"""
        mock_supabase.client.table.return_value.select.return_value.gt.return_value.order.return_value.limit.return_value.execute.return_value.data = [
            {
                'id': 'mg_1',
                'canonical_name': 'Samsung TV',
                'category': 'Electronics',
                'savings_amount': 5000,
                'savings_percentage': 20.0,
                'best_retailer': 'TWD',
                'min_price': 20000,
                'max_price': 25000,
                'confidence_score': 0.90
            }
        ]
        
        response = client.get("/api/v1/price-comparisons/savings", params={
            'min_savings': 1000,
            'category': 'Electronics',
            'limit': 10
        })
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) > 0
        assert data[0]['savings_amount'] >= 1000
    
    def test_error_handling(self, mock_supabase):
        """Test API error handling"""
        # Database error
        mock_supabase.client.table.side_effect = Exception("Database connection failed")
        
        response = client.get("/api/v1/price-comparisons")
        
        assert response.status_code == 500
        assert "error" in response.json()['detail'].lower()