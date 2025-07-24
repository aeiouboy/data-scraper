"""Scraper-related fixtures for testing."""

import pytest
from unittest.mock import Mock, AsyncMock, patch
from bs4 import BeautifulSoup
import httpx


@pytest.fixture
def mock_scraper_response():
    """Create a mock scraper response."""
    def _mock_response(html_content, status_code=200):
        response = Mock()
        response.status_code = status_code
        response.text = html_content
        response.content = html_content.encode('utf-8')
        return response
    return _mock_response


@pytest.fixture
def sample_product_html():
    """Sample HTML for a product page."""
    return """
    <div class="product">
        <h1 class="product-title">Test Product</h1>
        <div class="price">
            <span class="current-price">฿1,299</span>
            <span class="original-price">฿1,599</span>
        </div>
        <div class="brand">Brand Name</div>
        <div class="sku">SKU123456</div>
        <div class="stock in-stock">In Stock</div>
        <img src="https://example.com/product.jpg" alt="Product Image">
    </div>
    """


@pytest.fixture
def sample_category_html():
    """Sample HTML for a category page."""
    return """
    <div class="category-page">
        <div class="product-grid">
            <div class="product-item" data-product-id="1">
                <a href="/product/1" class="product-link">
                    <img src="https://example.com/product1.jpg" alt="Product 1">
                    <h3>Product 1</h3>
                    <div class="price">฿999</div>
                </a>
            </div>
            <div class="product-item" data-product-id="2">
                <a href="/product/2" class="product-link">
                    <img src="https://example.com/product2.jpg" alt="Product 2">
                    <h3>Product 2</h3>
                    <div class="price">฿1,499</div>
                </a>
            </div>
        </div>
        <div class="pagination">
            <a href="?page=2" class="next-page">Next</a>
        </div>
    </div>
    """


@pytest.fixture
def mock_httpx_client():
    """Create a mock httpx client."""
    client = AsyncMock()
    return client


@pytest.fixture
def mock_beautiful_soup():
    """Create a mock BeautifulSoup parser."""
    def _mock_soup(html_content):
        return BeautifulSoup(html_content, 'html.parser')
    return _mock_soup


@pytest.fixture
def mock_firecrawl_client():
    """Mock Firecrawl client for testing."""
    client = Mock()
    client.scrape = AsyncMock()
    client.scrape.return_value = {
        'success': True,
        'data': {
            'content': 'Scraped content',
            'metadata': {
                'title': 'Page Title',
                'description': 'Page Description'
            }
        }
    }
    return client


@pytest.fixture
def retailer_test_urls():
    """Common test URLs for different retailers."""
    return {
        'homepro': {
            'base': 'https://www.homepro.co.th',
            'category': 'https://www.homepro.co.th/c/power-tools',
            'product': 'https://www.homepro.co.th/p/1234567'
        },
        'megahome': {
            'base': 'https://www.megahome.co.th',
            'category': 'https://www.megahome.co.th/category/tools',
            'product': 'https://www.megahome.co.th/product/test-product'
        },
        'thaiwatsadu': {
            'base': 'https://www.thaiwatsadu.com',
            'category': 'https://www.thaiwatsadu.com/th/category/tools',
            'product': 'https://www.thaiwatsadu.com/th/product/12345'
        },
        'boonthavorn': {
            'base': 'https://www.boonthavorn.com',
            'category': 'https://www.boonthavorn.com/th/category/ceramic-tiles',
            'product': 'https://www.boonthavorn.com/th/product/tile-001'
        }
    }