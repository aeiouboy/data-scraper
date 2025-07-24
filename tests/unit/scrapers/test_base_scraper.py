"""Unit tests for the base scraper functionality."""

import pytest
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime
import httpx
from bs4 import BeautifulSoup

from src.scrapers.base_scraper import BaseScraper
from src.models.product import Product


class TestBaseScraper:
    """Test the base scraper class."""
    
    @pytest.fixture
    def scraper(self):
        """Create a test scraper instance."""
        class TestScraper(BaseScraper):
            def __init__(self):
                super().__init__("test_retailer", "https://test.com")
            
            async def scrape_product(self, url: str) -> Product:
                return Product(
                    retailer_code=self.retailer_code,
                    sku="TEST123",
                    name="Test Product",
                    current_price=100.0,
                    product_url=url
                )
            
            async def scrape_category(self, category_url: str, max_pages: int = 10):
                return [
                    Product(
                        retailer_code=self.retailer_code,
                        sku=f"TEST{i}",
                        name=f"Test Product {i}",
                        current_price=100.0 * i,
                        product_url=f"https://test.com/product/{i}"
                    )
                    for i in range(3)
                ]
        
        return TestScraper()
    
    @pytest.mark.asyncio
    async def test_initialization(self, scraper):
        """Test scraper initialization."""
        assert scraper.retailer_code == "test_retailer"
        assert scraper.base_url == "https://test.com"
        assert scraper.session is None
    
    @pytest.mark.asyncio
    async def test_session_management(self, scraper):
        """Test HTTP session creation and cleanup."""
        # Session should be created on first access
        session = await scraper.get_session()
        assert isinstance(session, httpx.AsyncClient)
        assert scraper.session is not None
        
        # Same session should be returned
        session2 = await scraper.get_session()
        assert session is session2
        
        # Cleanup
        await scraper.close()
        assert scraper.session is None
    
    @pytest.mark.asyncio
    async def test_parse_price(self, scraper):
        """Test price parsing functionality."""
        # Test various price formats
        assert scraper.parse_price("฿1,299") == 1299.0
        assert scraper.parse_price("1,299 บาท") == 1299.0
        assert scraper.parse_price("THB 1,299.50") == 1299.50
        assert scraper.parse_price("฿1,299.-") == 1299.0
        assert scraper.parse_price("1299") == 1299.0
        assert scraper.parse_price("invalid") == 0.0
        assert scraper.parse_price("") == 0.0
        assert scraper.parse_price(None) == 0.0
    
    @pytest.mark.asyncio
    async def test_extract_text(self, scraper):
        """Test text extraction from BeautifulSoup elements."""
        html = "<div>  Test Text  </div>"
        soup = BeautifulSoup(html, 'html.parser')
        element = soup.find('div')
        
        assert scraper.extract_text(element) == "Test Text"
        assert scraper.extract_text(element, 'default') == "Test Text"
        assert scraper.extract_text(None) == ""
        assert scraper.extract_text(None, 'default') == "default"
    
    @pytest.mark.asyncio
    async def test_validate_url(self, scraper):
        """Test URL validation."""
        assert scraper.validate_url("https://test.com/product/123")
        assert scraper.validate_url("http://test.com/product/123")
        assert not scraper.validate_url("invalid-url")
        assert not scraper.validate_url("")
        assert not scraper.validate_url(None)
        assert not scraper.validate_url("javascript:void(0)")
    
    @pytest.mark.asyncio
    async def test_build_absolute_url(self, scraper):
        """Test absolute URL building."""
        assert scraper.build_absolute_url("/product/123") == "https://test.com/product/123"
        assert scraper.build_absolute_url("product/123") == "https://test.com/product/123"
        assert scraper.build_absolute_url("https://test.com/product/123") == "https://test.com/product/123"
        assert scraper.build_absolute_url("http://other.com/product") == "http://other.com/product"
    
    @pytest.mark.asyncio
    async def test_rate_limiting(self, scraper):
        """Test rate limiting functionality."""
        scraper.rate_limiter = Mock()
        scraper.rate_limiter.acquire = AsyncMock()
        
        session = Mock()
        session.get = AsyncMock(return_value=Mock(status_code=200, text="<html></html>"))
        
        with patch.object(scraper, 'get_session', return_value=session):
            await scraper.fetch_page("https://test.com/page")
            scraper.rate_limiter.acquire.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_fetch_page_success(self, scraper):
        """Test successful page fetching."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = "<html><body>Test Content</body></html>"
        
        session = Mock()
        session.get = AsyncMock(return_value=mock_response)
        
        with patch.object(scraper, 'get_session', return_value=session):
            content = await scraper.fetch_page("https://test.com/page")
            assert content == mock_response.text
            session.get.assert_called_once_with("https://test.com/page")
    
    @pytest.mark.asyncio
    async def test_fetch_page_retry(self, scraper):
        """Test page fetching with retries."""
        # First two attempts fail, third succeeds
        responses = [
            httpx.RequestError("Connection failed"),
            httpx.HTTPStatusError("Server error", request=Mock(), response=Mock(status_code=500)),
            Mock(status_code=200, text="Success")
        ]
        
        session = Mock()
        session.get = AsyncMock(side_effect=responses)
        
        with patch.object(scraper, 'get_session', return_value=session):
            content = await scraper.fetch_page("https://test.com/page", max_retries=3)
            assert content == "Success"
            assert session.get.call_count == 3
    
    @pytest.mark.asyncio
    async def test_clean_text(self, scraper):
        """Test text cleaning functionality."""
        assert scraper.clean_text("  Multiple   Spaces  ") == "Multiple Spaces"
        assert scraper.clean_text("Line1\nLine2\rLine3") == "Line1 Line2 Line3"
        assert scraper.clean_text("\t\tTabbed\t\t") == "Tabbed"
        assert scraper.clean_text("") == ""
        assert scraper.clean_text(None) == ""
    
    @pytest.mark.asyncio
    async def test_extract_specifications(self, scraper):
        """Test specification extraction."""
        html = """
        <table class="specs">
            <tr><td>Power</td><td>600W</td></tr>
            <tr><td>Voltage</td><td>220V</td></tr>
            <tr><td>Weight</td><td>2.5kg</td></tr>
        </table>
        """
        soup = BeautifulSoup(html, 'html.parser')
        
        # Default implementation returns empty dict
        specs = scraper.extract_specifications(soup)
        assert specs == {}
    
    @pytest.mark.asyncio
    async def test_error_handling(self, scraper):
        """Test error handling in fetch_page."""
        session = Mock()
        session.get = AsyncMock(side_effect=Exception("Unexpected error"))
        
        with patch.object(scraper, 'get_session', return_value=session):
            content = await scraper.fetch_page("https://test.com/page", max_retries=1)
            assert content is None
    
    @pytest.mark.asyncio
    async def test_context_manager(self, scraper):
        """Test async context manager functionality."""
        async with scraper:
            # Session should be created
            session = await scraper.get_session()
            assert session is not None
        
        # Session should be closed after context
        assert scraper.session is None