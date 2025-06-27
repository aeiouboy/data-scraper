"""
Unit tests for SupabaseService class
"""
import pytest
from unittest.mock import Mock, AsyncMock, patch
from app.services.supabase_service import SupabaseService


class TestSupabaseService:
    """Test suite for SupabaseService"""
    
    def setup_method(self):
        """Setup for each test method"""
        with patch('app.services.supabase_service.create_async_client') as mock_create_client:
            mock_client = AsyncMock()
            mock_create_client.return_value = mock_client
            self.service = SupabaseService()
            self.mock_client = mock_client
    
    @pytest.mark.asyncio
    async def test_upsert_product_success(self, test_product_data):
        """Test successful product upsert"""
        from app.models.product import Product
        
        # Create product instance
        product = Product(**test_product_data)
        
        # Mock successful upsert
        mock_response = Mock()
        mock_response.data = [{"id": "test-uuid", **test_product_data}]
        mock_response.error = None
        
        self.mock_client.table.return_value.upsert.return_value.execute.return_value = mock_response
        
        result = await self.service.upsert_product(product)
        
        assert result is not None
        assert result["id"] == "test-uuid"
        assert result["sku"] == test_product_data["sku"]
    
    @pytest.mark.asyncio
    async def test_upsert_product_failure(self, test_product_data):
        """Test product upsert failure"""
        from app.models.product import Product
        
        product = Product(**test_product_data)
        
        # Mock failed upsert
        mock_response = Mock()
        mock_response.data = None
        mock_response.error = {"message": "Upsert failed"}
        
        self.mock_client.table.return_value.upsert.return_value.execute.return_value = mock_response
        
        result = await self.service.upsert_product(product)
        
        assert result is None
    
    @pytest.mark.asyncio
    async def test_get_product_by_id_success(self):
        """Test successful product retrieval by ID"""
        product_id = "test-uuid"
        expected_product = {
            "id": product_id,
            "sku": "TEST123",
            "name": "Test Product"
        }
        
        # Mock successful query
        mock_response = Mock()
        mock_response.data = [expected_product]
        mock_response.error = None
        
        self.mock_client.table.return_value.select.return_value.eq.return_value.execute.return_value = mock_response
        
        result = await self.service.get_product_by_id(product_id)
        
        assert result == expected_product
        self.mock_client.table.assert_called_with("products")
    
    @pytest.mark.asyncio
    async def test_get_product_by_id_not_found(self):
        """Test product retrieval when not found"""
        product_id = "non-existent"
        
        # Mock empty result
        mock_response = Mock()
        mock_response.data = []
        mock_response.error = None
        
        self.mock_client.table.return_value.select.return_value.eq.return_value.execute.return_value = mock_response
        
        result = await self.service.get_product_by_id(product_id)
        
        assert result is None
    
    @pytest.mark.asyncio
    async def test_search_products_success(self):
        """Test successful product search"""
        query = "drill"
        filters = {"brands": ["TestBrand"], "min_price": 1000}
        
        expected_products = [
            {"id": "1", "name": "Electric Drill", "brand": "TestBrand"},
            {"id": "2", "name": "Cordless Drill", "brand": "TestBrand"}
        ]
        
        # Mock successful search
        mock_response = Mock()
        mock_response.data = expected_products
        mock_response.error = None
        
        # Mock the query chain
        mock_query = Mock()
        mock_query.execute.return_value = mock_response
        mock_query.range.return_value = mock_query
        mock_query.order.return_value = mock_query
        mock_query.gte.return_value = mock_query
        mock_query.in_.return_value = mock_query
        mock_query.textSearch.return_value = mock_query
        
        self.mock_client.table.return_value.select.return_value = mock_query
        
        result = await self.service.search_products(
            query=query,
            filters=filters,
            page=1,
            limit=20
        )
        
        assert "products" in result
        assert "total" in result
        assert len(result["products"]) == 2
    
    @pytest.mark.asyncio
    async def test_create_scrape_job_success(self):
        """Test successful scrape job creation"""
        job_data = {
            "job_type": "category",
            "target_url": "https://www.homepro.co.th/c/tools"
        }
        
        expected_job = {
            "id": "job-uuid",
            "status": "pending",
            **job_data
        }
        
        # Mock successful job creation
        mock_response = Mock()
        mock_response.data = [expected_job]
        mock_response.error = None
        
        self.mock_client.table.return_value.insert.return_value.execute.return_value = mock_response
        
        result = await self.service.create_scrape_job(**job_data)
        
        assert result == expected_job
        self.mock_client.table.assert_called_with("scrape_jobs")
    
    @pytest.mark.asyncio
    async def test_update_scrape_job_success(self):
        """Test successful scrape job update"""
        job_id = "job-uuid"
        updates = {"status": "completed", "success_items": 10}
        
        # Mock successful update
        mock_response = Mock()
        mock_response.data = [{"id": job_id, **updates}]
        mock_response.error = None
        
        self.mock_client.table.return_value.update.return_value.eq.return_value.execute.return_value = mock_response
        
        result = await self.service.update_scrape_job(job_id, updates)
        
        assert result is True
    
    @pytest.mark.asyncio
    async def test_get_product_stats_success(self):
        """Test successful product statistics retrieval"""
        expected_stats = {
            "total_products": 1000,
            "total_brands": 50,
            "avg_price": 2500.0
        }
        
        # Mock successful stats query
        mock_response = Mock()
        mock_response.data = [expected_stats]
        mock_response.error = None
        
        self.mock_client.table.return_value.select.return_value.execute.return_value = mock_response
        
        result = await self.service.get_product_stats()
        
        assert result == expected_stats
        self.mock_client.table.assert_called_with("product_stats")
    
    @pytest.mark.asyncio
    async def test_get_all_brands_success(self):
        """Test successful brands retrieval"""
        expected_brands = ["Brand A", "Brand B", "Brand C"]
        
        # Mock successful brands query
        mock_response = Mock()
        mock_response.data = [{"brand": brand} for brand in expected_brands]
        mock_response.error = None
        
        self.mock_client.table.return_value.select.return_value.is_.return_value.order.return_value.execute.return_value = mock_response
        
        result = await self.service.get_all_brands()
        
        assert result == expected_brands
    
    @pytest.mark.asyncio
    async def test_get_categories_success(self):
        """Test successful categories retrieval"""
        expected_categories = [
            {"id": "1", "name": "Electronics"},
            {"id": "2", "name": "Tools"}
        ]
        
        # Mock successful categories query
        mock_response = Mock()
        mock_response.data = expected_categories
        mock_response.error = None
        
        self.mock_client.table.return_value.select.return_value.order.return_value.execute.return_value = mock_response
        
        result = await self.service.get_categories()
        
        assert result == expected_categories
        self.mock_client.table.assert_called_with("categories")
    
    @pytest.mark.asyncio
    async def test_batch_upsert_products_success(self, test_product_data):
        """Test successful batch product upsert"""
        from app.models.product import Product
        
        products = [Product(**test_product_data) for _ in range(3)]
        
        # Mock successful batch upsert
        mock_response = Mock()
        mock_response.data = [{"id": f"uuid-{i}"} for i in range(3)]
        mock_response.error = None
        
        self.mock_client.table.return_value.upsert.return_value.execute.return_value = mock_response
        
        result = await self.service.batch_upsert_products(products)
        
        assert result == 3  # Number of successfully upserted products
    
    @pytest.mark.asyncio
    async def test_get_price_history_success(self):
        """Test successful price history retrieval"""
        product_id = "test-uuid"
        expected_history = [
            {"price": 2490.0, "recorded_at": "2025-06-27T10:00:00Z"},
            {"price": 2390.0, "recorded_at": "2025-06-26T10:00:00Z"}
        ]
        
        # Mock successful price history query
        mock_response = Mock()
        mock_response.data = expected_history
        mock_response.error = None
        
        mock_query = Mock()
        mock_query.execute.return_value = mock_response
        mock_query.limit.return_value = mock_query
        mock_query.order.return_value = mock_query
        mock_query.eq.return_value = mock_query
        
        self.mock_client.table.return_value.select.return_value = mock_query
        
        result = await self.service.get_price_history(product_id, limit=30)
        
        assert result == expected_history
        self.mock_client.table.assert_called_with("price_history")
    
    @pytest.mark.asyncio
    async def test_add_price_history_success(self):
        """Test successful price history addition"""
        product_id = "test-uuid"
        price = 2490.0
        original_price = 2990.0
        
        # Mock successful price history insert
        mock_response = Mock()
        mock_response.data = [{"id": "history-uuid"}]
        mock_response.error = None
        
        self.mock_client.table.return_value.insert.return_value.execute.return_value = mock_response
        
        result = await self.service.add_price_history(product_id, price, original_price)
        
        assert result is True
    
    @pytest.mark.asyncio
    async def test_get_daily_scrape_stats_success(self):
        """Test successful daily scrape stats retrieval"""
        expected_stats = [
            {"date": "2025-06-27", "jobs_run": 5, "avg_success_rate": 95.0},
            {"date": "2025-06-26", "jobs_run": 3, "avg_success_rate": 87.5}
        ]
        
        # Mock successful stats query
        mock_response = Mock()
        mock_response.data = expected_stats
        mock_response.error = None
        
        mock_query = Mock()
        mock_query.execute.return_value = mock_response
        mock_query.limit.return_value = mock_query
        mock_query.order.return_value = mock_query
        
        self.mock_client.table.return_value.select.return_value = mock_query
        
        result = await self.service.get_daily_scrape_stats(days=7)
        
        assert result == expected_stats
        self.mock_client.table.assert_called_with("daily_scrape_stats")
    
    @pytest.mark.asyncio
    async def test_error_handling(self):
        """Test error handling in service methods"""
        # Mock database error
        mock_response = Mock()
        mock_response.data = None
        mock_response.error = {"message": "Database connection failed"}
        
        self.mock_client.table.return_value.select.return_value.execute.return_value = mock_response
        
        result = await self.service.get_product_stats()
        
        # Should return None on error
        assert result is None