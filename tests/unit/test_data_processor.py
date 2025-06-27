"""
Unit tests for DataProcessor class
"""
import pytest
from decimal import Decimal
from app.core.data_processor import DataProcessor
from app.models.product import Product


class TestDataProcessor:
    """Test suite for DataProcessor"""
    
    def setup_method(self):
        """Setup for each test method"""
        self.processor = DataProcessor()
    
    # Price extraction tests
    def test_extract_price_valid_numbers(self):
        """Test price extraction from valid numeric strings"""
        test_cases = [
            ("2490", Decimal("2490")),
            ("2,490", Decimal("2490")),
            ("฿2,490", Decimal("2490")),
            ("฿ 2,490 บาท", Decimal("2490")),
            ("2490.50", Decimal("2490.50")),
            ("฿2,490.75", Decimal("2490.75"))
        ]
        
        for input_text, expected in test_cases:
            result = self.processor.extract_price(input_text)
            assert result == expected, f"Failed for input: {input_text}"
    
    def test_extract_price_invalid_inputs(self):
        """Test price extraction with invalid inputs"""
        invalid_inputs = [
            None,
            "",
            "not a number",
            "abcdef",  # Pure letters
            "฿฿฿",
            "บาทบาท",
            [],
            {},
            0  # Edge case: zero should return None (not considered valid price)
        ]
        
        for invalid_input in invalid_inputs:
            result = self.processor.extract_price(invalid_input)
            assert result is None, f"Should return None for: {invalid_input}"
    
    def test_extract_price_mixed_alphanumeric(self):
        """Test price extraction from mixed alphanumeric strings"""
        # These should extract the numeric portion
        test_cases = [
            ("abc123", Decimal("123")),
            ("SKU-456", Decimal("456")),
            ("Model2490", Decimal("2490")),
        ]
        
        for input_text, expected in test_cases:
            result = self.processor.extract_price(input_text)
            assert result == expected, f"Failed for input: {input_text}"
    
    def test_extract_price_edge_cases(self):
        """Test edge cases for price extraction"""
        # Multiple numbers - should extract first
        result = self.processor.extract_price("Price: ฿2,490 was ฿2,990")
        assert result == Decimal("2490")
        
        # Very small numbers
        result = self.processor.extract_price("฿0.01")
        assert result == Decimal("0.01")
        
        # Large numbers
        result = self.processor.extract_price("฿999,999.99")
        assert result == Decimal("999999.99")
    
    # Text cleaning tests
    def test_clean_text_normal_input(self):
        """Test text cleaning with normal input"""
        test_cases = [
            ("  Hello World  ", "Hello World"),
            ("Multiple    spaces", "Multiple spaces"),
            ("Line\nbreaks\nhere", "Line breaks here"),
            ("Tab\there", "Tab here")
        ]
        
        for input_text, expected in test_cases:
            result = self.processor.clean_text(input_text)
            assert result == expected, f"Failed for: {input_text}"
    
    def test_clean_text_special_characters(self):
        """Test text cleaning with special characters"""
        # Control characters should be removed
        input_with_control = "Hello\x00\x1f\x7fWorld"
        result = self.processor.clean_text(input_with_control)
        assert result == "HelloWorld"
        
        # Thai characters should be preserved
        thai_text = "สินค้าคุณภาพดี"
        result = self.processor.clean_text(thai_text)
        assert result == thai_text
    
    def test_clean_text_edge_cases(self):
        """Test edge cases for text cleaning"""
        # None and empty inputs
        assert self.processor.clean_text(None) == ""
        assert self.processor.clean_text("") == ""
        assert self.processor.clean_text(123) == "123"
    
    # SKU extraction tests
    def test_extract_sku_valid_patterns(self):
        """Test SKU extraction with valid patterns"""
        test_cases = [
            ("SKU: ABC-12345", "ABC-12345"),
            ("รหัส: HP-67890", "HP-67890"),
            ("Product Code: XYZ123", "XYZ123"),
            ("Model: 1000012345", "1000012345"),
            ("Part No. DEF-4567", "DEF-4567")
        ]
        
        for input_text, expected in test_cases:
            result = self.processor.extract_sku(input_text)
            assert result == expected.upper(), f"Failed for: {input_text}"
    
    def test_extract_sku_no_match(self):
        """Test SKU extraction when no pattern matches"""
        no_match_inputs = [
            "No SKU here",
            "Just regular text",
            "Numbers 123 but no pattern",
            None,
            ""
        ]
        
        for input_text in no_match_inputs:
            result = self.processor.extract_sku(input_text)
            assert result is None, f"Should return None for: {input_text}"
    
    # Image processing tests
    def test_process_images_valid_urls(self):
        """Test image processing with valid URLs"""
        valid_images = [
            "https://example.com/image1.jpg",
            "http://example.com/image2.png",
            "//cdn.example.com/image3.gif"
        ]
        
        result = self.processor.process_images(valid_images)
        
        assert len(result) == 3
        assert result[0] == "https://example.com/image1.jpg"
        assert result[1] == "http://example.com/image2.png"
        assert result[2] == "https://cdn.example.com/image3.gif"  # Protocol added
    
    def test_process_images_invalid_inputs(self):
        """Test image processing with invalid inputs"""
        # Empty and None inputs
        assert self.processor.process_images(None) == []
        assert self.processor.process_images([]) == []
        assert self.processor.process_images("") == []
        
        # Invalid URLs
        invalid_images = ["not-a-url", "ftp://invalid.com", "relative/path"]
        result = self.processor.process_images(invalid_images)
        assert result == []
    
    def test_process_images_mixed_input(self):
        """Test image processing with mixed valid/invalid inputs"""
        mixed_images = [
            "https://valid.com/image.jpg",
            "not-a-url",
            "//protocol-relative.com/image.png",
            "",
            "http://another-valid.com/pic.gif"
        ]
        
        result = self.processor.process_images(mixed_images)
        
        assert len(result) == 3
        assert "https://valid.com/image.jpg" in result
        assert "https://protocol-relative.com/image.png" in result
        assert "http://another-valid.com/pic.gif" in result
    
    # Availability determination tests
    def test_determine_availability_in_stock(self):
        """Test availability detection for in-stock items"""
        in_stock_texts = [
            "in stock",
            "available now",
            "มีสินค้า",
            "พร้อมส่ง",
            "สินค้าพร้อม",
            "IN STOCK",
            "ready to ship"
        ]
        
        for text in in_stock_texts:
            result = self.processor.determine_availability(text)
            assert result == "in_stock", f"Failed for: {text}"
    
    def test_determine_availability_out_of_stock(self):
        """Test availability detection for out-of-stock items"""
        out_of_stock_texts = [
            "out of stock",
            "unavailable",
            "หมด",
            "สินค้าหมด",
            "sold out",
            "ไม่มีสินค้า",
            "OUT OF STOCK"
        ]
        
        for text in out_of_stock_texts:
            result = self.processor.determine_availability(text)
            assert result == "out_of_stock", f"Failed for: {text}"
    
    def test_determine_availability_unknown(self):
        """Test availability detection for unknown status"""
        unknown_texts = [
            "contact for availability",
            "check with store",
            "unknown status",
            None,
            ""
        ]
        
        for text in unknown_texts:
            result = self.processor.determine_availability(text)
            assert result == "unknown", f"Failed for: {text}"
    
    # Product data processing tests
    def test_process_product_data_complete(self, test_raw_data):
        """Test processing complete product data"""
        url = "https://www.homepro.co.th/p/1001234567"
        
        result = self.processor.process_product_data(test_raw_data, url)
        
        assert result is not None
        assert isinstance(result, Product)
        assert result.name == "เครื่องเจาะไฟฟ้า TestBrand 18V"
        assert result.sku == "1001234567"  # Extracted from URL
        assert result.brand == "TestBrand"
        assert result.current_price == Decimal("2490")
        assert result.original_price == Decimal("2990")
        assert result.url == url
    
    def test_process_product_data_minimal(self):
        """Test processing with minimal data"""
        minimal_data = {
            "metadata": {
                "title": "Basic Product"
            }
        }
        url = "https://www.homepro.co.th/p/9999999999"
        
        result = self.processor.process_product_data(minimal_data, url)
        
        assert result is not None
        assert result.name == "Basic Product"
        assert result.sku == "9999999999"
        assert result.url == url
    
    def test_process_product_data_invalid(self):
        """Test processing with invalid/empty data"""
        invalid_data_sets = [
            {},  # Empty dict
            {"metadata": {}},  # Empty metadata
            {"metadata": {"title": ""}},  # Empty title
        ]
        
        url = "https://www.homepro.co.th/p/1234567890"
        
        for invalid_data in invalid_data_sets:
            result = self.processor.process_product_data(invalid_data, url)
            # Should return None for invalid data
            assert result is None or not result.name
    
    # Product validation tests
    def test_validate_product_valid(self, test_product_data):
        """Test validation with valid product"""
        product = Product(**test_product_data)
        
        is_valid = self.processor.validate_product(product)
        assert is_valid is True
    
    def test_validate_product_missing_required_fields(self, test_product_data):
        """Test validation with missing required fields"""
        # Test missing SKU
        data_no_sku = test_product_data.copy()
        data_no_sku["sku"] = ""
        product = Product(**data_no_sku)
        assert self.processor.validate_product(product) is False
        
        # Test missing name
        data_no_name = test_product_data.copy()
        data_no_name["name"] = ""
        product = Product(**data_no_name)
        assert self.processor.validate_product(product) is False
        
        # Test missing URL
        data_no_url = test_product_data.copy()
        data_no_url["url"] = ""
        product = Product(**data_no_url)
        assert self.processor.validate_product(product) is False
    
    def test_validate_product_invalid_price(self, test_product_data):
        """Test validation with invalid prices"""
        # Negative price
        data_negative_price = test_product_data.copy()
        data_negative_price["current_price"] = -100.0
        product = Product(**data_negative_price)
        assert self.processor.validate_product(product) is False
        
        # Zero price
        data_zero_price = test_product_data.copy()
        data_zero_price["current_price"] = 0.0
        product = Product(**data_zero_price)
        assert self.processor.validate_product(product) is False
    
    def test_validate_product_invalid_lengths(self, test_product_data):
        """Test validation with invalid field lengths"""
        # Name too short
        data_short_name = test_product_data.copy()
        data_short_name["name"] = "AB"
        product = Product(**data_short_name)
        assert self.processor.validate_product(product) is False
        
        # Name too long
        data_long_name = test_product_data.copy()
        data_long_name["name"] = "A" * 501
        product = Product(**data_long_name)
        assert self.processor.validate_product(product) is False
        
        # SKU too short
        data_short_sku = test_product_data.copy()
        data_short_sku["sku"] = "AB"
        product = Product(**data_short_sku)
        assert self.processor.validate_product(product) is False
        
        # SKU too long
        data_long_sku = test_product_data.copy()
        data_long_sku["sku"] = "A" * 51
        product = Product(**data_long_sku)
        assert self.processor.validate_product(product) is False


