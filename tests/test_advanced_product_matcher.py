"""
Test suite for advanced product matcher
"""
import pytest
import asyncio
from datetime import datetime
from unittest.mock import Mock, AsyncMock, patch, MagicMock
import numpy as np

from src.services.advanced_product_matcher import AdvancedProductMatcher
from src.models.matching_models import (
    MatchingAlgorithmConfig,
    MatchConfidenceLevel,
    ProductMatchGroup,
    MatchFeature,
    ConfidenceBreakdown,
    PriceVolatilityLevel
)
from src.services.supabase_service import SupabaseService


@pytest.fixture
def mock_supabase():
    """Create mock Supabase service"""
    mock = Mock(spec=SupabaseService)
    mock.client = Mock()
    return mock


@pytest.fixture
def matcher(mock_supabase):
    """Create matcher instance with mock dependencies"""
    config = MatchingAlgorithmConfig(
        min_name_similarity=0.6,
        min_brand_similarity=0.7,
        use_ml_matching=False,  # Disable ML for unit tests
        price_variance_threshold=0.5,
        require_same_category=True
    )
    return AdvancedProductMatcher(mock_supabase, config)


@pytest.fixture
def sample_products():
    """Sample products for testing"""
    return [
        {
            'id': '1',
            'retailer_code': 'HP',
            'retailer_name': 'HomePro',
            'name': 'Samsung 55" 4K Smart TV UN55TU8000',
            'brand': 'Samsung',
            'category': 'Electronics',
            'current_price': 25000.0,
            'url': 'https://homepro.com/tv1',
            'in_stock': True,
            'description': '55 inch 4K UHD Smart TV with HDR'
        },
        {
            'id': '2',
            'retailer_code': 'TWD',
            'retailer_name': 'Thai Watsadu',
            'name': 'Samsung Smart TV 55 inch 4K UN55TU8000',
            'brand': 'Samsung',
            'category': 'Electronics',
            'current_price': 24000.0,
            'url': 'https://thaiwatsadu.com/tv1',
            'in_stock': True,
            'description': 'Samsung 55" 4K Smart LED TV'
        },
        {
            'id': '3',
            'retailer_code': 'HP',
            'retailer_name': 'HomePro',
            'name': 'LG 50" 4K Smart TV',
            'brand': 'LG',
            'category': 'Electronics',
            'current_price': 22000.0,
            'url': 'https://homepro.com/tv2',
            'in_stock': True
        }
    ]


