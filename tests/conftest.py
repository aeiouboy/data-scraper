"""
Pytest configuration and shared fixtures
"""
import asyncio
import pytest
import pytest_asyncio
from unittest.mock import Mock, AsyncMock
from fastapi.testclient import TestClient
from typing import AsyncGenerator, Generator
import tempfile
import os
import sys
from pathlib import Path

# Add src to path for native scraping tests
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

# Configure asyncio for testing
pytest_asyncio.fixture_scope_function = True


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    policy = asyncio.get_event_loop_policy()
    loop = policy.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def mock_firecrawl_client():
    """Mock Firecrawl client for testing without external API calls"""
    client = Mock()
    client.__aenter__ = AsyncMock(return_value=client)
    client.__aexit__ = AsyncMock(return_value=None)
    
    # Mock scrape method
    client.scrape = AsyncMock(return_value={
        "metadata": {
            "title": "Test Product - HomePro",
            "description": "Test Product, TestBrand, SKU123"
        },
        "markdown": "# Test Product\n\n฿2,490 each ฿2,990\n\nมีคนซื้อไปแล้ว 50 ชิ้น",
        "html": "<html><title>Test Product</title></html>",
        "linksOnPage": [
            "https://www.homepro.co.th/p/1001234567",
            "https://www.homepro.co.th/p/1001234568"
        ]
    })
    
    # Mock batch_scrape method
    client.batch_scrape = AsyncMock(return_value=[
        {"metadata": {"title": "Product 1"}, "markdown": "# Product 1"},
        {"metadata": {"title": "Product 2"}, "markdown": "# Product 2"}
    ])
    
    # Mock crawl method
    client.crawl = AsyncMock(return_value=[
        "https://www.homepro.co.th/p/1001234567",
        "https://www.homepro.co.th/p/1001234568"
    ])
    
    return client


@pytest.fixture
def mock_supabase_service():
    """Mock Supabase service for testing without database calls"""
    service = Mock()
    
    # Mock product operations
    service.upsert_product = AsyncMock(return_value={
        "id": "test-uuid",
        "sku": "TEST123",
        "name": "Test Product",
        "current_price": 2490.00
    })
    
    service.get_product_by_id = AsyncMock(return_value={
        "id": "test-uuid",
        "sku": "TEST123", 
        "name": "Test Product",
        "url": "https://www.homepro.co.th/p/1001234567",
        "current_price": 2490.00,
        "created_at": "2025-06-27T12:00:00Z"
    })
    
    service.search_products = AsyncMock(return_value={
        "products": [],
        "total": 0
    })
    
    # Mock job operations
    service.create_scrape_job = AsyncMock(return_value={
        "id": "job-uuid",
        "status": "pending",
        "job_type": "product"
    })
    
    service.update_scrape_job = AsyncMock(return_value=True)
    service.get_scrape_job = AsyncMock(return_value={
        "id": "job-uuid",
        "status": "completed"
    })
    
    # Mock statistics
    service.get_product_stats = AsyncMock(return_value={
        "total_products": 100,
        "total_brands": 20,
        "avg_price": 1500.00
    })
    
    service.get_daily_scrape_stats = AsyncMock(return_value=[])
    
    # Mock filter operations
    service.get_all_brands = AsyncMock(return_value=["TestBrand", "AnotherBrand"])
    service.get_categories = AsyncMock(return_value=["Electronics", "Tools"])
    
    return service


@pytest.fixture
def test_product_data():
    """Sample product data for testing"""
    return {
        "sku": "HP-TEST123",
        "name": "Test Electric Drill",
        "brand": "TestBrand",
        "category": "Tools",
        "current_price": 2490.00,
        "original_price": 2990.00,
        "discount_percentage": 16.72,
        "description": "High-quality electric drill for home use",
        "features": ["Cordless", "18V Battery", "LED Light"],
        "specifications": {
            "voltage": "18V",
            "weight": "1.5kg",
            "warranty": "2 years"
        },
        "availability": "in_stock",
        "images": ["https://example.com/image1.jpg"],
        "url": "https://www.homepro.co.th/p/1001234567"
    }


@pytest.fixture
def test_raw_data():
    """Sample raw data from Firecrawl for testing"""
    return {
        "metadata": {
            "title": "เครื่องเจาะไฟฟ้า TestBrand 18V - HomePro",
            "description": "เครื่องเจาะไฟฟ้า, TestBrand, HP-TEST123"
        },
        "markdown": """# เครื่องเจาะไฟฟ้า TestBrand 18V

## รายละเอียดสินค้า
- แรงดันไฟ: 18V
- น้ำหนัก: 1.5kg
- รับประกัน: 2 ปี

## ราคา
฿2,490 each ฿2,990

มีคนซื้อไปแล้ว 15 ชิ้น

## คุณสมบัติ
- ไร้สาย
- แบตเตอรี่ 18V
- ไฟ LED
""",
        "html": "<html><head><title>เครื่องเจาะไฟฟ้า</title></head><body>...</body></html>",
        "linksOnPage": [
            "https://www.homepro.co.th/p/1001234567",
            "https://www.homepro.co.th/p/1001234568"
        ]
    }


