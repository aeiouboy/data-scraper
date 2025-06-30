"""
Adaptive Scraper Mixin - Adds adaptive scraping capabilities to existing scrapers
"""
import logging
import time
from typing import Dict, Any, Optional, List
from bs4 import BeautifulSoup
import lxml.html
import json
import re

from app.core.scraper_config_manager import ScraperConfigManager, Selector

logger = logging.getLogger(__name__)


class AdaptiveScraperMixin:
    """
    Mixin class that adds adaptive scraping capabilities to any scraper
    
    Usage:
        class HomeProScraper(BaseScraper, AdaptiveScraperMixin):
            pass
    """
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.config_manager = ScraperConfigManager()
        self._extraction_cache = {}
        
    async def extract_with_fallback(
        self,
        html: str,
        page_type: str,
        element_type: str,
        url: Optional[str] = None
    ) -> Optional[str]:
        """
        Extract element using configured selectors with fallback
        
        Args:
            html: HTML content
            page_type: Type of page (product, category, etc.)
            element_type: Type of element to extract
            url: Optional URL for performance tracking
            
        Returns:
            Extracted value or None
        """
        # Get selectors for this element
        selectors = await self.config_manager.get_selectors(
            self.retailer_config.code,
            page_type,
            element_type
        )
        
        if not selectors:
            logger.warning(f"No selectors configured for {element_type}")
            return None
            
        # Try each selector in priority order
        for selector in selectors:
            start_time = time.time()
            
            try:
                value = await self._extract_with_selector(html, selector)
                
                if value:
                    # Validate value
                    if selector.validate_value(value):
                        # Apply transformation
                        final_value = selector.transform_value(value)
                        
                        # Record success
                        execution_time = int((time.time() - start_time) * 1000)
                        if url:
                            await self.config_manager.record_selector_performance(
                                selector.id,
                                url,
                                success=True,
                                execution_time_ms=execution_time,
                                extracted_value=final_value
                            )
                        
                        return final_value
                    else:
                        logger.debug(f"Value failed validation: {value}")
                        
            except Exception as e:
                # Record failure
                execution_time = int((time.time() - start_time) * 1000)
                if url and selector.id:
                    await self.config_manager.record_selector_performance(
                        selector.id,
                        url,
                        success=False,
                        execution_time_ms=execution_time,
                        error_message=str(e),
                        error_type=type(e).__name__
                    )
                logger.debug(f"Selector failed: {str(e)}")
                
        # All selectors failed - return fallback value if configured
        if selectors and selectors[0].fallback_value:
            return selectors[0].fallback_value
            
        return None
    
    async def _extract_with_selector(
        self,
        html: str,
        selector: Selector
    ) -> Optional[str]:
        """Extract value using a specific selector"""
        
        if selector.selector_type == 'css':
            return self._extract_css(html, selector)
        elif selector.selector_type == 'xpath':
            return self._extract_xpath(html, selector)
        elif selector.selector_type == 'regex':
            return self._extract_regex(html, selector)
        elif selector.selector_type == 'json_path':
            return self._extract_json_path(html, selector)
        else:
            raise ValueError(f"Unknown selector type: {selector.selector_type}")
    
    def _extract_css(self, html: str, selector: Selector) -> Optional[str]:
        """Extract using CSS selector"""
        soup = BeautifulSoup(html, 'html.parser')
        
        # Handle context selector
        if selector.selector_context:
            context = soup.select_one(selector.selector_context)
            if not context:
                return None
            element = context.select_one(selector.selector_value)
        else:
            element = soup.select_one(selector.selector_value)
            
        if element:
            # Extract text or specific attribute
            if selector.selector_value.endswith('::text'):
                return element.get_text(strip=True)
            elif '::attr(' in selector.selector_value:
                # Extract attribute (e.g., "img::attr(src)")
                attr_match = re.search(r'::attr\(([^)]+)\)', selector.selector_value)
                if attr_match:
                    attr_name = attr_match.group(1)
                    return element.get(attr_name)
            else:
                return element.get_text(strip=True)
                
        return None
    
    def _extract_xpath(self, html: str, selector: Selector) -> Optional[str]:
        """Extract using XPath"""
        tree = lxml.html.fromstring(html)
        
        # Handle context
        if selector.selector_context:
            context_nodes = tree.xpath(selector.selector_context)
            if not context_nodes:
                return None
            tree = context_nodes[0]
            
        # Execute XPath
        results = tree.xpath(selector.selector_value)
        
        if results:
            if isinstance(results[0], str):
                return results[0].strip()
            else:
                # Element node - get text
                return results[0].text_content().strip()
                
        return None
    
    def _extract_regex(self, html: str, selector: Selector) -> Optional[str]:
        """Extract using regex"""
        match = re.search(selector.selector_value, html, re.IGNORECASE | re.DOTALL)
        
        if match:
            # Return first capturing group or whole match
            if match.groups():
                return match.group(1).strip()
            else:
                return match.group(0).strip()
                
        return None
    
    def _extract_json_path(self, html: str, selector: Selector) -> Optional[str]:
        """Extract from JSON data in HTML"""
        # Look for JSON in script tags
        soup = BeautifulSoup(html, 'html.parser')
        
        for script in soup.find_all('script', type='application/ld+json'):
            try:
                data = json.loads(script.string)
                
                # Simple JSON path implementation
                path_parts = selector.selector_value.split('.')
                value = data
                
                for part in path_parts:
                    if isinstance(value, dict) and part in value:
                        value = value[part]
                    else:
                        value = None
                        break
                        
                if value is not None:
                    return str(value)
                    
            except json.JSONDecodeError:
                continue
                
        return None
    
    async def extract_product_adaptive(
        self,
        html: str,
        url: str
    ) -> Dict[str, Any]:
        """
        Extract product data using adaptive selectors
        
        Args:
            html: Product page HTML
            url: Product URL
            
        Returns:
            Dictionary of extracted product data
        """
        product_data = {}
        
        # Define extraction mapping
        extraction_map = {
            'product_name': 'name',
            'price': 'current_price',
            'original_price': 'original_price',
            'brand': 'brand',
            'sku': 'sku',
            'availability': 'availability',
            'description': 'description',
            'image': 'image_url',
            'rating': 'rating',
            'review_count': 'review_count'
        }
        
        # Extract each element
        for element_type, field_name in extraction_map.items():
            value = await self.extract_with_fallback(
                html,
                'product',
                element_type,
                url
            )
            
            if value:
                # Type conversion for specific fields
                if element_type in ['price', 'original_price']:
                    # Extract numeric price
                    price_match = re.search(r'[\d,]+\.?\d*', value)
                    if price_match:
                        product_data[field_name] = float(
                            price_match.group(0).replace(',', '')
                        )
                elif element_type == 'rating':
                    # Extract numeric rating
                    rating_match = re.search(r'[\d.]+', value)
                    if rating_match:
                        product_data[field_name] = float(rating_match.group(0))
                elif element_type == 'review_count':
                    # Extract count
                    count_match = re.search(r'\d+', value)
                    if count_match:
                        product_data[field_name] = int(count_match.group(0))
                else:
                    product_data[field_name] = value
                    
        # Add metadata
        product_data['url'] = url
        product_data['retailer_code'] = self.retailer_config.code
        product_data['scraped_at'] = time.strftime('%Y-%m-%d %H:%M:%S')
        
        return product_data
    
    async def extract_category_products_adaptive(
        self,
        html: str,
        category_url: str
    ) -> List[str]:
        """
        Extract product URLs from category page using adaptive selectors
        
        Args:
            html: Category page HTML
            category_url: Category URL
            
        Returns:
            List of product URLs
        """
        # Extract product links
        links_text = await self.extract_with_fallback(
            html,
            'category',
            'product_link',
            category_url
        )
        
        if not links_text:
            return []
            
        # Parse links (assuming selector returns multiple links)
        soup = BeautifulSoup(html, 'html.parser')
        product_urls = []
        
        # Get the selector that worked
        selectors = await self.config_manager.get_selectors(
            self.retailer_config.code,
            'category',
            'product_link'
        )
        
        if selectors:
            selector = selectors[0]  # Use the first (highest priority)
            
            if selector.selector_type == 'css':
                links = soup.select(selector.selector_value)
                for link in links:
                    href = link.get('href')
                    if href:
                        # Make absolute URL
                        if not href.startswith('http'):
                            href = self.retailer_config.base_url.rstrip('/') + '/' + href.lstrip('/')
                        product_urls.append(href)
                        
        return product_urls
    
    async def update_selectors_from_failures(self):
        """
        Analyze failures and update selector priorities
        """
        # Get recent performance data
        selectors = await self.config_manager.get_retailer_config(
            self.retailer_config.code
        )
        
        # Deactivate consistently failing selectors
        await self.config_manager.deactivate_failing_selectors(
            threshold=0.3,  # 30% success rate minimum
            min_uses=10
        )
        
        logger.info(f"Updated selector configuration for {self.retailer_config.code}")