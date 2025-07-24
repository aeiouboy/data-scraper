"""Integration tests for matching API endpoints."""

import pytest
from fastapi.testclient import TestClient
from src.api.main import app
# TODO: Update for Supabase - from src.api.database import get_db
from src.models.product import Product
from tests.fixtures.database import override_get_db, seeded_db, test_session
from tests.factories import ProductFactory, MatchFactory


class TestMatchingAPI:
    """Test matching API endpoints."""
    
    @pytest.fixture(autouse=True)
    def setup(self, test_session, override_get_db):
        """Set up test client with database override."""
        app.dependency_overrides[get_db] = override_get_db
        yield
        app.dependency_overrides.clear()
    
    @pytest.fixture
    def client(self):
        """Create test client."""
        return TestClient(app)
    
    @pytest.fixture
    def matched_products(self, test_session):
        """Create products with matches."""
        # Create matching products
        product1 = ProductFactory.create(
            retailer_code="homepro",
            name="Bosch Drill GBM 13 RE",
            brand="Bosch",
            current_price=2990.0
        )
        product2 = ProductFactory.create(
            retailer_code="megahome",
            name="บ๊อช สว่าน GBM 13 RE",
            brand="BOSCH",
            current_price=3100.0
        )
        product3 = ProductFactory.create(
            retailer_code="thaiwatsadu",
            name="Makita Drill DF457",
            brand="Makita",
            current_price=4500.0
        )
        
        test_session.add_all([product1, product2, product3])
        test_session.commit()
        
        # Create matches
        match1 = MatchFactory.create(
            product1=product1,
            product2=product2,
            confidence_score=0.92,
            match_type="automatic"
        )
        match2 = MatchFactory.create(
            product1=product1,
            product2=product3,
            confidence_score=0.35,
            match_type="rejected"
        )
        
        test_session.add_all([match1, match2])
        test_session.commit()
        
        return [product1, product2, product3]
    
    @pytest.mark.asyncio
    async def test_find_matches(self, client, seeded_db):
        """Test finding matches for a product."""
        # Get a product
        products_response = client.get("/api/v1/products?size=1")
        product_id = products_response.json()["products"][0]["id"]
        
        response = client.post(f"/api/v1/matching/find/{product_id}")
        assert response.status_code == 200
        
        matches = response.json()
        assert isinstance(matches, list)
        for match in matches:
            assert "product" in match
            assert "confidence_score" in match
            assert 0 <= match["confidence_score"] <= 1
    
    @pytest.mark.asyncio
    async def test_create_manual_match(self, client, matched_products):
        """Test creating a manual match."""
        response = client.post("/api/v1/matching/manual", json={
            "product1_id": matched_products[0].id,
            "product2_id": matched_products[2].id,
            "confidence_score": 1.0
        })
        
        assert response.status_code == 200
        match = response.json()
        assert match["match_type"] == "manual"
        assert match["confidence_score"] == 1.0
    
    @pytest.mark.asyncio
    async def test_update_match(self, client, matched_products, test_session):
        """Test updating an existing match."""
        # Get existing match
        match = test_session.query(ProductMatch).first()
        
        response = client.put(f"/api/v1/matching/{match.id}", json={
            "confidence_score": 0.95,
            "match_type": "verified"
        })
        
        assert response.status_code == 200
        updated = response.json()
        assert updated["confidence_score"] == 0.95
        assert updated["match_type"] == "verified"
    
    @pytest.mark.asyncio
    async def test_delete_match(self, client, matched_products, test_session):
        """Test deleting a match."""
        # Get existing match
        match = test_session.query(ProductMatch).first()
        
        response = client.delete(f"/api/v1/matching/{match.id}")
        assert response.status_code == 200
        
        # Verify deletion
        deleted_match = test_session.query(ProductMatch).filter_by(id=match.id).first()
        assert deleted_match is None
    
    @pytest.mark.asyncio
    async def test_bulk_match(self, client, seeded_db):
        """Test bulk matching operation."""
        response = client.post("/api/v1/matching/bulk", json={
            "retailer1": "homepro",
            "retailer2": "megahome",
            "threshold": 0.8
        })
        
        assert response.status_code == 200
        result = response.json()
        assert "matches_found" in result
        assert "processing_time" in result
        assert isinstance(result["matches_found"], int)
    
    @pytest.mark.asyncio
    async def test_get_match_suggestions(self, client, seeded_db):
        """Test getting match suggestions."""
        response = client.get("/api/v1/matching/suggestions?limit=10")
        assert response.status_code == 200
        
        suggestions = response.json()
        assert isinstance(suggestions, list)
        assert len(suggestions) <= 10
        
        for suggestion in suggestions:
            assert "product1" in suggestion
            assert "product2" in suggestion
            assert "confidence_score" in suggestion
            assert 0.5 <= suggestion["confidence_score"] <= 0.8  # Suggestions range
    
    @pytest.mark.asyncio
    async def test_verify_match(self, client, matched_products, test_session):
        """Test verifying a suggested match."""
        # Create a suggested match
        match = MatchFactory.create(
            product1=matched_products[0],
            product2=matched_products[2],
            confidence_score=0.75,
            match_type="suggested"
        )
        test_session.add(match)
        test_session.commit()
        
        response = client.post(f"/api/v1/matching/{match.id}/verify")
        assert response.status_code == 200
        
        verified = response.json()
        assert verified["match_type"] == "verified"
        assert verified["confidence_score"] >= match.confidence_score
    
    @pytest.mark.asyncio
    async def test_reject_match(self, client, matched_products, test_session):
        """Test rejecting a suggested match."""
        # Create a suggested match
        match = MatchFactory.create(
            product1=matched_products[0],
            product2=matched_products[2],
            confidence_score=0.75,
            match_type="suggested"
        )
        test_session.add(match)
        test_session.commit()
        
        response = client.post(f"/api/v1/matching/{match.id}/reject")
        assert response.status_code == 200
        
        rejected = response.json()
        assert rejected["match_type"] == "rejected"
    
    @pytest.mark.asyncio
    async def test_get_match_stats(self, client, matched_products, test_session):
        """Test getting matching statistics."""
        # Create various matches
        for i in range(10):
            match = MatchFactory.create(
                product1=matched_products[0],
                product2=matched_products[1],
                confidence_score=0.5 + (i * 0.05),
                match_type=["automatic", "manual", "suggested", "rejected"][i % 4]
            )
            test_session.add(match)
        test_session.commit()
        
        response = client.get("/api/v1/matching/stats")
        assert response.status_code == 200
        
        stats = response.json()
        assert "total_matches" in stats
        assert "matches_by_type" in stats
        assert "average_confidence" in stats
        assert "matches_by_retailer_pair" in stats
    
    @pytest.mark.asyncio
    async def test_match_by_sku(self, client, test_session):
        """Test matching products by SKU."""
        # Create products with similar SKUs
        product1 = ProductFactory.create(sku="ABC-123", retailer_code="homepro")
        product2 = ProductFactory.create(sku="ABC123", retailer_code="megahome")
        product3 = ProductFactory.create(sku="XYZ-789", retailer_code="thaiwatsadu")
        
        test_session.add_all([product1, product2, product3])
        test_session.commit()
        
        response = client.post("/api/v1/matching/by-sku", json={
            "sku_pattern": "ABC",
            "fuzzy": True
        })
        
        assert response.status_code == 200
        matches = response.json()
        assert len(matches) >= 1
        assert any(m["product1_id"] == product1.id and m["product2_id"] == product2.id 
                  for m in matches)
    
    @pytest.mark.asyncio
    async def test_match_history(self, client, matched_products, test_session):
        """Test getting match history for a product."""
        response = client.get(f"/api/v1/matching/history/{matched_products[0].id}")
        assert response.status_code == 200
        
        history = response.json()
        assert isinstance(history, list)
        for entry in history:
            assert "matched_product" in entry
            assert "confidence_score" in entry
            assert "match_type" in entry
            assert "created_at" in entry
    
    @pytest.mark.asyncio
    async def test_export_matches(self, client, matched_products):
        """Test exporting matches."""
        response = client.get("/api/v1/matching/export?format=csv")
        assert response.status_code == 200
        assert response.headers["content-type"] == "text/csv; charset=utf-8"
        
        # Test JSON export
        response = client.get("/api/v1/matching/export?format=json")
        assert response.status_code == 200
        data = response.json()
        assert "matches" in data
        assert isinstance(data["matches"], list)
    
    @pytest.mark.asyncio
    async def test_match_validation(self, client, test_session):
        """Test match validation rules."""
        product = ProductFactory.create()
        test_session.add(product)
        test_session.commit()
        
        # Test matching product with itself
        response = client.post("/api/v1/matching/manual", json={
            "product1_id": product.id,
            "product2_id": product.id,
            "confidence_score": 1.0
        })
        assert response.status_code == 400
        assert "cannot match with itself" in response.json()["detail"].lower()
        
        # Test invalid confidence score
        product2 = ProductFactory.create()
        test_session.add(product2)
        test_session.commit()
        
        response = client.post("/api/v1/matching/manual", json={
            "product1_id": product.id,
            "product2_id": product2.id,
            "confidence_score": 1.5  # Invalid score > 1
        })
        assert response.status_code == 422
    
    @pytest.mark.asyncio
    async def test_machine_learning_match(self, client, seeded_db):
        """Test ML-based matching endpoint."""
        response = client.post("/api/v1/matching/ml/train")
        assert response.status_code in [200, 501]  # 501 if ML not implemented
        
        if response.status_code == 200:
            result = response.json()
            assert "model_version" in result
            assert "accuracy" in result
            assert "training_samples" in result