@pytest.fixture
def temp_env_file():
    """Create temporary .env file for testing"""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.env', delete=False) as f:
        f.write("""
SUPABASE_URL=https://test.supabase.co
SUPABASE_ANON_KEY=test-anon-key
SUPABASE_SERVICE_ROLE_KEY=test-service-key
POSTGRES_URL=postgresql://test:test@localhost/test
POSTGRES_PASSWORD=test
FIRECRAWL_API_KEY=fc-test-key
ENVIRONMENT=test
LOG_LEVEL=debug
""")
        temp_path = f.name
    
    # Set environment variable
    original_env = os.environ.get('ENV_FILE')
    os.environ['ENV_FILE'] = temp_path
    
    yield temp_path
    
    # Cleanup
    os.unlink(temp_path)
    if original_env:
        os.environ['ENV_FILE'] = original_env
    else:
        os.environ.pop('ENV_FILE', None)


@pytest.fixture
def api_client(mock_supabase_service):
    """FastAPI test client with mocked dependencies"""
    from src.api.main import app
    from src.api.routers.products import get_supabase
    from src.api.routers.scraping import get_supabase as get_supabase_scraping
    from src.api.routers.analytics import get_supabase as get_supabase_analytics
    
    # Override dependencies
    app.dependency_overrides[get_supabase] = lambda: mock_supabase_service
    app.dependency_overrides[get_supabase_scraping] = lambda: mock_supabase_service
    app.dependency_overrides[get_supabase_analytics] = lambda: mock_supabase_service
    
    with TestClient(app) as client:
        yield client
    
    # Clean up overrides
    app.dependency_overrides.clear()


@pytest.fixture
def sample_urls():
    """Sample HomePro URLs for testing"""
    return [
        "https://www.homepro.co.th/p/1001234567",
        "https://www.homepro.co.th/p/1001234568", 
        "https://www.homepro.co.th/p/1001234569"
    ]


# Performance testing fixtures
@pytest.fixture
def performance_config():
    """Configuration for performance tests"""
    return {
        "max_response_time": 1000,  # milliseconds
        "max_memory_usage": 500,    # MB
        "concurrent_requests": 10
    }


# Security testing fixtures
@pytest.fixture
def malicious_inputs():
    """Common malicious inputs for security testing"""
    return {
        "sql_injection": [
            "'; DROP TABLE products; --",
            "1' OR '1'='1",
            "admin'/**/OR/**/1=1#"
        ],
        "xss": [
            "<script>alert('xss')</script>",
            "javascript:alert('xss')",
            "<img src=x onerror=alert('xss')>"
        ],
        "path_traversal": [
            "../../../etc/passwd",
            "..\\..\\..\\windows\\system32",
            "%2e%2e%2f%2e%2e%2f%2e%2e%2fetc%2fpasswd"
        ]
    }


# Native Scraping Test Fixtures
@pytest.fixture
def mock_retailer_config():
    """Mock retailer configuration for native scraping tests"""
    return {
        'name': 'Test Retailer',
        'code': 'TEST',
        'base_url': 'https://test-retailer.com',
        'rate_limit_delay': 0.1,
        'max_concurrent': 2,
        'retry_attempts': 2,
        'timeout': 5,
        'scraping_method': 'native',
        'primary_strategy': 'native',
        'fallback_strategy': 'firecrawl',
        'success_rate_threshold': 0.8,
        'response_time_threshold': 5.0,
        'fallback_after_failures': 2,
        'min_data_quality_score': 0.7,
        'category_urls': [
            'https://test-retailer.com/category/electronics',
            'https://test-retailer.com/category/tools'
        ],
        'product_url_patterns': ['/product/', '/p/'],
        'search_patterns': {
            'url_pattern': '/search?q={query}',
            'query_parameter': 'q'
        },
        'selectors': {
            'product_name': ['.product-title', 'h1.title'],
            'price': ['.price', '.cost'],
            'brand': ['.brand-name', '.manufacturer'],
            'sku': ['.sku', '.product-code'],
            'description': ['.description', '.product-info'],
            'images': ['.product-image img', '.gallery img'],
            'availability': ['.stock-status', '.availability'],
            'rating': ['.rating-score', '.product-rating'],
            'reviews_count': ['.review-count', '.reviews-total'],
            'product_links': ['.product-item a', '.product-card a'],
            'category_name': ['.category-title', '.page-title'],
            'pagination': ['.pagination a', '.page-nav a']
        }
    }


