"""
Unit tests for HomeProScraper class
"""
import pytest
from unittest.mock import Mock, AsyncMock, patch
from app.core.scraper import HomeProScraper


class TestHomeProScraper:
    """Test suite for HomeProScraper"""
    
    def setup_method(self):
        """Setup for each test method"""
        # Use patches to avoid real service calls
        with patch('app.core.scraper.FirecrawlClient'), \
             patch('app.core.scraper.SupabaseService'), \
             patch('app.core.scraper.DataProcessor'):
            self.scraper = HomeProScraper()
    
    @pytest.mark.asyncio
    async def test_scrape_single_product_success(self, mock_firecrawl_client, test_product_data):
        """Test successful single product scraping"""
        # Mock the scraper's dependencies
        self.scraper.firecrawl = mock_firecrawl_client
        self.scraper.supabase = Mock()
        self.scraper.processor = Mock()
        
        # Mock successful scraping flow
        self.scraper.processor.process_product_data.return_value = Mock(**test_product_data)
        self.scraper.processor.validate_product.return_value = True
        self.scraper.supabase.upsert_product = AsyncMock(return_value=test_product_data)
        
        # Mock firecrawl client context manager
        mock_client = AsyncMock()
        mock_client.scrape.return_value = {"metadata": {"title": "Test Product"}}
        mock_firecrawl_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_firecrawl_client.__aexit__ = AsyncMock(return_value=None)
        
        url = "https://www.homepro.co.th/p/1001234567"
        result = await self.scraper.scrape_single_product(url)
        
        assert result is not None
        assert result == test_product_data
        
        # Verify method calls
        mock_client.scrape.assert_called_once_with(url)
        self.scraper.processor.process_product_data.assert_called_once()
        self.scraper.processor.validate_product.assert_called_once()
        self.scraper.supabase.upsert_product.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_scrape_single_product_no_data(self, mock_firecrawl_client):
        """Test scraping when no data is returned"""
        self.scraper.firecrawl = mock_firecrawl_client
        
        # Mock no data returned
        mock_client = AsyncMock()
        mock_client.scrape.return_value = None
        mock_firecrawl_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_firecrawl_client.__aexit__ = AsyncMock(return_value=None)
        
        url = "https://www.homepro.co.th/p/1001234567"
        result = await self.scraper.scrape_single_product(url)
        
        assert result is None
    
    @pytest.mark.asyncio
    async def test_scrape_single_product_processing_failure(self, mock_firecrawl_client):
        """Test scraping when data processing fails"""
        self.scraper.firecrawl = mock_firecrawl_client
        self.scraper.processor = Mock()
        
        # Mock processing failure
        mock_client = AsyncMock()
        mock_client.scrape.return_value = {"metadata": {"title": "Test"}}
        mock_firecrawl_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_firecrawl_client.__aexit__ = AsyncMock(return_value=None)
        
        self.scraper.processor.process_product_data.return_value = None
        
        url = "https://www.homepro.co.th/p/1001234567"
        result = await self.scraper.scrape_single_product(url)
        
        assert result is None
    
    @pytest.mark.asyncio
    async def test_scrape_single_product_validation_failure(self, mock_firecrawl_client, test_product_data):
        """Test scraping when validation fails"""
        self.scraper.firecrawl = mock_firecrawl_client
        self.scraper.processor = Mock()
        
        # Mock validation failure
        mock_client = AsyncMock()
        mock_client.scrape.return_value = {"metadata": {"title": "Test"}}
        mock_firecrawl_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_firecrawl_client.__aexit__ = AsyncMock(return_value=None)
        
        product_mock = Mock(**test_product_data)
        self.scraper.processor.process_product_data.return_value = product_mock
        self.scraper.processor.validate_product.return_value = False
        
        url = "https://www.homepro.co.th/p/1001234567"
        result = await self.scraper.scrape_single_product(url)
        
        assert result is None
    
    @pytest.mark.asyncio
    async def test_discover_product_urls_success(self):
        """Test successful URL discovery"""
        with patch('app.core.scraper.URLDiscovery') as mock_discovery_class:
            mock_discovery = AsyncMock()
            mock_discovery.discover_from_category.return_value = [
                "https://www.homepro.co.th/p/1001234567",
                "https://www.homepro.co.th/p/1001234568"
            ]
            mock_discovery.close = AsyncMock()
            mock_discovery_class.return_value = mock_discovery
            
            url = "https://www.homepro.co.th/c/tools"
            result = await self.scraper.discover_product_urls(url, max_pages=2)
            
            assert len(result) == 2
            assert "https://www.homepro.co.th/p/1001234567" in result
            mock_discovery.discover_from_category.assert_called_once_with(url, 2)
            mock_discovery.close.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_discover_product_urls_failure(self):
        """Test URL discovery failure"""
        with patch('app.core.scraper.URLDiscovery') as mock_discovery_class:
            mock_discovery = AsyncMock()
            mock_discovery.discover_from_category.side_effect = Exception("Discovery failed")
            mock_discovery.close = AsyncMock()
            mock_discovery_class.return_value = mock_discovery
            
            url = "https://www.homepro.co.th/c/tools"
            result = await self.scraper.discover_product_urls(url)
            
            assert result == []
            mock_discovery.close.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_scrape_batch_success(self, mock_firecrawl_client, sample_urls):
        """Test successful batch scraping"""
        self.scraper.firecrawl = mock_firecrawl_client
        self.scraper.supabase = Mock()
        self.scraper.processor = Mock()
        
        # Mock job creation and updates
        job_data = {"id": "test-job-id", "status": "pending"}
        self.scraper.supabase.create_scrape_job = AsyncMock(return_value=job_data)
        self.scraper.supabase.update_scrape_job = AsyncMock(return_value=True)
        
        # Mock firecrawl client
        mock_client = AsyncMock()
        mock_client.batch_scrape.return_value = [
            {"metadata": {"title": "Product 1"}},
            {"metadata": {"title": "Product 2"}},
            {"metadata": {"title": "Product 3"}}
        ]
        mock_firecrawl_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_firecrawl_client.__aexit__ = AsyncMock(return_value=None)
        
        # Mock processing and validation
        self.scraper.processor.process_product_data.return_value = Mock()
        self.scraper.processor.validate_product.return_value = True
        self.scraper.supabase.upsert_product = AsyncMock(return_value={"id": "product-id"})
        
        result = await self.scraper.scrape_batch(sample_urls, max_concurrent=2)
        
        assert "job_id" in result
        assert result["total"] == 3
        assert result["success"] == 3
        assert result["failed"] == 0
    
    @pytest.mark.asyncio
    async def test_scrape_batch_job_creation_failure(self, sample_urls):
        """Test batch scraping when job creation fails"""
        self.scraper.supabase = Mock()
        self.scraper.supabase.create_scrape_job = AsyncMock(return_value=None)
        
        result = await self.scraper.scrape_batch(sample_urls)
        
        assert result["success"] == 0
        assert result["failed"] == len(sample_urls)
    
    @pytest.mark.asyncio
    async def test_scrape_category_success(self, sample_urls):
        """Test successful category scraping"""
        with patch.object(self.scraper, 'discover_product_urls') as mock_discover, \
             patch.object(self.scraper, 'scrape_batch') as mock_batch:
            
            mock_discover.return_value = sample_urls
            mock_batch.return_value = {
                "job_id": "test-job",
                "total": 3,
                "success": 2,
                "failed": 1,
                "success_rate": 66.7
            }
            
            category_url = "https://www.homepro.co.th/c/tools"
            result = await self.scraper.scrape_category(category_url, max_pages=5)
            
            assert "category_url" in result
            assert result["category_url"] == category_url
            assert result["discovered"] == 3
            assert result["success"] == 2
            
            mock_discover.assert_called_once_with(category_url, 5)
            mock_batch.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_scrape_category_no_urls(self):
        """Test category scraping when no URLs are discovered"""
        with patch.object(self.scraper, 'discover_product_urls') as mock_discover:
            mock_discover.return_value = []
            
            category_url = "https://www.homepro.co.th/c/tools"
            result = await self.scraper.scrape_category(category_url)
            
            assert result["discovered"] == 0
            assert result["success"] == 0
            assert result["failed"] == 0
    
    @pytest.mark.asyncio
    async def test_get_scraping_stats(self):
        """Test getting scraping statistics"""
        self.scraper.supabase = Mock()
        
        mock_stats = {"total_products": 100, "total_brands": 20}
        mock_jobs = [{"date": "2025-06-27", "success_rate": 95.0}]
        
        self.scraper.supabase.get_product_stats = AsyncMock(return_value=mock_stats)
        self.scraper.supabase.get_daily_scrape_stats = AsyncMock(return_value=mock_jobs)
        
        result = await self.scraper.get_scraping_stats()
        
        assert "products" in result
        assert "recent_activity" in result
        assert result["products"] == mock_stats
        assert result["recent_activity"] == mock_jobs