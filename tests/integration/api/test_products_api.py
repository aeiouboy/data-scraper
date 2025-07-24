"""Integration tests for products API endpoints."""

import pytest
from fastapi.testclient import TestClient
from datetime import datetime, timedelta
from src.api.main import app
# TODO: Update for Supabase - from src.api.database import get_db
from tests.fixtures.database import override_get_db, seeded_db, test_session
from tests.factories import ProductFactory


class TestProductsAPI:
    """Test products API endpoints."""
    
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
    
    @pytest.mark.asyncio
    async def test_get_products_list(self, client, seeded_db):
        """Test getting products list."""
        response = client.get("/api/v1/products")
        assert response.status_code == 200
        
        data = response.json()
        assert "products" in data
        assert "total" in data
        assert "page" in data
        assert "size" in data
        
        assert len(data["products"]) > 0
        assert data["total"] > 0
    
    @pytest.mark.asyncio
    async def test_get_products_with_filters(self, client, seeded_db):
        """Test getting products with filters."""
        # Filter by retailer
        response = client.get("/api/v1/products?retailer=homepro")
        assert response.status_code == 200
        data = response.json()
        assert all(p["retailer_code"] == "homepro" for p in data["products"])
        
        # Filter by price range
        response = client.get("/api/v1/products?min_price=100&max_price=500")
        assert response.status_code == 200
        data = response.json()
        assert all(100 <= p["current_price"] <= 500 for p in data["products"])
        
        # Filter by brand
        response = client.get("/api/v1/products?brand=Brand 0")
        assert response.status_code == 200
        data = response.json()
        assert all(p["brand"] == "Brand 0" for p in data["products"])
        
        # Filter by category
        response = client.get("/api/v1/products?category=Tools")
        assert response.status_code == 200
        data = response.json()
        assert all("Tools" in p["category"] for p in data["products"])
    
    @pytest.mark.asyncio
    async def test_search_products(self, client, seeded_db):
        """Test product search functionality."""
        response = client.get("/api/v1/products/search?q=Test Product")
        assert response.status_code == 200
        
        data = response.json()
        assert len(data["products"]) > 0
        assert all("Test Product" in p["name"] for p in data["products"])
    
    @pytest.mark.asyncio
    async def test_get_product_by_id(self, client, seeded_db):
        """Test getting a single product by ID."""
        # First get a product ID
        list_response = client.get("/api/v1/products?size=1")
        product_id = list_response.json()["products"][0]["id"]
        
        # Get the product
        response = client.get(f"/api/v1/products/{product_id}")
        assert response.status_code == 200
        
        product = response.json()
        assert product["id"] == product_id
        assert "name" in product
        assert "current_price" in product
        assert "retailer_code" in product
    
    @pytest.mark.asyncio
    async def test_get_nonexistent_product(self, client):
        """Test getting a nonexistent product."""
        response = client.get("/api/v1/products/99999")
        assert response.status_code == 404
        assert "detail" in response.json()
    
    @pytest.mark.asyncio
    async def test_get_product_price_history(self, client, seeded_db):
        """Test getting product price history."""
        # Get a product with price history
        list_response = client.get("/api/v1/products?size=1")
        product_id = list_response.json()["products"][0]["id"]
        
        response = client.get(f"/api/v1/products/{product_id}/price-history")
        assert response.status_code == 200
        
        history = response.json()
        assert isinstance(history, list)
        if len(history) > 0:
            assert "price" in history[0]
            assert "recorded_at" in history[0]
    
    @pytest.mark.asyncio
    async def test_get_product_matches(self, client, seeded_db):
        """Test getting product matches."""
        # Get a product
        list_response = client.get("/api/v1/products?size=1")
        product_id = list_response.json()["products"][0]["id"]
        
        response = client.get(f"/api/v1/products/{product_id}/matches")
        assert response.status_code == 200
        
        matches = response.json()
        assert isinstance(matches, list)
        for match in matches:
            assert "matched_product" in match
            assert "confidence_score" in match
            assert "match_type" in match
    
    @pytest.mark.asyncio
    async def test_compare_products(self, client, seeded_db):
        """Test product comparison endpoint."""
        # Get two products
        list_response = client.get("/api/v1/products?size=2")
        products = list_response.json()["products"]
        
        if len(products) >= 2:
            response = client.post(
                "/api/v1/products/compare",
                json={"product_ids": [products[0]["id"], products[1]["id"]]}
            )
            assert response.status_code == 200
            
            comparison = response.json()
            assert "products" in comparison
            assert len(comparison["products"]) == 2
            assert "price_difference" in comparison
            assert "specifications_comparison" in comparison
    
    @pytest.mark.asyncio
    async def test_get_products_by_category(self, client, seeded_db):
        """Test getting products by category."""
        response = client.get("/api/v1/products/category/Tools")
        assert response.status_code == 200
        
        data = response.json()
        assert all("Tools" in p["category"] for p in data["products"])
    
    @pytest.mark.asyncio
    async def test_get_trending_products(self, client, seeded_db):
        """Test getting trending products."""
        response = client.get("/api/v1/products/trending")
        assert response.status_code == 200
        
        products = response.json()
        assert isinstance(products, list)
        assert len(products) <= 10  # Should return top 10
    
    @pytest.mark.asyncio
    async def test_pagination(self, client, seeded_db):
        """Test pagination functionality."""
        # Get first page
        response1 = client.get("/api/v1/products?page=1&size=5")
        assert response1.status_code == 200
        data1 = response1.json()
        
        # Get second page
        response2 = client.get("/api/v1/products?page=2&size=5")
        assert response2.status_code == 200
        data2 = response2.json()
        
        # Products should be different
        ids1 = {p["id"] for p in data1["products"]}
        ids2 = {p["id"] for p in data2["products"]}
        assert len(ids1 & ids2) == 0  # No overlap
    
    @pytest.mark.asyncio
    async def test_sorting(self, client, seeded_db):
        """Test sorting functionality."""
        # Sort by price ascending
        response = client.get("/api/v1/products?sort=price_asc")
        assert response.status_code == 200
        products = response.json()["products"]
        prices = [p["current_price"] for p in products]
        assert prices == sorted(prices)
        
        # Sort by price descending
        response = client.get("/api/v1/products?sort=price_desc")
        assert response.status_code == 200
        products = response.json()["products"]
        prices = [p["current_price"] for p in products]
        assert prices == sorted(prices, reverse=True)
    
    @pytest.mark.asyncio
    async def test_product_stats(self, client, seeded_db):
        """Test product statistics endpoint."""
        response = client.get("/api/v1/products/stats")
        assert response.status_code == 200
        
        stats = response.json()
        assert "total_products" in stats
        assert "retailers" in stats
        assert "brands" in stats
        assert "categories" in stats
        assert "price_range" in stats
    
    @pytest.mark.asyncio
    async def test_export_products(self, client, seeded_db):
        """Test product export functionality."""
        # Export as CSV
        response = client.get("/api/v1/products/export?format=csv")
        assert response.status_code == 200
        assert response.headers["content-type"] == "text/csv; charset=utf-8"
        
        # Export as JSON
        response = client.get("/api/v1/products/export?format=json")
        assert response.status_code == 200
        assert response.headers["content-type"] == "application/json"