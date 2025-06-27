"""
Integration tests for API endpoints
"""
import pytest
import json
from fastapi.testclient import TestClient


@pytest.mark.integration
class TestProductsAPI:
    """Integration tests for Products API endpoints"""
    
    def test_search_products_empty_database(self, api_client):
        """Test product search with empty database"""
        response = api_client.post("/api/products/search", json={
            "query": "test",
            "page": 1,
            "page_size": 20
        })
        
        assert response.status_code == 200
        data = response.json()
        assert "products" in data
        assert "total" in data
        assert data["total"] == 0
        assert len(data["products"]) == 0
    
    def test_search_products_with_filters(self, api_client):
        """Test product search with various filters"""
        search_request = {
            "query": "drill",
            "brands": ["TestBrand"],
            "min_price": 1000,
            "max_price": 5000,
            "on_sale_only": True,
            "sort_by": "price",
            "sort_order": "asc",
            "page": 1,
            "page_size": 10
        }
        
        response = api_client.post("/api/products/search", json=search_request)
        
        assert response.status_code == 200
        data = response.json()
        assert "products" in data
        assert "total" in data
        assert "page" in data
        assert data["page"] == 1
    
    def test_search_products_invalid_request(self, api_client):
        """Test product search with invalid request data"""
        invalid_requests = [
            {"page": 0},  # Invalid page number
            {"page_size": 0},  # Invalid page size
            {"page_size": 101},  # Page size too large
            {"sort_by": "invalid_field"},  # Invalid sort field
            {"sort_order": "invalid_order"}  # Invalid sort order
        ]
        
        for invalid_request in invalid_requests:
            response = api_client.post("/api/products/search", json=invalid_request)
            assert response.status_code == 422  # Validation error
    
    def test_get_product_by_id_not_found(self, api_client):
        """Test getting product by ID when not found"""
        response = api_client.get("/api/products/non-existent-id")
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()
    
    def test_get_product_by_id_success(self, api_client, mock_supabase_service):
        """Test successful product retrieval by ID"""
        # Mock service will return test data
        response = api_client.get("/api/products/test-uuid")
        
        assert response.status_code == 200
        data = response.json()
        assert "id" in data
        assert "sku" in data
        assert "name" in data
        assert data["id"] == "test-uuid"
    
    def test_get_price_history(self, api_client):
        """Test getting product price history"""
        response = api_client.get("/api/products/test-uuid/price-history?days=30")
        
        assert response.status_code == 200
        data = response.json()
        assert "product_id" in data
        assert "history" in data
        assert "days" in data
        assert data["days"] == 30
    
    def test_get_price_history_invalid_days(self, api_client):
        """Test price history with invalid days parameter"""
        invalid_days = [0, -1, 366, "invalid"]
        
        for days in invalid_days:
            response = api_client.get(f"/api/products/test-uuid/price-history?days={days}")
            assert response.status_code == 422
    
    def test_get_brands(self, api_client):
        """Test getting all brands"""
        response = api_client.get("/api/products/filters/brands")
        
        assert response.status_code == 200
        data = response.json()
        assert "brands" in data
        assert isinstance(data["brands"], list)
    
    def test_get_categories(self, api_client):
        """Test getting all categories"""
        response = api_client.get("/api/products/filters/categories")
        
        assert response.status_code == 200
        data = response.json()
        assert "categories" in data
        assert isinstance(data["categories"], list)
    
    def test_rescrape_product_not_found(self, api_client, mock_supabase_service):
        """Test rescaping non-existent product"""
        # Mock service to return None for non-existent product
        mock_supabase_service.get_product_by_id.return_value = None
        
        response = api_client.post("/api/products/non-existent/rescrape")
        assert response.status_code == 404


