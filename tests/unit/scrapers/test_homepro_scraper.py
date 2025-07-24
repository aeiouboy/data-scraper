"""Unit tests for HomePro scraper."""

import pytest
from unittest.mock import Mock, AsyncMock, patch
from bs4 import BeautifulSoup
from datetime import datetime

from src.scrapers.homepro_scraper import HomeProScraper
from src.models.product import Product


class TestHomeProScraper:
    """Test HomePro scraper functionality."""
    
    @pytest.fixture
    def scraper(self):
        """Create a HomePro scraper instance."""
        return HomeProScraper()
    
    @pytest.fixture
    def sample_product_html(self):
        """Sample HomePro product page HTML."""
        return """
        <html>
            <body>
                <div class="product-detail">
                    <h1 class="product-name">Bosch Professional Drill GBM 13 RE</h1>
                    <div class="product-sku">SKU: 1234567</div>
                    <div class="product-brand">แบรนด์: BOSCH</div>
                    <div class="price-box">
                        <span class="special-price">฿2,990</span>
                        <span class="old-price">฿3,590</span>
                    </div>
                    <div class="product-category">
                        <a href="/c/tools">เครื่องมือ</a> > 
                        <a href="/c/power-tools">เครื่องมือไฟฟ้า</a> > 
                        <a href="/c/drills">สว่าน</a>
                    </div>
                    <div class="product-stock in-stock">มีสินค้า</div>
                    <img class="product-image" src="https://cdn.homepro.co.th/product/1234567.jpg" />
                    <div class="product-description">
                        <h3>รายละเอียดสินค้า</h3>
                        <ul>
                            <li>กำลังไฟ: 600 วัตต์</li>
                            <li>ความเร็ว: 0-2,800 รอบ/นาที</li>
                            <li>ขนาดหัวจับ: 13 มม.</li>
                        </ul>
                    </div>
                </div>
            </body>
        </html>
        """
    
    @pytest.fixture
    def sample_category_html(self):
        """Sample HomePro category page HTML."""
        return """
        <html>
            <body>
                <div class="product-list">
                    <div class="product-item" data-product-id="1234567">
                        <a href="/p/1234567" class="product-link">
                            <img src="https://cdn.homepro.co.th/thumb/1234567.jpg" />
                            <h3 class="product-name">Bosch Drill</h3>
                            <div class="price">฿2,990</div>
                        </a>
                    </div>
                    <div class="product-item" data-product-id="2345678">
                        <a href="/p/2345678" class="product-link">
                            <img src="https://cdn.homepro.co.th/thumb/2345678.jpg" />
                            <h3 class="product-name">Makita Drill</h3>
                            <div class="price">฿3,490</div>
                        </a>
                    </div>
                </div>
                <div class="pagination">
                    <a href="?page=2" class="next">หน้าถัดไป</a>
                </div>
            </body>
        </html>
        """
    
    @pytest.mark.asyncio
    async def test_scraper_initialization(self, scraper):
        """Test HomePro scraper initialization."""
        assert scraper.retailer_code == "homepro"
        assert scraper.base_url == "https://www.homepro.co.th"
    
    @pytest.mark.asyncio
    async def test_scrape_product_success(self, scraper, sample_product_html):
        """Test successful product scraping."""
        with patch.object(scraper, 'fetch_page', return_value=sample_product_html):
            product = await scraper.scrape_product("https://www.homepro.co.th/p/1234567")
            
            assert product is not None
            assert product.retailer_code == "homepro"
            assert product.sku == "1234567"
            assert product.name == "Bosch Professional Drill GBM 13 RE"
            assert product.brand == "BOSCH"
            assert product.current_price == 2990.0
            assert product.original_price == 3590.0
            assert product.category == "เครื่องมือ/เครื่องมือไฟฟ้า/สว่าน"
            assert product.in_stock is True
            assert product.is_promotion is True
            assert "https://cdn.homepro.co.th/product/1234567.jpg" in product.image_url
    
    @pytest.mark.asyncio
    async def test_scrape_product_no_promotion(self, scraper):
        """Test product scraping without promotion."""
        html = """
        <div class="product-detail">
            <h1 class="product-name">Test Product</h1>
            <div class="product-sku">SKU: 123</div>
            <div class="price-box">
                <span class="regular-price">฿1,000</span>
            </div>
        </div>
        """
        
        with patch.object(scraper, 'fetch_page', return_value=html):
            product = await scraper.scrape_product("https://www.homepro.co.th/p/123")
            
            assert product.current_price == 1000.0
            assert product.original_price == 1000.0
            assert product.is_promotion is False
    
    @pytest.mark.asyncio
    async def test_scrape_product_out_of_stock(self, scraper):
        """Test out of stock product."""
        html = """
        <div class="product-detail">
            <h1 class="product-name">Test Product</h1>
            <div class="product-sku">SKU: 123</div>
            <div class="price-box">
                <span class="regular-price">฿1,000</span>
            </div>
            <div class="product-stock out-of-stock">สินค้าหมด</div>
        </div>
        """
        
        with patch.object(scraper, 'fetch_page', return_value=html):
            product = await scraper.scrape_product("https://www.homepro.co.th/p/123")
            
            assert product.in_stock is False
    
    @pytest.mark.asyncio
    async def test_scrape_category_products(self, scraper, sample_category_html):
        """Test category product scraping."""
        with patch.object(scraper, 'fetch_page', return_value=sample_category_html):
            with patch.object(scraper, 'scrape_product', side_effect=[
                Product(
                    retailer_code="homepro",
                    sku="1234567",
                    name="Bosch Drill",
                    current_price=2990.0,
                    product_url="https://www.homepro.co.th/p/1234567"
                ),
                Product(
                    retailer_code="homepro",
                    sku="2345678",
                    name="Makita Drill",
                    current_price=3490.0,
                    product_url="https://www.homepro.co.th/p/2345678"
                )
            ]) as mock_scrape:
                products = await scraper.scrape_category("https://www.homepro.co.th/c/drills", max_pages=1)
                
                assert len(products) == 2
                assert mock_scrape.call_count == 2
                assert products[0].name == "Bosch Drill"
                assert products[1].name == "Makita Drill"
    
    @pytest.mark.asyncio
    async def test_extract_product_urls(self, scraper, sample_category_html):
        """Test product URL extraction from category page."""
        soup = BeautifulSoup(sample_category_html, 'html.parser')
        urls = scraper.extract_product_urls(soup)
        
        assert len(urls) == 2
        assert "https://www.homepro.co.th/p/1234567" in urls
        assert "https://www.homepro.co.th/p/2345678" in urls
    
    @pytest.mark.asyncio
    async def test_extract_specifications(self, scraper, sample_product_html):
        """Test specification extraction."""
        soup = BeautifulSoup(sample_product_html, 'html.parser')
        specs = scraper.extract_specifications(soup)
        
        assert "กำลังไฟ" in specs
        assert specs["กำลังไฟ"] == "600 วัตต์"
        assert "ความเร็ว" in specs
        assert specs["ความเร็ว"] == "0-2,800 รอบ/นาที"
        assert "ขนาดหัวจับ" in specs
        assert specs["ขนาดหัวจับ"] == "13 มม."
    
    @pytest.mark.asyncio
    async def test_get_next_page_url(self, scraper, sample_category_html):
        """Test next page URL extraction."""
        soup = BeautifulSoup(sample_category_html, 'html.parser')
        next_url = scraper.get_next_page_url(soup, "https://www.homepro.co.th/c/drills")
        
        assert next_url == "https://www.homepro.co.th/c/drills?page=2"
    
    @pytest.mark.asyncio
    async def test_scrape_product_error_handling(self, scraper):
        """Test error handling in product scraping."""
        with patch.object(scraper, 'fetch_page', return_value=None):
            product = await scraper.scrape_product("https://www.homepro.co.th/p/invalid")
            assert product is None
        
        with patch.object(scraper, 'fetch_page', return_value="<html>Invalid HTML</html>"):
            product = await scraper.scrape_product("https://www.homepro.co.th/p/invalid")
            assert product is None
    
    @pytest.mark.asyncio
    async def test_parse_price_formats(self, scraper):
        """Test various price formats specific to HomePro."""
        assert scraper.parse_price("฿2,990.-") == 2990.0
        assert scraper.parse_price("2,990 บาท") == 2990.0
        assert scraper.parse_price("ราคา 2,990") == 2990.0
        assert scraper.parse_price("THB2,990") == 2990.0
    
    @pytest.mark.asyncio
    async def test_scrape_all_categories(self, scraper):
        """Test scraping all categories."""
        categories = {
            "tools": "https://www.homepro.co.th/c/tools",
            "bathroom": "https://www.homepro.co.th/c/bathroom"
        }
        
        with patch.object(scraper, 'get_category_urls', return_value=categories):
            with patch.object(scraper, 'scrape_category', return_value=[]) as mock_scrape:
                await scraper.scrape_all_categories()
                
                assert mock_scrape.call_count == 2
                mock_scrape.assert_any_call("https://www.homepro.co.th/c/tools")
                mock_scrape.assert_any_call("https://www.homepro.co.th/c/bathroom")