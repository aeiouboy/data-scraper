"""Unit tests for Thai Watsadu scraper."""

import pytest
from unittest.mock import Mock, AsyncMock, patch
from bs4 import BeautifulSoup
import json

from src.scrapers.thaiwatsadu_scraper import ThaiWatsaduScraper
from src.models.product import Product


class TestThaiWatsaduScraper:
    """Test Thai Watsadu scraper functionality."""
    
    @pytest.fixture
    def scraper(self):
        """Create a Thai Watsadu scraper instance."""
        return ThaiWatsaduScraper()
    
    @pytest.fixture
    def sample_product_html(self):
        """Sample Thai Watsadu product page HTML."""
        return """
        <html>
            <body>
                <div class="product-detail-main">
                    <h1 class="product-name">ค้อนช่าง STANLEY 16 oz ด้ามไฟเบอร์กลาส</h1>
                    <div class="product-sku">รหัสสินค้า: TWD123456</div>
                    <div class="product-brand">ยี่ห้อ: STANLEY</div>
                    <div class="product-price">
                        <span class="price-now">299</span>
                        <span class="price-was">399</span>
                        <span class="price-unit">บาท</span>
                    </div>
                    <div class="breadcrumb">
                        <a href="/th/category/tools">เครื่องมือช่าง</a>
                        <span>/</span>
                        <a href="/th/category/hand-tools">เครื่องมือทั่วไป</a>
                        <span>/</span>
                        <a href="/th/category/hammers">ค้อน</a>
                    </div>
                    <div class="stock-status available">มีสินค้า</div>
                    <img class="product-image" src="https://www.thaiwatsadu.com/images/product/TWD123456.jpg" />
                    <div class="product-spec">
                        <table>
                            <tr><td>น้ำหนักหัวค้อน</td><td>16 ออนซ์</td></tr>
                            <tr><td>วัสดุด้ามจับ</td><td>ไฟเบอร์กลาส</td></tr>
                            <tr><td>ความยาว</td><td>33 ซม.</td></tr>
                        </table>
                    </div>
                </div>
                
                <!-- JSON-LD structured data -->
                <script type="application/ld+json">
                {
                    "@type": "Product",
                    "name": "ค้อนช่าง STANLEY 16 oz",
                    "sku": "TWD123456",
                    "brand": {
                        "@type": "Brand",
                        "name": "STANLEY"
                    },
                    "offers": {
                        "@type": "Offer",
                        "price": "299",
                        "priceCurrency": "THB",
                        "availability": "InStock"
                    }
                }
                </script>
            </body>
        </html>
        """
    
    @pytest.fixture
    def sample_category_api_response(self):
        """Sample API response for category listing."""
        return {
            "products": [
                {
                    "id": "TWD123456",
                    "name": "ค้อนช่าง STANLEY 16 oz",
                    "price": 299,
                    "originalPrice": 399,
                    "brand": "STANLEY",
                    "url": "/th/product/TWD123456",
                    "imageUrl": "https://www.thaiwatsadu.com/images/product/TWD123456.jpg",
                    "inStock": True
                },
                {
                    "id": "TWD234567",
                    "name": "สว่านไฟฟ้า BOSCH GBM 13 RE",
                    "price": 2990,
                    "originalPrice": 3590,
                    "brand": "BOSCH",
                    "url": "/th/product/TWD234567",
                    "imageUrl": "https://www.thaiwatsadu.com/images/product/TWD234567.jpg",
                    "inStock": True
                }
            ],
            "pagination": {
                "currentPage": 1,
                "totalPages": 5,
                "totalProducts": 98
            }
        }
    
    @pytest.mark.asyncio
    async def test_scraper_initialization(self, scraper):
        """Test Thai Watsadu scraper initialization."""
        assert scraper.retailer_code == "thaiwatsadu"
        assert scraper.base_url == "https://www.thaiwatsadu.com"
    
    @pytest.mark.asyncio
    async def test_scrape_product_from_html(self, scraper, sample_product_html):
        """Test product scraping from HTML."""
        with patch.object(scraper, 'fetch_page', return_value=sample_product_html):
            product = await scraper.scrape_product("https://www.thaiwatsadu.com/th/product/TWD123456")
            
            assert product is not None
            assert product.retailer_code == "thaiwatsadu"
            assert product.sku == "TWD123456"
            assert product.name == "ค้อนช่าง STANLEY 16 oz ด้ามไฟเบอร์กลาส"
            assert product.brand == "STANLEY"
            assert product.current_price == 299.0
            assert product.original_price == 399.0
            assert product.category == "เครื่องมือช่าง/เครื่องมือทั่วไป/ค้อน"
            assert product.in_stock is True
            assert product.is_promotion is True
    
    @pytest.mark.asyncio
    async def test_scrape_product_from_json_ld(self, scraper, sample_product_html):
        """Test product data extraction from JSON-LD."""
        soup = BeautifulSoup(sample_product_html, 'html.parser')
        json_ld_data = scraper.extract_json_ld_data(soup)
        
        assert json_ld_data is not None
        assert json_ld_data.get("name") == "ค้อนช่าง STANLEY 16 oz"
        assert json_ld_data.get("sku") == "TWD123456"
        assert json_ld_data.get("brand", {}).get("name") == "STANLEY"
        assert json_ld_data.get("offers", {}).get("price") == "299"
    
    @pytest.mark.asyncio
    async def test_scrape_category_via_api(self, scraper, sample_category_api_response):
        """Test category scraping via API."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json = Mock(return_value=sample_category_api_response)
        
        with patch.object(scraper, 'get_session') as mock_session:
            mock_session.return_value.post = AsyncMock(return_value=mock_response)
            
            products = await scraper.scrape_category_via_api("tools", max_pages=1)
            
            assert len(products) == 2
            assert products[0].sku == "TWD123456"
            assert products[0].name == "ค้อนช่าง STANLEY 16 oz"
            assert products[1].sku == "TWD234567"
            assert products[1].name == "สว่านไฟฟ้า BOSCH GBM 13 RE"
    
    @pytest.mark.asyncio
    async def test_extract_specifications(self, scraper, sample_product_html):
        """Test specification extraction."""
        soup = BeautifulSoup(sample_product_html, 'html.parser')
        specs = scraper.extract_specifications(soup)
        
        assert "น้ำหนักหัวค้อน" in specs
        assert specs["น้ำหนักหัวค้อน"] == "16 ออนซ์"
        assert "วัสดุด้ามจับ" in specs
        assert specs["วัสดุด้ามจับ"] == "ไฟเบอร์กลาส"
        assert "ความยาว" in specs
        assert specs["ความยาว"] == "33 ซม."
    
    @pytest.mark.asyncio
    async def test_parse_category_from_breadcrumb(self, scraper, sample_product_html):
        """Test category parsing from breadcrumb."""
        soup = BeautifulSoup(sample_product_html, 'html.parser')
        breadcrumb = soup.find('div', class_='breadcrumb')
        category = scraper.parse_category_from_breadcrumb(breadcrumb)
        
        assert category == "เครื่องมือช่าง/เครื่องมือทั่วไป/ค้อน"
    
    @pytest.mark.asyncio
    async def test_scrape_product_out_of_stock(self, scraper):
        """Test out of stock product detection."""
        html = """
        <div class="product-detail-main">
            <h1 class="product-name">Test Product</h1>
            <div class="product-sku">รหัสสินค้า: TWD999</div>
            <div class="product-price">
                <span class="price-now">100</span>
            </div>
            <div class="stock-status out-of-stock">สินค้าหมด</div>
        </div>
        """
        
        with patch.object(scraper, 'fetch_page', return_value=html):
            product = await scraper.scrape_product("https://www.thaiwatsadu.com/th/product/TWD999")
            
            assert product.in_stock is False
    
    @pytest.mark.asyncio
    async def test_handle_api_error(self, scraper):
        """Test API error handling."""
        mock_response = Mock()
        mock_response.status_code = 500
        mock_response.raise_for_status.side_effect = Exception("Server error")
        
        with patch.object(scraper, 'get_session') as mock_session:
            mock_session.return_value.post = AsyncMock(return_value=mock_response)
            
            products = await scraper.scrape_category_via_api("tools")
            assert products == []
    
    @pytest.mark.asyncio
    async def test_parse_price_thai_format(self, scraper):
        """Test Thai price format parsing."""
        assert scraper.parse_price("299 บาท") == 299.0
        assert scraper.parse_price("฿ 1,299") == 1299.0
        assert scraper.parse_price("ราคา 2,990.-") == 2990.0
        assert scraper.parse_price("THB 3,590") == 3590.0
    
    @pytest.mark.asyncio
    async def test_category_mapping(self, scraper):
        """Test category ID mapping."""
        categories = scraper.get_category_urls()
        
        assert "tools" in categories
        assert "paint" in categories
        assert "tiles" in categories
        assert "bathroom" in categories
        
        # Check URL format
        for cat_id, url in categories.items():
            assert url.startswith(scraper.base_url)
            assert f"/category/{cat_id}" in url
    
    @pytest.mark.asyncio
    async def test_product_url_validation(self, scraper):
        """Test product URL pattern validation."""
        valid_urls = [
            "https://www.thaiwatsadu.com/th/product/TWD123456",
            "https://www.thaiwatsadu.com/en/product/ABC789",
            "/th/product/XYZ123"
        ]
        
        invalid_urls = [
            "https://www.thaiwatsadu.com/category/tools",
            "https://other-site.com/product/123",
            "/invalid/path"
        ]
        
        for url in valid_urls:
            assert scraper.is_product_url(url) is True
        
        for url in invalid_urls:
            assert scraper.is_product_url(url) is False