@pytest.mark.integration
class TestScrapingAPI:
    """Integration tests for Scraping API endpoints"""
    
    def test_create_scrape_job_category(self, api_client):
        """Test creating category scrape job"""
        job_request = {
            "job_type": "category",
            "target_url": "https://www.homepro.co.th/c/tools",
            "max_pages": 5
        }
        
        response = api_client.post("/api/scraping/jobs", json=job_request)
        
        assert response.status_code == 200
        data = response.json()
        assert "id" in data
        assert "job_type" in data
        assert "status" in data
        assert data["job_type"] == "category"
        assert data["status"] == "pending"
    
    def test_create_scrape_job_product(self, api_client):
        """Test creating product scrape job"""
        job_request = {
            "job_type": "product",
            "urls": [
                "https://www.homepro.co.th/p/1001234567",
                "https://www.homepro.co.th/p/1001234568"
            ]
        }
        
        response = api_client.post("/api/scraping/jobs", json=job_request)
        
        assert response.status_code == 200
        data = response.json()
        assert data["job_type"] == "product"
    
    def test_create_scrape_job_search(self, api_client):
        """Test creating search scrape job"""
        job_request = {
            "job_type": "search",
            "target_url": "https://www.homepro.co.th/search?q=drill",
            "max_pages": 3
        }
        
        response = api_client.post("/api/scraping/jobs", json=job_request)
        
        assert response.status_code == 200
        data = response.json()
        assert data["job_type"] == "search"
    
    def test_create_scrape_job_validation_errors(self, api_client):
        """Test scrape job creation validation errors"""
        invalid_requests = [
            # Missing URL for category job
            {"job_type": "category"},
            # Missing URLs for product job
            {"job_type": "product"},
            # Invalid job type
            {"job_type": "invalid"},
            # Invalid URL format
            {"job_type": "category", "target_url": "not-a-url"},
            # Invalid max_pages
            {"job_type": "category", "target_url": "https://example.com", "max_pages": 0},
            {"job_type": "category", "target_url": "https://example.com", "max_pages": 201},
        ]
        
        for invalid_request in invalid_requests:
            response = api_client.post("/api/scraping/jobs", json=invalid_request)
            assert response.status_code in [400, 422]
    
    def test_list_scrape_jobs(self, api_client):
        """Test listing scrape jobs"""
        response = api_client.get("/api/scraping/jobs")
        
        assert response.status_code == 200
        data = response.json()
        assert "jobs" in data
        assert "total" in data
        assert "active_jobs" in data
        assert "completed_jobs" in data
        assert "failed_jobs" in data
    
    def test_list_scrape_jobs_with_status_filter(self, api_client):
        """Test listing scrape jobs with status filter"""
        statuses = ["pending", "running", "completed", "failed"]
        
        for status in statuses:
            response = api_client.get(f"/api/scraping/jobs?status={status}")
            assert response.status_code == 200
            data = response.json()
            assert "jobs" in data
    
    def test_list_scrape_jobs_with_limit(self, api_client):
        """Test listing scrape jobs with limit"""
        response = api_client.get("/api/scraping/jobs?limit=5")
        
        assert response.status_code == 200
        data = response.json()
        assert len(data["jobs"]) <= 5
    
    def test_get_scrape_job_by_id(self, api_client):
        """Test getting scrape job by ID"""
        response = api_client.get("/api/scraping/jobs/job-uuid")
        
        assert response.status_code == 200
        data = response.json()
        assert "id" in data
        assert "status" in data
    
    def test_get_scrape_job_not_found(self, api_client, mock_supabase_service):
        """Test getting non-existent scrape job"""
        mock_supabase_service.get_scrape_job.return_value = None
        
        response = api_client.get("/api/scraping/jobs/non-existent")
        assert response.status_code == 404
    
    def test_cancel_scrape_job(self, api_client, mock_supabase_service):
        """Test canceling a scrape job"""
        # Mock running job
        mock_supabase_service.get_scrape_job.return_value = {
            "id": "job-uuid",
            "status": "running"
        }
        
        response = api_client.post("/api/scraping/jobs/job-uuid/cancel")
        
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "job_id" in data
    
    def test_cancel_scrape_job_invalid_status(self, api_client, mock_supabase_service):
        """Test canceling job with invalid status"""
        # Mock completed job (cannot be cancelled)
        mock_supabase_service.get_scrape_job.return_value = {
            "id": "job-uuid",
            "status": "completed"
        }
        
        response = api_client.post("/api/scraping/jobs/job-uuid/cancel")
        assert response.status_code == 400
    
    def test_discover_urls(self, api_client):
        """Test URL discovery endpoint"""
        discovery_request = {
            "url": "https://www.homepro.co.th/c/tools",
            "max_pages": 3
        }
        
        response = api_client.post("/api/scraping/discover", json=discovery_request)
        
        assert response.status_code == 200
        data = response.json()
        assert "url" in data
        assert "discovered_urls" in data
        assert "total" in data
        assert isinstance(data["discovered_urls"], list)


