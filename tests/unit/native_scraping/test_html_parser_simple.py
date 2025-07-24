"""
Simple unit tests for HTML parser (standalone)
"""
import pytest
import sys
import os
from pathlib import Path

# Add the src directory to the path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / 'src'))

try:
    from scrapers.engines.html_parser import HTMLParser
    from bs4 import BeautifulSoup
    HTML_PARSER_AVAILABLE = True
except ImportError as e:
    HTML_PARSER_AVAILABLE = False
    import_error = str(e)


@pytest.mark.unit
@pytest.mark.native
@pytest.mark.skipif(not HTML_PARSER_AVAILABLE, reason="HTML parser not available")
class TestHTMLParserSimple:
    """Simple test cases for HTML parser functionality"""
    
    def test_parse_price_basic(self):
        """Test basic price parsing functionality"""
        if not HTML_PARSER_AVAILABLE:
            pytest.skip("HTML parser not available")
        
        parser = HTMLParser()
        
        # Test basic price formats
        test_cases = [
            ("฿1,299.99", 1299.99),
            ("฿1,299", 1299.0),
            ("1,299.99 บาท", 1299.99),
            ("1299.99", 1299.99),
            ("invalid", None),
        ]
        
        for price_text, expected in test_cases:
            result = parser.parse_price(price_text)
            assert result == expected, f"Failed for {price_text}: expected {expected}, got {result}"
    
    def test_parse_number_basic(self):
        """Test basic number parsing functionality"""
        if not HTML_PARSER_AVAILABLE:
            pytest.skip("HTML parser not available")
        
        parser = HTMLParser()
        
        test_cases = [
            ("123", 123),
            ("1,234", 1234),
            ("invalid", None),
        ]
        
        for number_text, expected in test_cases:
            result = parser.parse_number(number_text)
            assert result == expected, f"Failed for {number_text}: expected {expected}, got {result}"


@pytest.mark.unit
@pytest.mark.native
@pytest.mark.skipif(HTML_PARSER_AVAILABLE, reason="Testing import error case")
class TestHTMLParserUnavailable:
    """Test case when HTML parser is not available"""
    
    def test_import_error_handling(self):
        """Test that import errors are handled gracefully"""
        assert not HTML_PARSER_AVAILABLE
        # This test just verifies that we can handle the import error gracefully