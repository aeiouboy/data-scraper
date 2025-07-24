"""Unit tests for text normalization utilities."""

import pytest
from src.utils.text_normalizer import TextNormalizer


class TestTextNormalizer:
    """Test text normalization functionality."""
    
    @pytest.fixture
    def normalizer(self):
        """Create a text normalizer instance."""
        return TextNormalizer()
    
    def test_normalize_thai_brands(self, normalizer):
        """Test Thai brand name normalization."""
        # Same brand, different spellings
        assert normalizer.normalize_brand("บ๊อช") == normalizer.normalize_brand("BOSCH")
        assert normalizer.normalize_brand("มากิต้า") == normalizer.normalize_brand("MAKITA")
        assert normalizer.normalize_brand("สแตนเล่ย์") == normalizer.normalize_brand("STANLEY")
        
        # Case insensitive
        assert normalizer.normalize_brand("bosch") == normalizer.normalize_brand("BOSCH")
        assert normalizer.normalize_brand("Bosch") == normalizer.normalize_brand("BOSCH")
    
    def test_normalize_product_names(self, normalizer):
        """Test product name normalization."""
        # Remove extra spaces
        assert normalizer.normalize_name("  Product   Name  ") == "product name"
        
        # Remove special characters
        assert normalizer.normalize_name("Product-Name™") == "product name"
        assert normalizer.normalize_name("Product_Name®") == "product name"
        
        # Thai and English mix
        name1 = "สว่านไฟฟ้า BOSCH GBM 13 RE"
        name2 = "BOSCH สว่านไฟฟ้า รุ่น GBM 13 RE"
        # Should extract similar tokens
        tokens1 = set(normalizer.tokenize(name1))
        tokens2 = set(normalizer.tokenize(name2))
        assert len(tokens1 & tokens2) >= 3  # At least 3 common tokens
    
    def test_normalize_specifications(self, normalizer):
        """Test specification normalization."""
        # Power specifications
        assert normalizer.normalize_spec("600W") == normalizer.normalize_spec("600 วัตต์")
        assert normalizer.normalize_spec("600 watts") == normalizer.normalize_spec("600W")
        
        # Voltage specifications
        assert normalizer.normalize_spec("220V") == normalizer.normalize_spec("220 โวลต์")
        assert normalizer.normalize_spec("220 volts") == normalizer.normalize_spec("220V")
        
        # Size specifications
        assert normalizer.normalize_spec("13mm") == normalizer.normalize_spec("13 มม.")
        assert normalizer.normalize_spec("13 millimeters") == normalizer.normalize_spec("13mm")
    
    def test_extract_numbers(self, normalizer):
        """Test number extraction from text."""
        assert normalizer.extract_numbers("600W power") == [600]
        assert normalizer.extract_numbers("2,990 บาท") == [2990]
        assert normalizer.extract_numbers("13mm drill bit") == [13]
        assert normalizer.extract_numbers("No numbers here") == []
        assert normalizer.extract_numbers("1.5kg weight") == [1.5]
    
    def test_remove_stop_words(self, normalizer):
        """Test stop word removal."""
        # Thai stop words
        text = "นี่คือสว่านที่ดีมาก"
        filtered = normalizer.remove_stop_words(text)
        assert "นี่" not in filtered
        assert "คือ" not in filtered
        assert "ที่" not in filtered
        assert "สว่าน" in filtered
        
        # English stop words
        text = "This is a very good drill"
        filtered = normalizer.remove_stop_words(text)
        assert "this" not in filtered.lower()
        assert "is" not in filtered.lower()
        assert "a" not in filtered.lower()
        assert "drill" in filtered.lower()
    
    def test_normalize_categories(self, normalizer):
        """Test category normalization."""
        # Thai to English mapping
        assert normalizer.normalize_category("เครื่องมือไฟฟ้า") == "power tools"
        assert normalizer.normalize_category("เครื่องมือช่าง") == "hand tools"
        
        # Already English
        assert normalizer.normalize_category("Power Tools") == "power tools"
        assert normalizer.normalize_category("HAND TOOLS") == "hand tools"
        
        # With slashes
        assert normalizer.normalize_category("Tools/Power Tools/Drills") == "tools/power tools/drills"
    
    def test_calculate_similarity(self, normalizer):
        """Test text similarity calculation."""
        # Identical texts
        assert normalizer.calculate_similarity("test", "test") == 1.0
        
        # Similar texts
        sim1 = normalizer.calculate_similarity("Bosch Drill 600W", "BOSCH Power Drill 600 Watts")
        assert 0.7 < sim1 < 0.9
        
        # Different texts
        sim2 = normalizer.calculate_similarity("Bosch Drill", "Makita Saw")
        assert sim2 < 0.3
        
        # Empty text
        assert normalizer.calculate_similarity("", "test") == 0.0
        assert normalizer.calculate_similarity("test", "") == 0.0
    
    def test_tokenize(self, normalizer):
        """Test text tokenization."""
        # English
        tokens = normalizer.tokenize("Bosch Professional Drill GBM 13 RE")
        assert "bosch" in tokens
        assert "professional" in tokens
        assert "drill" in tokens
        assert "gbm" in tokens
        assert "13" in tokens
        assert "re" in tokens
        
        # Thai
        tokens = normalizer.tokenize("สว่านไฟฟ้า บ๊อช 600 วัตต์")
        assert "สว่านไฟฟ้า" in tokens
        assert "บ๊อช" in tokens
        assert "600" in tokens
        assert "วัตต์" in tokens
    
    def test_extract_model_number(self, normalizer):
        """Test model number extraction."""
        assert normalizer.extract_model("Bosch GBM 13 RE Professional") == "GBM 13 RE"
        assert normalizer.extract_model("Makita DF457D Cordless Drill") == "DF457D"
        assert normalizer.extract_model("Stanley STHT0-51309 Hammer") == "STHT0-51309"
        assert normalizer.extract_model("Generic Product Name") is None
    
    def test_normalize_units(self, normalizer):
        """Test unit normalization."""
        # Weight
        assert normalizer.normalize_unit("2.5kg") == "2.5 kg"
        assert normalizer.normalize_unit("2.5 กิโลกรัม") == "2.5 kg"
        assert normalizer.normalize_unit("2500g") == "2.5 kg"
        assert normalizer.normalize_unit("2500 กรัม") == "2.5 kg"
        
        # Length
        assert normalizer.normalize_unit("100cm") == "100 cm"
        assert normalizer.normalize_unit("100 เซนติเมตร") == "100 cm"
        assert normalizer.normalize_unit("1m") == "100 cm"
        assert normalizer.normalize_unit("1 เมตร") == "100 cm"
        
        # Volume
        assert normalizer.normalize_unit("1L") == "1 L"
        assert normalizer.normalize_unit("1 ลิตร") == "1 L"
        assert normalizer.normalize_unit("1000ml") == "1 L"
        assert normalizer.normalize_unit("1000 มิลลิลิตร") == "1 L"