@pytest.fixture
def sample_product_html():
    """Sample HTML for product page testing"""
    return """
    <html>
        <head>
            <title>Test Product - Test Retailer</title>
            <meta name="description" content="A high-quality test product">
        </head>
        <body>
            <div class="product-container">
                <h1 class="product-title">High-Quality Test Product</h1>
                <div class="product-details">
                    <span class="brand-name">TestBrand</span>
                    <span class="sku">SKU-12345</span>
                    <div class="price">฿1,299.99</div>
                    <div class="description">
                        This is a comprehensive test product with multiple features.
                        Perfect for testing scraping functionality.
                    </div>
                    <div class="stock-status">In Stock</div>
                    <div class="rating-score">4.5 out of 5 stars</div>
                    <div class="review-count">123 reviews</div>
                </div>
                <div class="product-images">
                    <img src="/images/product1.jpg" alt="Product Image 1">
                    <img src="/images/product2.jpg" alt="Product Image 2">
                </div>
                <div class="specifications">
                    <table>
                        <tr><td>Weight</td><td>2.5 kg</td></tr>
                        <tr><td>Dimensions</td><td>30x20x15 cm</td></tr>
                        <tr><td>Material</td><td>High-grade plastic</td></tr>
                    </table>
                </div>
            </div>
        </body>
    </html>
    """


@pytest.fixture
def sample_category_html():
    """Sample HTML for category page testing"""
    return """
    <html>
        <head>
            <title>Electronics - Test Retailer</title>
        </head>
        <body>
            <div class="category-container">
                <h1 class="category-title">Electronics</h1>
                <div class="product-grid">
                    <div class="product-item">
                        <a href="/product/smartphone-123">
                            <img src="/images/smartphone.jpg" alt="Smartphone">
                            <h3>Test Smartphone</h3>
                            <span class="price">฿15,999</span>
                        </a>
                    </div>
                    <div class="product-item">
                        <a href="/product/laptop-456">
                            <img src="/images/laptop.jpg" alt="Laptop">
                            <h3>Test Laptop</h3>
                            <span class="price">฿25,999</span>
                        </a>
                    </div>
                    <div class="product-item">
                        <a href="/product/headphones-789">
                            <img src="/images/headphones.jpg" alt="Headphones">
                            <h3>Test Headphones</h3>
                            <span class="price">฿2,999</span>
                        </a>
                    </div>
                </div>
                <div class="pagination">
                    <a href="/category/electronics?page=1">1</a>
                    <a href="/category/electronics?page=2">2</a>
                    <a href="/category/electronics?page=3">3</a>
                    <a href="/category/electronics?page=2">Next</a>
                </div>
            </div>
        </body>
    </html>
    """


@pytest.fixture
def mock_aiohttp_session():
    """Mock aiohttp session for testing"""
    from aiohttp import ClientSession
    
    session = Mock(spec=ClientSession)
    
    # Mock response
    mock_response = Mock()
    mock_response.status = 200
    mock_response.text = AsyncMock(return_value="<html><body>Test content</body></html>")
    mock_response.headers = {'content-type': 'text/html'}
    
    # Mock context manager
    mock_context = AsyncMock()
    mock_context.__aenter__ = AsyncMock(return_value=mock_response)
    mock_context.__aexit__ = AsyncMock(return_value=None)
    
    session.get = Mock(return_value=mock_context)
    session.close = AsyncMock()
    session.closed = False
    
    return session


@pytest.fixture
def performance_thresholds():
    """Performance test thresholds"""
    return {
        'response_time': 5.0,  # seconds
        'success_rate': 0.95,   # 95%
        'concurrent_requests': 5,
        'requests_per_second': 2.0
    }


# Configure pytest markers for native scraping tests
def pytest_configure(config):
    """Configure pytest markers"""
    config.addinivalue_line(
        "markers", "unit: mark test as unit test"
    )
    config.addinivalue_line(
        "markers", "integration: mark test as integration test"
    )
    config.addinivalue_line(
        "markers", "e2e: mark test as end-to-end test"
    )
    config.addinivalue_line(
        "markers", "performance: mark test as performance test"
    )
    config.addinivalue_line(
        "markers", "slow: mark test as slow running"
    )
    config.addinivalue_line(
        "markers", "network: mark test as requiring network access"
    )
    config.addinivalue_line(
        "markers", "native: mark test as native scraping test"
    )