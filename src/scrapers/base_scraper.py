"""
Base scraper class for standardizing scraper interfaces
"""
from typing import Dict, List, Any, Optional
from abc import ABC, abstractmethod
import logging

logger = logging.getLogger(__name__)


class BaseScraper(ABC):
    """Base class for all retailer scrapers"""
    
    def __init__(self):
        self.retailer_name = self.__class__.__name__.replace('Scraper', '')
    
    async def scrape_category_standardized(self, category_url: str, max_pages: int = 5) -> Dict[str, Any]:
        """
        Standardized category scraping that returns a consistent dict format
        
        Returns:
            Dict with keys: total, success, failed, products
        """
        try:
            # Call the original scrape_category method
            result = await self.scrape_category(category_url, max_pages)
            
            # If result is already a dict with the expected format, return it
            if isinstance(result, dict) and all(key in result for key in ['total', 'success', 'failed']):
                return result
            
            # If result is a list of products, convert to standard format
            if isinstance(result, list):
                products = result
                success_count = len([p for p in products if p is not None])
                
                return {
                    'total': len(products),
                    'success': success_count,
                    'failed': len(products) - success_count,
                    'products': products,
                    'category_url': category_url
                }
            
            # If result is something else, try to extract meaningful data
            logger.warning(f"Unexpected result type from {self.retailer_name}: {type(result)}")
            return {
                'total': 0,
                'success': 0,
                'failed': 0,
                'products': [],
                'category_url': category_url,
                'error': f'Unexpected result type: {type(result)}'
            }
            
        except Exception as e:
            logger.error(f"Error in {self.retailer_name} scrape_category: {str(e)}")
            return {
                'total': 0,
                'success': 0,
                'failed': 0,
                'products': [],
                'category_url': category_url,
                'error': str(e)
            }
    
    @abstractmethod
    async def scrape_category(self, category_url: str, max_pages: int = 5):
        """Each scraper must implement this method"""
        pass
    
    @abstractmethod
    async def scrape_product(self, product_url: str):
        """Each scraper must implement this method"""
        pass