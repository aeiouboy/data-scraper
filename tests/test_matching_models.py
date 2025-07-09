"""
Test suite for matching models
"""
import pytest
from datetime import datetime
from src.models.matching_models import (
    MatchConfidenceLevel,
    PriceVolatilityLevel,
    MatchFeature,
    ConfidenceBreakdown,
    NormalizedSpecifications,
    CanonicalProduct,
    VariantMapping,
    PricePoint,
    PriceTrend,
    PriceAnomaly,
    SavingsOpportunity,
    PriceAnalysis,
    MatchMetadata,
    MatchedProduct,
    ProductMatchGroup,
    MatchingAlgorithmConfig,
    MatchingRequest,
    MatchingResponse
)


class TestMatchConfidenceLevel:
    """Test MatchConfidenceLevel enum"""
    
    def test_confidence_levels(self):
        assert MatchConfidenceLevel.EXACT == "exact"
        assert MatchConfidenceLevel.HIGH == "high"
        assert MatchConfidenceLevel.MEDIUM == "medium"
        assert MatchConfidenceLevel.LOW == "low"
        assert MatchConfidenceLevel.NONE == "none"


class TestPriceVolatilityLevel:
    """Test PriceVolatilityLevel enum"""
    
    def test_volatility_levels(self):
        assert PriceVolatilityLevel.STABLE == "stable"
        assert PriceVolatilityLevel.LOW == "low"
        assert PriceVolatilityLevel.MODERATE == "moderate"
        assert PriceVolatilityLevel.HIGH == "high"
        assert PriceVolatilityLevel.EXTREME == "extreme"


class TestMatchFeature:
    """Test MatchFeature model"""
    
    def test_valid_match_feature(self):
        feature = MatchFeature(
            name="brand_match",
            value="Samsung",
            weight=0.25,
            matched=True,
            similarity_score=0.95
        )
        assert feature.name == "brand_match"
        assert feature.value == "Samsung"
        assert feature.weight == 0.25
        assert feature.matched is True
        assert feature.similarity_score == 0.95
    
    def test_weight_validation(self):
        with pytest.raises(ValueError):
            MatchFeature(
                name="test",
                value="test",
                weight=1.5,  # Invalid: > 1
                matched=True,
                similarity_score=0.5
            )
    
    def test_similarity_score_validation(self):
        with pytest.raises(ValueError):
            MatchFeature(
                name="test",
                value="test",
                weight=0.5,
                matched=True,
                similarity_score=1.5  # Invalid: > 1
            )


class TestConfidenceBreakdown:
    """Test ConfidenceBreakdown model"""
    
    def test_manual_overall_score(self):
        confidence = ConfidenceBreakdown(
            overall=0.85,
            name_match=0.9,
            brand_match=0.95,
            spec_match=0.8,
            price_consistency=0.7,
            user_validation=0.0
        )
        assert confidence.overall == 0.85
    
    def test_automatic_overall_calculation(self):
        confidence = ConfidenceBreakdown(
            name_match=0.9,
            brand_match=1.0,
            spec_match=0.8,
            price_consistency=0.6,
            user_validation=0.0
        )
        # Expected: (0.9*0.3 + 1.0*0.25 + 0.8*0.25 + 0.6*0.15 + 0.0*0.05)
        # = 0.27 + 0.25 + 0.20 + 0.09 + 0.0 = 0.81
        assert confidence.overall == 0.81
    
    def test_all_perfect_scores(self):
        confidence = ConfidenceBreakdown(
            name_match=1.0,
            brand_match=1.0,
            spec_match=1.0,
            price_consistency=1.0,
            user_validation=1.0
        )
        assert confidence.overall == 1.0
    
    def test_all_zero_scores(self):
        confidence = ConfidenceBreakdown(
            name_match=0.0,
            brand_match=0.0,
            spec_match=0.0,
            price_consistency=0.0,
            user_validation=0.0
        )
        assert confidence.overall == 0.0


class TestCanonicalProduct:
    """Test CanonicalProduct model"""
    
    def test_canonical_product_creation(self):
        product = CanonicalProduct(
            normalized_name="samsung 55 inch 4k smart tv",
            brand="Samsung",
            category="Electronics",
            subcategory="Televisions",
            product_type="television",
            model_number="UN55TU8000",
            key_features=["4K", "55 inch", "Smart TV", "HDR"],
            specifications=None
        )
        assert product.normalized_name == "samsung 55 inch 4k smart tv"
        assert product.brand == "Samsung"
        assert product.category == "Electronics"
        assert product.subcategory == "Televisions"
        assert product.product_type == "television"
        assert product.model_number == "UN55TU8000"
        assert len(product.key_features) == 4
        assert "4K" in product.key_features


class TestPriceAnalysis:
    """Test PriceAnalysis model"""
    
    def test_price_analysis_with_savings(self):
        savings = SavingsOpportunity(
            amount=5000.0,
            percentage=20.0,
            best_retailer="HP",
            compared_to_retailers=["TWD", "BTV"],
            confidence=0.95
        )
        
        analysis = PriceAnalysis(
            current_best_price=20000.0,
            current_best_retailer="HP",
            savings_opportunity=savings,
            volatility=PriceVolatilityLevel.LOW,
            volatility_score=0.08,
            last_updated=datetime.now()
        )
        
        assert analysis.current_best_price == 20000.0
        assert analysis.current_best_retailer == "HP"
        assert analysis.savings_opportunity.amount == 5000.0
        assert analysis.volatility == PriceVolatilityLevel.LOW
    
    def test_price_analysis_without_savings(self):
        analysis = PriceAnalysis(
            current_best_price=15000.0,
            current_best_retailer="TWD",
            savings_opportunity=None,
            volatility=PriceVolatilityLevel.STABLE,
            volatility_score=0.03,
            last_updated=datetime.now()
        )
        
        assert analysis.savings_opportunity is None
        assert analysis.volatility == PriceVolatilityLevel.STABLE


