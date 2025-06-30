"""
Text cleaning and extraction utilities
"""
import re
from typing import Optional, Union
from decimal import Decimal


def clean_text(text: Optional[str]) -> str:
    """
    Clean and normalize text
    
    Args:
        text: Text to clean
        
    Returns:
        Cleaned text
    """
    if not text:
        return ""
    
    # Convert to string if needed
    text = str(text)
    
    # Remove excessive whitespace
    text = re.sub(r'\s+', ' ', text)
    
    # Remove leading/trailing whitespace
    text = text.strip()
    
    # Remove HTML entities
    text = re.sub(r'&[a-zA-Z]+;', ' ', text)
    
    # Remove special characters but keep Thai characters
    # Keep: Thai (u0E00-u0E7F), alphanumeric, spaces, common punctuation
    text = re.sub(r'[^\u0E00-\u0E7F\w\s\-.,!?()฿]', '', text)
    
    # Clean up multiple spaces again
    text = re.sub(r'\s+', ' ', text)
    
    return text.strip()


def extract_number_from_string(text: Union[str, int, float]) -> Optional[float]:
    """
    Extract numeric value from string
    
    Args:
        text: String containing number
        
    Returns:
        Extracted number or None
    """
    if isinstance(text, (int, float)):
        return float(text)
    
    if not text:
        return None
    
    # Convert to string
    text = str(text)
    
    # Remove common currency symbols and text
    text = re.sub(r'[฿$€£¥]', '', text)
    text = re.sub(r'(บาท|baht|THB)', '', text, flags=re.IGNORECASE)
    
    # Remove commas and spaces
    text = text.replace(',', '').replace(' ', '')
    
    # Extract number pattern
    match = re.search(r'[-+]?[0-9]*\.?[0-9]+', text)
    
    if match:
        try:
            return float(match.group())
        except ValueError:
            return None
    
    return None


def extract_price(text: str) -> Optional[Decimal]:
    """
    Extract price from text
    
    Args:
        text: Text containing price
        
    Returns:
        Price as Decimal or None
    """
    number = extract_number_from_string(text)
    
    if number is not None and number >= 0:
        return Decimal(str(number))
    
    return None


def normalize_brand_name(brand: str) -> str:
    """
    Normalize brand name for matching
    
    Args:
        brand: Brand name to normalize
        
    Returns:
        Normalized brand name
    """
    if not brand:
        return ""
    
    # Convert to uppercase
    brand = brand.upper()
    
    # Remove common suffixes
    brand = re.sub(r'\s*(CO\.|LTD\.|INC\.|CORP\.|LIMITED|บริษัท|จำกัด).*$', '', brand)
    
    # Remove special characters
    brand = re.sub(r'[^\w\s]', '', brand)
    
    # Clean whitespace
    brand = re.sub(r'\s+', ' ', brand).strip()
    
    return brand


def extract_thai_text(text: str) -> str:
    """
    Extract only Thai text from mixed language string
    
    Args:
        text: Mixed language text
        
    Returns:
        Thai text only
    """
    if not text:
        return ""
    
    # Keep only Thai characters and spaces
    thai_text = re.sub(r'[^\u0E00-\u0E7F\s]', ' ', text)
    
    # Clean up whitespace
    thai_text = re.sub(r'\s+', ' ', thai_text).strip()
    
    return thai_text


def extract_english_text(text: str) -> str:
    """
    Extract only English text from mixed language string
    
    Args:
        text: Mixed language text
        
    Returns:
        English text only
    """
    if not text:
        return ""
    
    # Keep only English characters, numbers, and spaces
    english_text = re.sub(r'[^a-zA-Z0-9\s]', ' ', text)
    
    # Clean up whitespace
    english_text = re.sub(r'\s+', ' ', english_text).strip()
    
    return english_text