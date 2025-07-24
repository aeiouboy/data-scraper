"""Integration tests for scraping API endpoints."""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime
from src.api.main import app
# TODO: Update for Supabase - from src.api.database import get_db
from tests.mock_scraper_manager import ScraperManager
from tests.fixtures.database import override_get_db, test_session


class TestScrapingAPI:
    """Test scraping API endpoints."""
    
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
    def mock_scraper_manager(self):
        """Mock scraper manager."""
        with patch('src.api.routers.scraping.scraper_manager') as mock:
            mock.scrape_retailer = AsyncMock()
            mock.scrape_product = AsyncMock()
            mock.get_supported_retailers = Mock(return_value=[
                "homepro", "megahome", "thaiwatsadu", "boonthavorn"
            ])
            yield mock
    
    @pytest.mark.asyncio
    async def test_start_scraping_job(self, client, mock_scraper_manager):
        """Test starting a scraping job."""
        response = client.post("/api/v1/scraping/start", json={
            "retailer": "homepro",
            "job_type": "category",
            "category": "tools"
        })
        
        assert response.status_code == 200
        data = response.json()
        assert "job_id" in data
        assert data["status"] == "started"
        assert data["retailer"] == "homepro"
        assert data["job_type"] == "category"
    
    @pytest.mark.asyncio
    async def test_start_scraping_invalid_retailer(self, client, mock_scraper_manager):
        """Test starting scraping with invalid retailer."""
        response = client.post("/api/v1/scraping/start", json={
            "retailer": "invalid_retailer",
            "job_type": "full"
        })
        
        assert response.status_code == 400
        assert "Unsupported retailer" in response.json()["detail"]
    
    @pytest.mark.asyncio
    async def test_get_scraping_status(self, client, test_session):
        """Test getting scraping job status."""
        # Create a test job
        from tests.models_mock import ScrapingJob
        job = ScrapingJob(
            retailer_code="homepro",
            job_type="category",
            status="running",
            started_at=datetime.utcnow(),
            total_products=100,
            successful_products=50,
            failed_products=5
        )
        test_session.add(job)
        test_session.commit()
        
        response = client.get(f"/api/v1/scraping/status/{job.id}")
        assert response.status_code == 200
        
        status = response.json()
        assert status["id"] == job.id
        assert status["retailer_code"] == "homepro"
        assert status["status"] == "running"
        assert status["progress"]["total"] == 100
        assert status["progress"]["successful"] == 50
        assert status["progress"]["failed"] == 5
    
    @pytest.mark.asyncio
    async def test_get_nonexistent_job_status(self, client):
        """Test getting status of nonexistent job."""
        response = client.get("/api/v1/scraping/status/99999")
        assert response.status_code == 404
    
    @pytest.mark.asyncio
    async def test_list_scraping_jobs(self, client, test_session):
        """Test listing scraping jobs."""
        # Create test jobs
        from tests.models_mock import ScrapingJob
        from datetime import timedelta
        
        for i in range(5):
            job = ScrapingJob(
                retailer_code=["homepro", "megahome"][i % 2],
                job_type=["full", "category", "update"][i % 3],
                status=["completed", "failed", "running"][i % 3],
                started_at=datetime.utcnow() - timedelta(hours=i),
                total_products=100 * (i + 1)
            )
            test_session.add(job)
        test_session.commit()
        
        response = client.get("/api/v1/scraping/jobs")
        assert response.status_code == 200
        
        data = response.json()
        assert len(data["jobs"]) == 5
        assert data["total"] == 5
    
    @pytest.mark.asyncio
    async def test_list_jobs_with_filters(self, client, test_session):
        """Test listing jobs with filters."""
        # Create test jobs
        from tests.models_mock import ScrapingJob
        
        job1 = ScrapingJob(
            retailer_code="homepro",
            job_type="full",
            status="completed",
            started_at=datetime.utcnow()
        )
        job2 = ScrapingJob(
            retailer_code="megahome",
            job_type="category",
            status="running",
            started_at=datetime.utcnow()
        )
        test_session.add_all([job1, job2])
        test_session.commit()
        
        # Filter by retailer
        response = client.get("/api/v1/scraping/jobs?retailer=homepro")
        assert response.status_code == 200
        data = response.json()
        assert all(j["retailer_code"] == "homepro" for j in data["jobs"])
        
        # Filter by status
        response = client.get("/api/v1/scraping/jobs?status=running")
        assert response.status_code == 200
        data = response.json()
        assert all(j["status"] == "running" for j in data["jobs"])
    
    @pytest.mark.asyncio
    async def test_cancel_scraping_job(self, client, test_session):
        """Test cancelling a scraping job."""
        # Create a running job
        from tests.models_mock import ScrapingJob
        job = ScrapingJob(
            retailer_code="homepro",
            job_type="full",
            status="running",
            started_at=datetime.utcnow()
        )
        test_session.add(job)
        test_session.commit()
        
        response = client.post(f"/api/v1/scraping/cancel/{job.id}")
        assert response.status_code == 200
        
        # Check job was cancelled
        test_session.refresh(job)
        assert job.status == "cancelled"
    
    @pytest.mark.asyncio
    async def test_scrape_single_product(self, client, mock_scraper_manager):
        """Test scraping a single product."""
        mock_product = {
            "retailer_code": "homepro",
            "sku": "12345",
            "name": "Test Product",
            "current_price": 1000.0,
            "product_url": "https://homepro.co.th/p/12345"
        }
        mock_scraper_manager.scrape_product.return_value = mock_product
        
        response = client.post("/api/v1/scraping/product", json={
            "url": "https://homepro.co.th/p/12345"
        })
        
        assert response.status_code == 200
        product = response.json()
        assert product["name"] == "Test Product"
        assert product["current_price"] == 1000.0
    
    @pytest.mark.asyncio
    async def test_get_scraping_stats(self, client, test_session):
        """Test getting scraping statistics."""
        # Create test jobs
        from tests.models_mock import ScrapingJob
        from datetime import timedelta
        
        for i in range(10):
            job = ScrapingJob(
                retailer_code=["homepro", "megahome"][i % 2],
                job_type="full",
                status="completed" if i < 8 else "failed",
                started_at=datetime.utcnow() - timedelta(days=i),
                completed_at=datetime.utcnow() - timedelta(days=i) + timedelta(hours=1),
                total_products=1000,
                successful_products=900 if i < 8 else 100,
                failed_products=100 if i < 8 else 900
            )
            test_session.add(job)
        test_session.commit()
        
        response = client.get("/api/v1/scraping/stats")
        assert response.status_code == 200
        
        stats = response.json()
        assert "total_jobs" in stats
        assert "jobs_by_status" in stats
        assert "jobs_by_retailer" in stats
        assert "success_rate" in stats
        assert "average_duration" in stats
        assert "products_scraped" in stats
    
    @pytest.mark.asyncio
    async def test_retry_failed_jobs(self, client, test_session):
        """Test retrying failed jobs."""
        # Create failed jobs
        from tests.models_mock import ScrapingJob
        
        failed_jobs = []
        for i in range(3):
            job = ScrapingJob(
                retailer_code="homepro",
                job_type="category",
                status="failed",
                started_at=datetime.utcnow(),
                completed_at=datetime.utcnow(),
                total_products=100,
                failed_products=100
            )
            test_session.add(job)
            failed_jobs.append(job)
        test_session.commit()
        
        response = client.post("/api/v1/scraping/retry-failed")
        assert response.status_code == 200
        
        data = response.json()
        assert data["retried_count"] == 3
        assert len(data["new_job_ids"]) == 3
    
    @pytest.mark.asyncio
    async def test_get_supported_retailers(self, client, mock_scraper_manager):
        """Test getting supported retailers."""
        response = client.get("/api/v1/scraping/retailers")
        assert response.status_code == 200
        
        retailers = response.json()
        assert "homepro" in retailers
        assert "megahome" in retailers
        assert "thaiwatsadu" in retailers
        assert "boonthavorn" in retailers
    
    @pytest.mark.asyncio
    async def test_schedule_scraping_job(self, client):
        """Test scheduling a scraping job."""
        response = client.post("/api/v1/scraping/schedule", json={
            "retailer": "homepro",
            "job_type": "update",
            "schedule_at": (datetime.utcnow() + timedelta(hours=1)).isoformat(),
            "recurrence": "daily"
        })
        
        assert response.status_code == 200
        data = response.json()
        assert "schedule_id" in data
        assert data["status"] == "scheduled"
    
    @pytest.mark.asyncio
    async def test_webhook_notifications(self, client, test_session):
        """Test webhook notifications for job completion."""
        # Create a completed job
        from tests.models_mock import ScrapingJob
        
        job = ScrapingJob(
            retailer_code="homepro",
            job_type="full",
            status="completed",
            started_at=datetime.utcnow(),
            completed_at=datetime.utcnow(),
            total_products=1000,
            successful_products=950,
            failed_products=50
        )
        test_session.add(job)
        test_session.commit()
        
        # Register webhook
        response = client.post("/api/v1/scraping/webhooks", json={
            "url": "https://example.com/webhook",
            "events": ["job.completed", "job.failed"]
        })
        assert response.status_code == 200
        
        webhook_data = response.json()
        assert "webhook_id" in webhook_data
        assert webhook_data["url"] == "https://example.com/webhook"