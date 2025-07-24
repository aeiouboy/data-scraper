"""Unit tests for product matching utilities."""

import pytest
from src.utils.product_matcher import ProductMatcher
from src.models.product import Product
from tests.factories import ProductFactory


class TestProductMatcher:
    """Test product matching functionality."""
    
    @pytest.fixture
    def matcher(self):
        """Create a product matcher instance."""
        return ProductMatcher()
    
    @pytest.fixture
    def sample_products(self):
        """Create sample products for testing."""
        return [
            Product(
                id=1,
                retailer_code="homepro",
                sku="HP001",
                name="Bosch Professional Drill GBM 13 RE 600W",
                brand="Bosch",
                current_price=2990.0,
                category="Power Tools/Drills",
                specifications={"power": "600W", "speed": "2800rpm", "chuck": "13mm"}
            ),
            Product(
                id=2,
                retailer_code="megahome",
                sku="MH001",
                name="บ๊อช สว่านไฟฟ้า โปร GBM 13 RE 600 วัตต์",
                brand="BOSCH",
                current_price=3150.0,
                category="เครื่องมือไฟฟ้า/สว่าน",
                specifications={"กำลัง": "600 วัตต์", "ความเร็ว": "2800 รอบ/นาที", "หัวจับ": "13 มม."}
            ),
            Product(
                id=3,
                retailer_code="thaiwatsadu",
                sku="TWD001",
                name="Makita Cordless Drill DF457D 18V",
                brand="Makita",
                current_price=4500.0,
                category="Power Tools/Drills",
                specifications={"voltage": "18V", "torque": "42Nm", "speed": "1400rpm"}
            )
        ]
    
    def test_calculate_match_score(self, matcher, sample_products):
        """Test match score calculation between products."""
        # Same product from different retailers (should have high score)
        score1 = matcher.calculate_match_score(sample_products[0], sample_products[1])
        assert score1 > 0.8  # High confidence match
        
        # Different products (should have low score)
        score2 = matcher.calculate_match_score(sample_products[0], sample_products[2])
        assert score2 < 0.5  # Low confidence match
        
        # Same product with itself (should be perfect match)
        score3 = matcher.calculate_match_score(sample_products[0], sample_products[0])
        assert score3 == 1.0
    
    def test_find_matches(self, matcher, sample_products):
        """Test finding matches for a product."""
        matches = matcher.find_matches(sample_products[0], sample_products, threshold=0.7)
        
        # Should find the matching product from another retailer
        assert len(matches) >= 1
        assert any(match['product'].id == 2 for match in matches)
        assert all(match['score'] >= 0.7 for match in matches)
        
        # Should not include the product itself
        assert not any(match['product'].id == 1 for match in matches)
    
    def test_match_by_sku(self, matcher):
        """Test SKU-based matching."""
        product1 = ProductFactory.create(sku="GBM13RE")
        product2 = ProductFactory.create(sku="GBM-13-RE")
        product3 = ProductFactory.create(sku="DIFFERENT")
        
        # Similar SKUs should match
        assert matcher.match_by_sku(product1, product2) > 0.8
        
        # Different SKUs should not match
        assert matcher.match_by_sku(product1, product3) < 0.3
    
    def test_match_by_name(self, matcher, sample_products):
        """Test name-based matching."""
        # Thai and English names for same product
        score = matcher.match_by_name(sample_products[0], sample_products[1])
        assert score > 0.7  # Should recognize as similar despite language difference
        
        # Different products
        score2 = matcher.match_by_name(sample_products[0], sample_products[2])
        assert score2 < 0.5
    
    def test_match_by_specifications(self, matcher, sample_products):
        """Test specification-based matching."""
        # Same specs in different languages
        score = matcher.match_by_specifications(sample_products[0], sample_products[1])
        assert score > 0.8  # Should match 600W with 600 วัตต์
        
        # Different specs
        score2 = matcher.match_by_specifications(sample_products[0], sample_products[2])
        assert score2 < 0.3
    
    def test_match_by_price(self, matcher):
        """Test price-based matching."""
        product1 = ProductFactory.create(current_price=1000.0)
        product2 = ProductFactory.create(current_price=1050.0)  # 5% difference
        product3 = ProductFactory.create(current_price=1500.0)  # 50% difference
        
        # Small price difference
        assert matcher.match_by_price(product1, product2) > 0.9
        
        # Large price difference
        assert matcher.match_by_price(product1, product3) < 0.5
    
    def test_group_matches(self, matcher):
        """Test grouping products by matches."""
        # Create products that should match
        products = []
        
        # Group 1: Bosch drills
        products.extend([
            ProductFactory.create(name="Bosch Drill GBM 13", brand="Bosch", current_price=3000),
            ProductFactory.create(name="บ๊อช สว่าน GBM 13", brand="BOSCH", current_price=3100),
            ProductFactory.create(name="BOSCH GBM13 Drill", brand="Bosch", current_price=2900)
        ])
        
        # Group 2: Makita drills
        products.extend([
            ProductFactory.create(name="Makita Drill DF457", brand="Makita", current_price=4500),
            ProductFactory.create(name="มากิต้า สว่าน DF457", brand="MAKITA", current_price=4600)
        ])
        
        # Single product
        products.append(
            ProductFactory.create(name="Stanley Hammer", brand="Stanley", current_price=500)
        )
        
        groups = matcher.group_matches(products, threshold=0.7)
        
        # Should create 3 groups
        assert len(groups) == 3
        
        # Check group sizes
        group_sizes = sorted([len(g) for g in groups])
        assert group_sizes == [1, 2, 3]
    
    def test_match_with_confidence_levels(self, matcher):
        """Test different confidence levels for matching."""
        product1 = ProductFactory.create(
            name="Bosch Professional Drill GBM 13 RE",
            brand="Bosch",
            sku="GBM13RE",
            current_price=3000
        )
        
        # High confidence match (same product)
        product2 = ProductFactory.create(
            name="BOSCH Pro Drill GBM 13 RE",
            brand="BOSCH",
            sku="GBM-13-RE",
            current_price=3100
        )
        
        # Medium confidence match (similar product)
        product3 = ProductFactory.create(
            name="Bosch Drill GBM 13",
            brand="Bosch",
            sku="GBM13",
            current_price=2800
        )
        
        # Low confidence match (different product)
        product4 = ProductFactory.create(
            name="Makita Drill",
            brand="Makita",
            sku="MKT123",
            current_price=4000
        )
        
        high_score = matcher.calculate_match_score(product1, product2)
        medium_score = matcher.calculate_match_score(product1, product3)
        low_score = matcher.calculate_match_score(product1, product4)
        
        assert high_score > 0.85
        assert 0.5 < medium_score < 0.85
        assert low_score < 0.5
    
    def test_fuzzy_brand_matching(self, matcher):
        """Test fuzzy matching for brand names."""
        brands_that_match = [
            ("Bosch", "BOSCH"),
            ("bosch", "บ๊อช"),
            ("Makita", "มากิต้า"),
            ("3M", "ทรีเอ็ม"),
            ("Stanley", "สแตนเล่ย์")
        ]
        
        for brand1, brand2 in brands_that_match:
            product1 = ProductFactory.create(brand=brand1)
            product2 = ProductFactory.create(brand=brand2)
            assert matcher.match_by_brand(product1, product2) > 0.9
    
    def test_handle_missing_data(self, matcher):
        """Test matching with missing data."""
        complete_product = ProductFactory.create(
            name="Test Product",
            brand="TestBrand",
            sku="TEST123",
            specifications={"power": "600W"}
        )
        
        # Missing brand
        no_brand = ProductFactory.create(name="Test Product", brand=None, sku="TEST123")
        score1 = matcher.calculate_match_score(complete_product, no_brand)
        assert score1 > 0.5  # Should still match on other attributes
        
        # Missing SKU
        no_sku = ProductFactory.create(name="Test Product", brand="TestBrand", sku=None)
        score2 = matcher.calculate_match_score(complete_product, no_sku)
        assert score2 > 0.5
        
        # Missing specifications
        no_specs = ProductFactory.create(
            name="Test Product",
            brand="TestBrand",
            sku="TEST123",
            specifications=None
        )
        score3 = matcher.calculate_match_score(complete_product, no_specs)
        assert score3 > 0.5