# Parametrized tests for comprehensive coverage
class TestDataProcessorParametrized:
    """Parametrized tests for DataProcessor"""
    
    @pytest.mark.parametrize("input_price,expected", [
        ("฿1,234", Decimal("1234")),
        ("2,500.75 บาท", Decimal("2500.75")),
        ("Price: ฿999", Decimal("999")),
        ("฿ 10,000.00", Decimal("10000.00")),
        ("123456", Decimal("123456")),
    ])
    def test_extract_price_parametrized(self, input_price, expected):
        """Parametrized test for price extraction"""
        processor = DataProcessor()
        result = processor.extract_price(input_price)
        assert result == expected
    
    @pytest.mark.parametrize("input_text,expected", [
        ("  spaced  text  ", "spaced text"),
        ("line\nbreak\ntext", "line break text"),
        ("tab\ttab\ttext", "tab tab text"),
        ("mixed \n\t spaces", "mixed spaces"),
    ])
    def test_clean_text_parametrized(self, input_text, expected):
        """Parametrized test for text cleaning"""
        processor = DataProcessor()
        result = processor.clean_text(input_text)
        assert result == expected
    
    @pytest.mark.parametrize("availability_text,expected", [
        ("Product is in stock", "in_stock"),
        ("Currently unavailable", "out_of_stock"),
        ("มีสินค้าพร้อมส่ง", "in_stock"),
        ("สินค้าหมดแล้ว", "out_of_stock"),
        ("Unknown status", "unknown"),
    ])
    def test_availability_parametrized(self, availability_text, expected):
        """Parametrized test for availability determination"""
        processor = DataProcessor()
        result = processor.determine_availability(availability_text)
        assert result == expected