class TestAdvancedProductMatcher:
    """Test AdvancedProductMatcher class"""
    
    @pytest.mark.asyncio
    async def test_match_products_basic(self, matcher, sample_products):
        """Test basic product matching"""
        # Run matching
        results = await matcher.match_products(sample_products[:2])
        
        # Should find one match group (Samsung TVs from different retailers)
        assert len(results) == 1
        assert len(results[0].matched_products) == 2
        assert results[0].canonical_product.brand.lower() == "samsung"
        assert results[0].confidence.overall >= 0.5
    
    @pytest.mark.asyncio
    async def test_no_matches_same_retailer(self, matcher, sample_products):
        """Test that products from same retailer don't match"""
        # Two HP products
        hp_products = [p for p in sample_products if p['retailer_code'] == 'HP']
        results = await matcher.match_products(hp_products)
        
        # Should find no matches
        assert len(results) == 0
    
    @pytest.mark.asyncio
    async def test_brand_mismatch(self, matcher, sample_products):
        """Test that different brands don't match"""
        # Samsung vs LG
        different_brands = [sample_products[0], sample_products[2]]
        different_brands[2]['retailer_code'] = 'TWD'  # Make different retailers
        
        results = await matcher.match_products(different_brands)
        
        # Should find no matches due to brand mismatch
        assert len(results) == 0
    
    @pytest.mark.asyncio
    async def test_price_variance_threshold(self, matcher):
        """Test price variance threshold filtering"""
        products = [
            {
                'id': '1',
                'retailer_code': 'HP',
                'name': 'Product A',
                'brand': 'Brand',
                'category': 'Category',
                'current_price': 1000.0
            },
            {
                'id': '2',
                'retailer_code': 'TWD',
                'name': 'Product A',
                'brand': 'Brand',
                'category': 'Category',
                'current_price': 2000.0  # 100% more expensive
            }
        ]
        
        # With 50% threshold, should not match
        results = await matcher.match_products(products)
        assert len(results) == 0
        
        # Increase threshold
        matcher.config.price_variance_threshold = 1.5
        results = await matcher.match_products(products)
        assert len(results) == 1
    
    def test_normalize_brand(self, matcher):
        """Test brand normalization"""
        assert matcher._normalize_brand("Samsung") == "samsung"
        assert matcher._normalize_brand("Samsung Electronics") == "samsung"
        assert matcher._normalize_brand("LG Electronics") == "lg"
        assert matcher._normalize_brand("") == ""
        assert matcher._normalize_brand(None) == ""
    
    def test_normalize_product_name(self, matcher):
        """Test product name normalization"""
        name = "Samsung 55\" 4K Smart TV (2023 Model) - Special Edition!"
        normalized = matcher._normalize_product_name(name)
        
        assert "samsung" in normalized
        assert "55" in normalized
        assert "4k" in normalized
        assert "smart tv" in normalized
        assert "(" not in normalized  # Special chars removed
        assert "!" not in normalized
    
    def test_extract_specifications(self, matcher):
        """Test specification extraction"""
        text = "Screen Size: 55 inch, Resolution: 4K UHD, Smart TV = Yes, Weight 15.5 kg"
        specs = matcher._extract_specifications(text)
        
        assert "screen size" in specs
        assert specs["screen size"] == "55 inch"
        assert "resolution" in specs
        assert specs["resolution"] == "4K UHD"
        assert "smart tv" in specs
        assert specs["smart tv"] == "Yes"
        
        # Test None handling
        assert matcher._extract_specifications(None) == {}
        assert matcher._extract_specifications("") == {}
    
    def test_calculate_price_consistency(self, matcher):
        """Test price consistency calculation"""
        # Very consistent prices
        score = matcher._calculate_price_consistency([1000, 1020, 1010])
        assert score >= 0.9
        
        # Moderately consistent
        score = matcher._calculate_price_consistency([1000, 1100, 1050])
        assert 0.7 <= score <= 0.9
        
        # Inconsistent prices
        score = matcher._calculate_price_consistency([1000, 2000, 1500])
        assert score < 0.5
        
        # Edge cases
        assert matcher._calculate_price_consistency([]) == 1.0
        assert matcher._calculate_price_consistency([1000]) == 1.0
        assert matcher._calculate_price_consistency([0, 0]) == 0.0
    
    @pytest.mark.asyncio
    async def test_determine_canonical_product(self, matcher, sample_products):
        """Test canonical product determination"""
        canonical = await matcher._determine_canonical_product(sample_products[:2])
        
        assert canonical.brand.lower() == "samsung"
        assert canonical.category == "Electronics"
        assert "4k" in [f.lower() for f in canonical.key_features]
        assert canonical.product_type == "television"
    
    @pytest.mark.asyncio
    async def test_calculate_confidence(self, matcher, sample_products):
        """Test confidence calculation"""
        from src.models.matching_models import CanonicalProduct
        
        canonical = CanonicalProduct(
            normalized_name="samsung 55 4k smart tv",
            brand="samsung",
            category="Electronics",
            product_type="television"
        )
        
        confidence, features = await matcher._calculate_confidence(
            sample_products[:2], 
            canonical
        )
        
        assert 0 <= confidence.overall <= 1
        assert 0 <= confidence.name_match <= 1
        assert 0 <= confidence.brand_match <= 1
        assert 0 <= confidence.spec_match <= 1
        assert 0 <= confidence.price_consistency <= 1
        assert confidence.user_validation == 0.0
        
        assert len(features) >= 4  # At least 4 feature types
        assert all(isinstance(f, MatchFeature) for f in features)
    
    @pytest.mark.asyncio
    async def test_analyze_prices(self, matcher):
        """Test price analysis"""
        from src.models.matching_models import MatchedProduct
        
        products = [
            MatchedProduct(
                product_id="1",
                retailer_code="HP",
                retailer_name="HomePro",
                product_name="Product A",
                current_price=1200.0,
                url="https://example.com/1",
                last_updated=datetime.now()
            ),
            MatchedProduct(
                product_id="2",
                retailer_code="TWD",
                retailer_name="Thai Watsadu",
                product_name="Product A",
                current_price=1000.0,
                url="https://example.com/2",
                last_updated=datetime.now()
            )
        ]
        
        analysis = await matcher._analyze_prices(products)
        
        assert analysis.current_best_price == 1000.0
        assert analysis.current_best_retailer == "TWD"
        assert analysis.savings_opportunity is not None
        assert analysis.savings_opportunity.amount == 200.0
        assert analysis.savings_opportunity.percentage == pytest.approx(16.67, rel=0.01)
        assert analysis.volatility == PriceVolatilityLevel.LOW
    
    @pytest.mark.asyncio
    async def test_extract_key_features(self, matcher):
        """Test key feature extraction"""
        names = [
            "Samsung 55\" 4K Smart TV with WiFi",
            "TV Samsung 55 inch 4K HDR Bluetooth",
            "55in Samsung Television 4K OLED USB-C"
        ]
        
        features = await matcher._extract_key_features(names)
        
        assert "55" in features or "55 inch" in features
        assert "4K" in features
        assert any("WiFi" in f or "Bluetooth" in f for f in features)
    
    def test_determine_product_type(self, matcher):
        """Test product type determination"""
        assert matcher._determine_product_type("Samsung 55 TV", "Electronics") == "television"
        assert matcher._determine_product_type("LG Refrigerator 500L", "") == "refrigerator"
        assert matcher._determine_product_type("Panasonic Air Conditioner", "") == "air_conditioner"
        assert matcher._determine_product_type("Samsung Washing Machine", "") == "washing_machine"
        assert matcher._determine_product_type("Unknown Product", "appliances") == "appliances"
        assert matcher._determine_product_type("Unknown Product", "") == "unknown"
    
    @pytest.mark.asyncio
    async def test_ml_matching_disabled(self, matcher):
        """Test matching with ML disabled"""
        matcher.config.use_ml_matching = False
        
        products = [
            {
                'id': '1',
                'retailer_code': 'HP',
                'name': 'Samsung TV Model ABC',
                'brand': 'Samsung',
                'category': 'TV',
                'current_price': 1000.0
            },
            {
                'id': '2',
                'retailer_code': 'TWD',
                'name': 'Samsung Television ABC',
                'brand': 'Samsung',
                'category': 'TV',
                'current_price': 1050.0
            }
        ]
        
        results = await matcher.match_products(products)
        
        assert len(results) == 1
        assert results[0].confidence.name_match > 0  # Should use fuzzy matching
    
    @pytest.mark.asyncio
    async def test_match_products_with_ml(self, mock_supabase):
        """Test matching with ML enabled (mocked)"""
        config = MatchingAlgorithmConfig(use_ml_matching=True)
        matcher = AdvancedProductMatcher(mock_supabase, config)
        
        # Mock ML model
        mock_model = MagicMock()
        mock_model.encode = MagicMock(return_value=np.array([[0.1, 0.2], [0.1, 0.21]]))
        
        with patch.object(matcher, 'ml_model', mock_model):
            products = [
                {
                    'id': '1',
                    'retailer_code': 'HP',
                    'name': 'Product A',
                    'brand': 'Brand',
                    'category': 'Cat',
                    'current_price': 1000.0
                },
                {
                    'id': '2',
                    'retailer_code': 'TWD',
                    'name': 'Product A Similar',
                    'brand': 'Brand',
                    'category': 'Cat',
                    'current_price': 1000.0
                }
            ]
            
            # Mock cosine similarity
            with patch('app.services.advanced_product_matcher.cosine_similarity') as mock_cosine:
                mock_cosine.return_value = [[0.95]]  # High similarity
                
                results = await matcher.match_products(products)
                
                assert len(results) == 1
                assert mock_model.encode.called
    
    @pytest.mark.asyncio
    async def test_empty_products_list(self, matcher):
        """Test with empty product list"""
        results = await matcher.match_products([])
        assert results == []
    
    @pytest.mark.asyncio
    async def test_single_product(self, matcher):
        """Test with single product"""
        products = [{
            'id': '1',
            'retailer_code': 'HP',
            'name': 'Product',
            'brand': 'Brand',
            'category': 'Category',
            'current_price': 1000.0
        }]
        
        results = await matcher.match_products(products)
        assert len(results) == 0  # No matches possible with single product
    
    @pytest.mark.asyncio
    async def test_category_mismatch_with_requirement(self, matcher):
        """Test category requirement enforcement"""
        matcher.config.require_same_category = True
        
        products = [
            {
                'id': '1',
                'retailer_code': 'HP',
                'name': 'Samsung TV',
                'brand': 'Samsung',
                'category': 'Television',
                'current_price': 1000.0
            },
            {
                'id': '2',
                'retailer_code': 'TWD',
                'name': 'Samsung TV',
                'brand': 'Samsung',
                'category': 'Electronics',  # Different category
                'current_price': 1000.0
            }
        ]
        
        results = await matcher.match_products(products)
        assert len(results) == 0
        
        # Disable category requirement
        matcher.config.require_same_category = False
        results = await matcher.match_products(products)
        assert len(results) == 1