class TestProductMatchGroup:
    """Test ProductMatchGroup model"""
    
    def test_match_group_confidence_level(self):
        canonical = CanonicalProduct(
            normalized_name="test product",
            brand="TestBrand",
            category="TestCategory",
            product_type="test"
        )
        
        confidence = ConfidenceBreakdown(
            overall=0.96,
            name_match=0.95,
            brand_match=1.0,
            spec_match=0.9,
            price_consistency=0.95,
            user_validation=0.0
        )
        
        matched_products = [
            MatchedProduct(
                product_id="1",
                retailer_code="HP",
                retailer_name="HomePro",
                product_name="Test Product HP",
                current_price=10000.0,
                url="https://example.com/1",
                last_updated=datetime.now()
            ),
            MatchedProduct(
                product_id="2",
                retailer_code="TWD",
                retailer_name="Thai Watsadu",
                product_name="Test Product TWD",
                current_price=9500.0,
                url="https://example.com/2",
                last_updated=datetime.now()
            )
        ]
        
        metadata = MatchMetadata(
            algorithm_version="2.0",
            match_features=[],
            processing_time_ms=150,
            created_at=datetime.now()
        )
        
        price_analysis = PriceAnalysis(
            current_best_price=9500.0,
            current_best_retailer="TWD",
            volatility=PriceVolatilityLevel.LOW,
            volatility_score=0.05,
            last_updated=datetime.now()
        )
        
        group = ProductMatchGroup(
            id="mg_123",
            canonical_product=canonical,
            matched_products=matched_products,
            confidence=confidence,
            match_metadata=metadata,
            price_analysis=price_analysis,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        assert group.confidence_level == MatchConfidenceLevel.EXACT
        assert group.retailer_count == 2
        assert group.price_range == (9500.0, 10000.0)
    
    def test_confidence_level_mapping(self):
        """Test that confidence levels map correctly"""
        test_cases = [
            (0.96, MatchConfidenceLevel.EXACT),
            (0.85, MatchConfidenceLevel.HIGH),
            (0.70, MatchConfidenceLevel.MEDIUM),
            (0.55, MatchConfidenceLevel.LOW),
            (0.40, MatchConfidenceLevel.NONE)
        ]
        
        for score, expected_level in test_cases:
            confidence = ConfidenceBreakdown(
                overall=score,
                name_match=score,
                brand_match=score,
                spec_match=score,
                price_consistency=score
            )
            
            group = ProductMatchGroup(
                id=f"mg_{score}",
                canonical_product=CanonicalProduct(
                    normalized_name="test",
                    brand="test",
                    category="test",
                    product_type="test"
                ),
                matched_products=[],
                confidence=confidence,
                match_metadata=MatchMetadata(
                    algorithm_version="2.0",
                    match_features=[],
                    processing_time_ms=0,
                    created_at=datetime.now()
                ),
                price_analysis=PriceAnalysis(
                    current_best_price=0,
                    current_best_retailer="test",
                    volatility=PriceVolatilityLevel.STABLE,
                    volatility_score=0,
                    last_updated=datetime.now()
                ),
                created_at=datetime.now(),
                updated_at=datetime.now()
            )
            
            assert group.confidence_level == expected_level


class TestMatchingAlgorithmConfig:
    """Test MatchingAlgorithmConfig model"""
    
    def test_default_config(self):
        config = MatchingAlgorithmConfig()
        assert config.min_name_similarity == 0.7
        assert config.min_brand_similarity == 0.8
        assert config.use_ml_matching is True
        assert config.ml_model_name == "sentence-transformers/all-MiniLM-L6-v2"
        assert config.ml_threshold == 0.75
        assert config.price_variance_threshold == 0.5
        assert config.require_same_category is True
        assert config.fuzzy_match_threshold == 0.85
    
    def test_custom_config(self):
        config = MatchingAlgorithmConfig(
            min_name_similarity=0.6,
            min_brand_similarity=0.7,
            use_ml_matching=False,
            price_variance_threshold=0.7,
            require_same_category=False
        )
        assert config.min_name_similarity == 0.6
        assert config.min_brand_similarity == 0.7
        assert config.use_ml_matching is False
        assert config.price_variance_threshold == 0.7
        assert config.require_same_category is False


class TestPriceTrend:
    """Test PriceTrend model"""
    
    def test_price_trend_creation(self):
        trend = PriceTrend(
            period="weekly",
            direction="up",
            change_percentage=5.5,
            average_price=10000.0,
            min_price=9500.0,
            max_price=10500.0,
            volatility_score=0.05
        )
        assert trend.period == "weekly"
        assert trend.direction == "up"
        assert trend.change_percentage == 5.5
        assert trend.average_price == 10000.0
        assert trend.min_price == 9500.0
        assert trend.max_price == 10500.0
        assert trend.volatility_score == 0.05


class TestPriceAnomaly:
    """Test PriceAnomaly model"""
    
    def test_price_anomaly_creation(self):
        anomaly = PriceAnomaly(
            timestamp=datetime.now(),
            anomaly_type="spike",
            severity="high",
            actual_price=15000.0,
            expected_range=(9000.0, 11000.0),
            confidence=0.95
        )
        assert anomaly.anomaly_type == "spike"
        assert anomaly.severity == "high"
        assert anomaly.actual_price == 15000.0
        assert anomaly.expected_range == (9000.0, 11000.0)
        assert anomaly.confidence == 0.95