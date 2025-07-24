"""
Unit tests for HTML parser
"""
import pytest
from bs4 import BeautifulSoup
from scrapers.engines.html_parser import HTMLParser


@pytest.mark.unit
@pytest.mark.native
class TestHTMLParser:
    """Test cases for HTML parser functionality"""
    
    def test_extract_text_by_selectors_css(self):
        """Test text extraction using CSS selectors"""
        parser = HTMLParser()
        html = """
        <html>
            <body>
                <h1 class="title">Test Product</h1>
                <div class="description">Product description</div>
            </body>
        </html>
        """
        soup = BeautifulSoup(html, 'html.parser')
        
        # Test single selector
        selectors = ['h1.title']
        result = parser.extract_text_by_selectors(soup, selectors)
        assert result == "Test Product"
        
        # Test multiple selectors with fallback
        selectors = ['h1.nonexistent', 'h1.title']
        result = parser.extract_text_by_selectors(soup, selectors)
        assert result == "Test Product"
        
        # Test no match
        selectors = ['h1.nonexistent']
        result = parser.extract_text_by_selectors(soup, selectors)
        assert result is None
    
    def test_extract_text_by_selectors_regex(self):
        """Test text extraction using regex selectors"""
        parser = HTMLParser()
        html = """
        <html>
            <body>
                <div>Price: ฿1,299.99</div>
                <div>SKU: ABC-123</div>
            </body>
        </html>
        """
        soup = BeautifulSoup(html, 'html.parser')
        
        # Test regex selector
        selectors = ['regex:Price:\\s*฿([0-9,]+(?:\\.[0-9]+)?)']
        result = parser.extract_text_by_selectors(soup, selectors)
        assert result == "1,299.99"
        
        # Test regex with no match
        selectors = ['regex:NotFound:\\s*([0-9]+)']
        result = parser.extract_text_by_selectors(soup, selectors)
        assert result is None
    
    def test_extract_text_list(self):
        """Test extracting list of texts"""
        parser = HTMLParser()
        html = """
        <html>
            <body>
                <ul>
                    <li class="item">Item 1</li>
                    <li class="item">Item 2</li>
                    <li class="item">Item 3</li>
                </ul>
            </body>
        </html>
        """
        soup = BeautifulSoup(html, 'html.parser')
        
        selectors = ['li.item']
        result = parser.extract_text_list(soup, selectors)
        assert result == ["Item 1", "Item 2", "Item 3"]
    
    def test_extract_links(self):
        """Test extracting links"""
        parser = HTMLParser()
        html = """
        <html>
            <body>
                <a href="/product/1">Product 1</a>
                <a href="/product/2">Product 2</a>
                <a href="https://external.com">External</a>
            </body>
        </html>
        """
        soup = BeautifulSoup(html, 'html.parser')
        base_url = "https://example.com"
        
        selectors = ['a']
        result = parser.extract_links(soup, selectors, base_url)
        assert len(result) == 3
        assert "https://example.com/product/1" in result
        assert "https://example.com/product/2" in result
        assert "https://external.com" in result
    
    def test_extract_images(self):
        """Test extracting image URLs"""
        parser = HTMLParser()
        html = """
        <html>
            <body>
                <img src="/images/product1.jpg" alt="Product 1">
                <img data-src="/images/product2.jpg" alt="Product 2">
                <img src="https://cdn.example.com/image.jpg" alt="CDN Image">
            </body>
        </html>
        """
        soup = BeautifulSoup(html, 'html.parser')
        base_url = "https://example.com"
        
        selectors = ['img']
        result = parser.extract_images(soup, selectors, base_url)
        assert len(result) >= 2
        assert "https://example.com/images/product1.jpg" in result
        assert "https://example.com/images/product2.jpg" in result
    
    def test_extract_specifications(self):
        """Test extracting specifications"""
        parser = HTMLParser()
        html = """
        <html>
            <body>
                <table class="specs">
                    <tr><td>Weight</td><td>2.5 kg</td></tr>
                    <tr><td>Dimensions</td><td>30x20x15 cm</td></tr>
                    <tr><td>Material</td><td>Plastic</td></tr>
                </table>
            </body>
        </html>
        """
        soup = BeautifulSoup(html, 'html.parser')
        
        selectors = ['table.specs']
        result = parser.extract_specifications(soup, selectors)
        assert "Weight" in result
        assert result["Weight"] == "2.5 kg"
        assert "Dimensions" in result
        assert result["Dimensions"] == "30x20x15 cm"
    
    def test_parse_price(self):
        """Test price parsing"""
        parser = HTMLParser()
        
        # Test various price formats
        test_cases = [
            ("฿1,299.99", 1299.99),
            ("฿1,299", 1299.0),
            ("1,299.99 บาท", 1299.99),
            ("THB 1,299.99", 1299.99),
            ("1299.99", 1299.99),
            ("1,299", 1299.0),
            ("invalid", None),
            ("", None),
            (None, None)
        ]
        
        for price_text, expected in test_cases:
            result = parser.parse_price(price_text)
            assert result == expected, f"Failed for {price_text}: expected {expected}, got {result}"
    
    def test_parse_number(self):
        """Test number parsing"""
        parser = HTMLParser()
        
        test_cases = [
            ("123", 123),
            ("1,234", 1234),
            ("1,234.56", 1234),  # Should convert to int
            ("123 reviews", 123),
            ("invalid", None),
            ("", None),
            (None, None)
        ]
        
        for number_text, expected in test_cases:
            result = parser.parse_number(number_text)
            assert result == expected, f"Failed for {number_text}: expected {expected}, got {result}"
    
    def test_parse_rating(self):
        """Test rating parsing"""
        parser = HTMLParser()
        
        test_cases = [
            ("4.5 out of 5 stars", 4.5),
            ("4.5/5", 4.5),
            ("4.5 จาก 5 ดาว", 4.5),
            ("4.5 ดาว", 4.5),
            ("4.5", 4.5),
            ("5.5", 5.0),  # Should cap at 5.0
            ("-1", 0.0),   # Should floor at 0.0
            ("invalid", None),
            ("", None),
            (None, None)
        ]
        
        for rating_text, expected in test_cases:
            result = parser.parse_rating(rating_text)
            assert result == expected, f"Failed for {rating_text}: expected {expected}, got {result}"
    
    def test_parse_availability(self):
        """Test availability parsing"""
        parser = HTMLParser()
        
        test_cases = [
            ("มีสินค้า", "in_stock"),
            ("In Stock", "in_stock"),
            ("พร้อมส่ง", "in_stock"),
            ("หมดสินค้า", "out_of_stock"),
            ("Out of Stock", "out_of_stock"),
            ("สั่งจองล่วงหน้า", "pre_order"),
            ("Pre-order", "pre_order"),
            ("unknown status", "unknown"),
            ("", None),
            (None, None)
        ]
        
        for availability_text, expected in test_cases:
            result = parser.parse_availability(availability_text)
            assert result == expected, f"Failed for {availability_text}: expected {expected}, got {result}"
    
    def test_extract_pagination(self):
        """Test pagination extraction"""
        parser = HTMLParser()
        html = """
        <html>
            <body>
                <div class="pagination">
                    <a href="/category/electronics?page=1">1</a>
                    <a href="/category/electronics?page=2">2</a>
                    <a href="/category/electronics?page=3">3</a>
                    <a href="/category/electronics?page=2">Next</a>
                </div>
            </body>
        </html>
        """
        soup = BeautifulSoup(html, 'html.parser')
        base_url = "https://example.com"
        
        selectors = ['.pagination a']
        result = parser.extract_pagination(soup, selectors, base_url)
        
        assert 'page_urls' in result
        assert len(result['page_urls']) >= 3
        assert 'next_page_url' in result
        assert result['next_page_url'] == "https://example.com/category/electronics?page=2"
        assert 'total_pages' in result
        assert result['total_pages'] == 3
    
    def test_statistics_tracking(self):
        """Test statistics tracking"""
        parser = HTMLParser()
        
        # Reset stats
        parser.reset_stats()
        stats = parser.get_stats()
        assert stats['total_extractions'] == 0
        assert stats['successful_extractions'] == 0
        assert stats['failed_extractions'] == 0
        
        # Perform some extractions
        html = "<html><body><h1>Test</h1></body></html>"
        soup = BeautifulSoup(html, 'html.parser')
        
        # Successful extraction
        parser.extract_text_by_selectors(soup, ['h1'])
        stats = parser.get_stats()
        assert stats['total_extractions'] == 1
        assert stats['successful_extractions'] == 1
        assert stats['failed_extractions'] == 0
        
        # Failed extraction
        parser.extract_text_by_selectors(soup, ['h2'])
        stats = parser.get_stats()
        assert stats['total_extractions'] == 2
        assert stats['successful_extractions'] == 1
        assert stats['failed_extractions'] == 1
    
    def test_complex_html_parsing(self, sample_product_html):
        """Test parsing complex HTML with multiple selectors"""
        parser = HTMLParser()
        soup = BeautifulSoup(sample_product_html, 'html.parser')
        
        # Test product name extraction
        selectors = ['.product-title', 'h1.title']
        name = parser.extract_text_by_selectors(soup, selectors)
        assert name == "High-Quality Test Product"
        
        # Test price extraction
        selectors = ['.price', '.cost']
        price_text = parser.extract_text_by_selectors(soup, selectors)
        price = parser.parse_price(price_text)
        assert price == 1299.99
        
        # Test brand extraction
        selectors = ['.brand-name', '.manufacturer']
        brand = parser.extract_text_by_selectors(soup, selectors)
        assert brand == "TestBrand"
        
        # Test SKU extraction
        selectors = ['.sku', '.product-code']
        sku = parser.extract_text_by_selectors(soup, selectors)
        assert sku == "SKU-12345"
        
        # Test rating extraction
        selectors = ['.rating-score', '.product-rating']
        rating_text = parser.extract_text_by_selectors(soup, selectors)
        rating = parser.parse_rating(rating_text)
        assert rating == 4.5
        
        # Test reviews count extraction
        selectors = ['.review-count', '.reviews-total']
        reviews_text = parser.extract_text_by_selectors(soup, selectors)
        reviews_count = parser.parse_number(reviews_text)
        assert reviews_count == 123
        
        # Test availability parsing
        selectors = ['.stock-status', '.availability']
        availability_text = parser.extract_text_by_selectors(soup, selectors)
        availability = parser.parse_availability(availability_text)
        assert availability == "in_stock"
        
        # Test image extraction
        selectors = ['.product-image img', '.gallery img']
        images = parser.extract_images(soup, selectors, "https://example.com")
        assert len(images) >= 2
        assert "https://example.com/images/product1.jpg" in images
        
        # Test specifications extraction
        selectors = ['.specifications table']
        specs = parser.extract_specifications(soup, selectors)
        assert "Weight" in specs
        assert specs["Weight"] == "2.5 kg"
    
    def test_error_handling(self):
        """Test error handling in parser"""
        parser = HTMLParser()
        
        # Test with invalid HTML
        html = "<html><body><h1>Unclosed tag"
        soup = BeautifulSoup(html, 'html.parser')
        
        # Should not raise exception
        result = parser.extract_text_by_selectors(soup, ['h1'])
        assert result == "Unclosed tag"
        
        # Test with empty selectors
        result = parser.extract_text_by_selectors(soup, [])
        assert result is None
        
        # Test with None soup
        result = parser.extract_text_by_selectors(None, ['h1'])
        assert result is None