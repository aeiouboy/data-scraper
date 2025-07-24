"""
HTML parser utilities for extracting product data from web pages
"""
import re
import logging
from typing import Dict, List, Any, Optional, Union
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup, Tag
import json
from decimal import Decimal
from datetime import datetime

logger = logging.getLogger(__name__)


class HTMLParser:
    """Advanced HTML parser with intelligent data extraction capabilities"""
    
    # Common price patterns
    PRICE_PATTERNS = [
        r'฿\s*([0-9,]+(?:\.[0-9]{1,2})?)',  # Thai Baht
        r'THB\s*([0-9,]+(?:\.[0-9]{1,2})?)',  # THB
        r'([0-9,]+(?:\.[0-9]{1,2})?)\s*บาท',  # Thai word for baht
        r'([0-9,]+(?:\.[0-9]{1,2})?)\s*฿',  # Baht symbol after
        r'([0-9,]+(?:\.[0-9]{1,2})?)',  # Just numbers
    ]
    
    # Common number patterns
    NUMBER_PATTERNS = [
        r'([0-9,]+(?:\.[0-9]+)?)',
        r'([0-9]+)',
    ]
    
    # Rating patterns
    RATING_PATTERNS = [
        r'([0-5](?:\.[0-9]+)?)\s*(?:out of|/|จาก)\s*5',
        r'([0-5](?:\.[0-9]+)?)\s*(?:stars?|ดาว)',
        r'([0-5](?:\.[0-9]+)?)',
    ]
    
    # Common Thai text patterns
    THAI_PATTERNS = {
        'in_stock': [
            'มีสินค้า', 'พร้อมส่ง', 'สินค้าพร้อม', 'มีของพร้อมส่ง',
            'In Stock', 'Available', 'Ready to Ship'
        ],
        'out_of_stock': [
            'หมดสินค้า', 'สินค้าหมด', 'ไม่มีสินค้า', 'Out of Stock',
            'Sold Out', 'Unavailable', 'Not Available'
        ],
        'pre_order': [
            'สั่งจองล่วงหน้า', 'Pre-order', 'Pre Order', 'สั่งจอง'
        ]
    }
    
    def __init__(self):
        self.stats = {
            'total_extractions': 0,
            'successful_extractions': 0,
            'failed_extractions': 0,
            'fallback_used': 0
        }
    
    def extract_text_by_selectors(self, soup: BeautifulSoup, selectors: List[str]) -> Optional[str]:
        """
        Extract text using a list of CSS selectors with fallback
        
        Args:
            soup: BeautifulSoup object
            selectors: List of CSS selectors to try
            
        Returns:
            Extracted text or None if no selectors match
        """
        self.stats['total_extractions'] += 1
        
        for selector in selectors:
            try:
                # Try CSS selector first
                if selector.startswith('css:'):
                    css_selector = selector[4:]
                    element = soup.select_one(css_selector)
                    if element:
                        text = self._extract_text_from_element(element)
                        if text:
                            self.stats['successful_extractions'] += 1
                            return text
                
                # Try XPath selector
                elif selector.startswith('xpath:'):
                    # Note: BeautifulSoup doesn't support XPath directly
                    # This is a placeholder for future lxml integration
                    continue
                
                # Try regex selector
                elif selector.startswith('regex:'):
                    pattern = selector[6:]
                    text = soup.get_text()
                    match = re.search(pattern, text, re.IGNORECASE)
                    if match:
                        result = match.group(1) if match.groups() else match.group(0)
                        self.stats['successful_extractions'] += 1
                        return result.strip()
                
                # Try JSON path selector
                elif selector.startswith('json:'):
                    json_path = selector[5:]
                    json_data = self._extract_json_from_soup(soup)
                    if json_data:
                        result = self._extract_from_json(json_data, json_path)
                        if result:
                            self.stats['successful_extractions'] += 1
                            return str(result)
                
                # Default CSS selector
                else:
                    element = soup.select_one(selector)
                    if element:
                        text = self._extract_text_from_element(element)
                        if text:
                            self.stats['successful_extractions'] += 1
                            return text
                        
            except Exception as e:
                logger.debug(f"Selector '{selector}' failed: {str(e)}")
                continue
        
        self.stats['failed_extractions'] += 1
        return None
    
    def extract_text_list(self, soup: BeautifulSoup, selectors: List[str]) -> List[str]:
        """Extract list of texts using selectors"""
        results = []
        
        for selector in selectors:
            try:
                if selector.startswith('css:'):
                    css_selector = selector[4:]
                    elements = soup.select(css_selector)
                elif selector.startswith('regex:'):
                    pattern = selector[6:]
                    text = soup.get_text()
                    matches = re.findall(pattern, text, re.IGNORECASE)
                    results.extend(matches)
                    continue
                else:
                    elements = soup.select(selector)
                
                for element in elements:
                    text = self._extract_text_from_element(element)
                    if text and text not in results:
                        results.append(text)
                        
            except Exception as e:
                logger.debug(f"List selector '{selector}' failed: {str(e)}")
                continue
        
        return results
    
    def extract_links(self, soup: BeautifulSoup, selectors: List[str], base_url: str) -> List[str]:
        """Extract links using selectors"""
        links = []
        
        for selector in selectors:
            try:
                if selector.startswith('css:'):
                    css_selector = selector[4:]
                    elements = soup.select(css_selector)
                else:
                    elements = soup.select(selector)
                
                for element in elements:
                    href = element.get('href')
                    if href:
                        full_url = urljoin(base_url, href)
                        if full_url not in links:
                            links.append(full_url)
                            
            except Exception as e:
                logger.debug(f"Link selector '{selector}' failed: {str(e)}")
                continue
        
        return links
    
    def extract_images(self, soup: BeautifulSoup, selectors: List[str], base_url: str) -> List[str]:
        """Extract image URLs using selectors"""
        images = []
        
        for selector in selectors:
            try:
                if selector.startswith('css:'):
                    css_selector = selector[4:]
                    elements = soup.select(css_selector)
                else:
                    elements = soup.select(selector)
                
                for element in elements:
                    # Try different image attributes
                    for attr in ['src', 'data-src', 'data-original', 'data-lazy']:
                        src = element.get(attr)
                        if src:
                            full_url = urljoin(base_url, src)
                            if full_url not in images:
                                images.append(full_url)
                            break
                            
            except Exception as e:
                logger.debug(f"Image selector '{selector}' failed: {str(e)}")
                continue
        
        return images
    
    def extract_specifications(self, soup: BeautifulSoup, selectors: List[str]) -> Dict[str, Any]:
        """Extract product specifications"""
        specs = {}
        
        for selector in selectors:
            try:
                if selector.startswith('css:'):
                    css_selector = selector[4:]
                    elements = soup.select(css_selector)
                else:
                    elements = soup.select(selector)
                
                for element in elements:
                    # Try to extract key-value pairs
                    key_value = self._extract_key_value_from_element(element)
                    if key_value:
                        specs.update(key_value)
                        
            except Exception as e:
                logger.debug(f"Specs selector '{selector}' failed: {str(e)}")
                continue
        
        return specs
    
    def extract_pagination(self, soup: BeautifulSoup, selectors: List[str], base_url: str) -> Dict[str, Any]:
        """Extract pagination information"""
        pagination = {
            'current_page': 1,
            'total_pages': 1,
            'next_page_url': None,
            'prev_page_url': None,
            'page_urls': []
        }
        
        for selector in selectors:
            try:
                if selector.startswith('css:'):
                    css_selector = selector[4:]
                    elements = soup.select(css_selector)
                else:
                    elements = soup.select(selector)
                
                # Extract page numbers and URLs
                for element in elements:
                    if element.name == 'a' and element.get('href'):
                        href = element.get('href')
                        full_url = urljoin(base_url, href)
                        text = self._extract_text_from_element(element)
                        
                        if text and text.isdigit():
                            pagination['page_urls'].append({
                                'page': int(text),
                                'url': full_url
                            })
                        elif 'next' in text.lower() or 'ถัดไป' in text:
                            pagination['next_page_url'] = full_url
                        elif 'prev' in text.lower() or 'ก่อนหน้า' in text:
                            pagination['prev_page_url'] = full_url
                            
            except Exception as e:
                logger.debug(f"Pagination selector '{selector}' failed: {str(e)}")
                continue
        
        # Calculate total pages
        if pagination['page_urls']:
            pagination['total_pages'] = max(p['page'] for p in pagination['page_urls'])
        
        return pagination
    
    def extract_filters(self, soup: BeautifulSoup, selectors: List[str]) -> List[Dict[str, Any]]:
        """Extract available filters"""
        filters = []
        
        for selector in selectors:
            try:
                if selector.startswith('css:'):
                    css_selector = selector[4:]
                    elements = soup.select(css_selector)
                else:
                    elements = soup.select(selector)
                
                for element in elements:
                    filter_data = self._extract_filter_from_element(element)
                    if filter_data:
                        filters.append(filter_data)
                        
            except Exception as e:
                logger.debug(f"Filter selector '{selector}' failed: {str(e)}")
                continue
        
        return filters
    
    def parse_price(self, price_text: str) -> Optional[float]:
        """Parse price from text"""
        if not price_text:
            return None
        
        # Clean the text
        price_text = price_text.strip()
        
        # Try each price pattern
        for pattern in self.PRICE_PATTERNS:
            match = re.search(pattern, price_text, re.IGNORECASE)
            if match:
                try:
                    # Remove commas and convert to float
                    price_str = match.group(1).replace(',', '')
                    return float(price_str)
                except (ValueError, IndexError):
                    continue
        
        return None
    
    def parse_number(self, number_text: str) -> Optional[int]:
        """Parse number from text"""
        if not number_text:
            return None
        
        # Clean the text
        number_text = number_text.strip()
        
        # Try each number pattern
        for pattern in self.NUMBER_PATTERNS:
            match = re.search(pattern, number_text, re.IGNORECASE)
            if match:
                try:
                    # Remove commas and convert to int
                    number_str = match.group(1).replace(',', '')
                    return int(float(number_str))  # Convert to float first in case of decimals
                except (ValueError, IndexError):
                    continue
        
        return None
    
    def parse_rating(self, rating_text: str) -> Optional[float]:
        """Parse rating from text"""
        if not rating_text:
            return None
        
        # Clean the text
        rating_text = rating_text.strip()
        
        # Try each rating pattern
        for pattern in self.RATING_PATTERNS:
            match = re.search(pattern, rating_text, re.IGNORECASE)
            if match:
                try:
                    rating = float(match.group(1))
                    # Ensure rating is between 0 and 5
                    return max(0, min(5, rating))
                except (ValueError, IndexError):
                    continue
        
        return None
    
    def parse_availability(self, availability_text: str) -> Optional[str]:
        """Parse availability status from text"""
        if not availability_text:
            return None
        
        text_lower = availability_text.lower()
        
        # Check for in stock
        for pattern in self.THAI_PATTERNS['in_stock']:
            if pattern.lower() in text_lower:
                return 'in_stock'
        
        # Check for out of stock
        for pattern in self.THAI_PATTERNS['out_of_stock']:
            if pattern.lower() in text_lower:
                return 'out_of_stock'
        
        # Check for pre-order
        for pattern in self.THAI_PATTERNS['pre_order']:
            if pattern.lower() in text_lower:
                return 'pre_order'
        
        return 'unknown'
    
    def _extract_text_from_element(self, element: Tag) -> Optional[str]:
        """Extract and clean text from element"""
        if not element:
            return None
        
        # Get text content
        text = element.get_text(strip=True)
        
        # Clean whitespace
        text = re.sub(r'\s+', ' ', text)
        
        return text if text else None
    
    def _extract_key_value_from_element(self, element: Tag) -> Dict[str, str]:
        """Extract key-value pairs from element"""
        specs = {}
        
        # Try different structures
        if element.name == 'table':
            # Table structure
            for row in element.find_all('tr'):
                cols = row.find_all(['td', 'th'])
                if len(cols) >= 2:
                    key = self._extract_text_from_element(cols[0])
                    value = self._extract_text_from_element(cols[1])
                    if key and value:
                        specs[key] = value
        
        elif element.name == 'dl':
            # Definition list structure
            terms = element.find_all('dt')
            definitions = element.find_all('dd')
            for term, definition in zip(terms, definitions):
                key = self._extract_text_from_element(term)
                value = self._extract_text_from_element(definition)
                if key and value:
                    specs[key] = value
        
        else:
            # Try to find key-value patterns in text
            text = self._extract_text_from_element(element)
            if text:
                # Look for patterns like "Key: Value"
                for line in text.split('\n'):
                    if ':' in line:
                        parts = line.split(':', 1)
                        if len(parts) == 2:
                            key = parts[0].strip()
                            value = parts[1].strip()
                            if key and value:
                                specs[key] = value
        
        return specs
    
    def _extract_filter_from_element(self, element: Tag) -> Optional[Dict[str, Any]]:
        """Extract filter information from element"""
        if not element:
            return None
        
        filter_data = {
            'name': None,
            'type': 'unknown',
            'options': []
        }
        
        # Try to identify filter type
        if element.name == 'select':
            filter_data['type'] = 'select'
            filter_data['name'] = element.get('name') or element.get('id')
            
            for option in element.find_all('option'):
                option_text = self._extract_text_from_element(option)
                if option_text:
                    filter_data['options'].append({
                        'text': option_text,
                        'value': option.get('value', option_text)
                    })
        
        elif element.name == 'input' and element.get('type') in ['checkbox', 'radio']:
            filter_data['type'] = element.get('type')
            filter_data['name'] = element.get('name')
            
            # Find associated label
            label = element.find_next('label')
            if label:
                filter_data['options'].append({
                    'text': self._extract_text_from_element(label),
                    'value': element.get('value')
                })
        
        return filter_data if filter_data['name'] else None
    
    def _extract_json_from_soup(self, soup: BeautifulSoup) -> Optional[Dict]:
        """Extract JSON data from script tags"""
        # Look for JSON-LD structured data
        json_scripts = soup.find_all('script', {'type': 'application/ld+json'})
        for script in json_scripts:
            try:
                json_data = json.loads(script.string)
                return json_data
            except (json.JSONDecodeError, AttributeError):
                continue
        
        # Look for other JSON data in script tags
        scripts = soup.find_all('script')
        for script in scripts:
            if script.string:
                # Try to find JSON objects
                json_matches = re.findall(r'\{[^{}]*\}', script.string)
                for match in json_matches:
                    try:
                        json_data = json.loads(match)
                        return json_data
                    except json.JSONDecodeError:
                        continue
        
        return None
    
    def _extract_from_json(self, json_data: Dict, json_path: str) -> Any:
        """Extract value from JSON using simple path notation"""
        try:
            # Simple path like "product.name" or "offers.price"
            keys = json_path.split('.')
            current = json_data
            
            for key in keys:
                if isinstance(current, dict) and key in current:
                    current = current[key]
                elif isinstance(current, list) and key.isdigit():
                    index = int(key)
                    if 0 <= index < len(current):
                        current = current[index]
                    else:
                        return None
                else:
                    return None
            
            return current
            
        except Exception as e:
            logger.debug(f"JSON path extraction failed: {str(e)}")
            return None
    
    def get_stats(self) -> Dict[str, Any]:
        """Get parser statistics"""
        return self.stats.copy()
    
    def reset_stats(self):
        """Reset parser statistics"""
        self.stats = {
            'total_extractions': 0,
            'successful_extractions': 0,
            'failed_extractions': 0,
            'fallback_used': 0
        }