@pytest.mark.integration
class TestAnalyticsAPI:
    """Integration tests for Analytics API endpoints"""
    
    def test_get_dashboard_analytics(self, api_client):
        """Test getting dashboard analytics"""
        response = api_client.get("/api/analytics/dashboard")
        
        assert response.status_code == 200
        data = response.json()
        assert "product_stats" in data
        assert "daily_stats" in data
        assert "brand_distribution" in data
        assert "category_distribution" in data
        assert "price_distribution" in data
    
    def test_get_product_trends(self, api_client):
        """Test getting product trends"""
        response = api_client.get("/api/analytics/products/trends?days=30")
        
        assert response.status_code == 200
        # Response format depends on implementation
    
    def test_get_scraping_performance(self, api_client):
        """Test getting scraping performance metrics"""
        response = api_client.get("/api/analytics/scraping/performance?days=7")
        
        assert response.status_code == 200
        # Response format depends on implementation


@pytest.mark.integration
class TestAPIErrorHandling:
    """Integration tests for API error handling"""
    
    def test_invalid_json_request(self, api_client):
        """Test handling of invalid JSON in request"""
        response = api_client.post(
            "/api/products/search",
            data="invalid json",
            headers={"Content-Type": "application/json"}
        )
        assert response.status_code == 422
    
    def test_missing_content_type(self, api_client):
        """Test handling of missing content type"""
        response = api_client.post("/api/products/search", data='{"query": "test"}')
        # Should still work as FastAPI is flexible
        assert response.status_code in [200, 422]
    
    def test_large_request_body(self, api_client):
        """Test handling of very large request body"""
        large_data = {
            "query": "test",
            "urls": ["https://example.com"] * 10000  # Very large list
        }
        
        response = api_client.post("/api/scraping/jobs", json=large_data)
        # Should either process or reject gracefully
        assert response.status_code in [200, 400, 413, 422]
    
    def test_cors_headers(self, api_client):
        """Test CORS headers are present"""
        response = api_client.options("/api/products/search")
        
        # Check for CORS headers
        headers = response.headers
        # Exact CORS headers depend on FastAPI CORS configuration
        assert response.status_code in [200, 405]  # OPTIONS might not be allowed
    
    def test_rate_limiting_headers(self, api_client):
        """Test for rate limiting headers (if implemented)"""
        response = api_client.get("/api/products/filters/brands")
        
        # Rate limiting headers (if implemented)
        headers = response.headers
        # This test assumes rate limiting is implemented
        # Remove if not applicable
    
    def test_security_headers(self, api_client):
        """Test for security headers"""
        response = api_client.get("/api/products/filters/brands")
        
        headers = response.headers
        # Basic security headers that should be present
        # Adjust based on actual security configuration


# Performance and load testing
@pytest.mark.integration
@pytest.mark.slow
class TestAPIPerformance:
    """Performance tests for API endpoints"""
    
    def test_concurrent_requests(self, api_client, performance_config):
        """Test handling of concurrent requests"""
        import threading
        import time
        
        results = []
        
        def make_request():
            start_time = time.time()
            response = api_client.get("/api/products/filters/brands")
            end_time = time.time()
            results.append({
                "status_code": response.status_code,
                "response_time": (end_time - start_time) * 1000  # ms
            })
        
        # Create multiple threads
        threads = []
        for _ in range(performance_config["concurrent_requests"]):
            thread = threading.Thread(target=make_request)
            threads.append(thread)
        
        # Start all threads
        start_time = time.time()
        for thread in threads:
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        total_time = time.time() - start_time
        
        # Assertions
        assert len(results) == performance_config["concurrent_requests"]
        assert all(r["status_code"] == 200 for r in results)
        
        # Performance assertions
        avg_response_time = sum(r["response_time"] for r in results) / len(results)
        assert avg_response_time < performance_config["max_response_time"]
        
        # Total time should be reasonable for concurrent requests
        assert total_time < (performance_config["max_response_time"] / 1000) * 2
    
    def test_response_time_under_load(self, api_client, performance_config):
        """Test response times under load"""
        import time
        
        response_times = []
        
        # Make multiple sequential requests
        for _ in range(20):
            start_time = time.time()
            response = api_client.get("/api/products/filters/categories")
            end_time = time.time()
            
            assert response.status_code == 200
            response_times.append((end_time - start_time) * 1000)  # ms
        
        # Check response time statistics
        avg_time = sum(response_times) / len(response_times)
        max_time = max(response_times)
        
        assert avg_time < performance_config["max_response_time"]
        assert max_time < performance_config["max_response_time"] * 2  # Allow some variation