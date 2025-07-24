"""
Base scraper class for standardizing scraper interfaces with strategy support
"""
from typing import Dict, List, Any, Optional, Union
from abc import ABC, abstractmethod
import logging

from .strategy_factory import StrategyFactory, StrategyManager
from .strategies.scraping_strategy import ScrapingStrategy, ScrapeResult
from ..config.retailers import RetailerConfig

logger = logging.getLogger(__name__)


class BaseScraper(ABC):
    """Base class for all retailer scrapers with strategy support"""
    
    def __init__(self, retailer_config: Optional[Union[RetailerConfig, Dict[str, Any]]] = None):
        self.retailer_name = self.__class__.__name__.replace('Scraper', '')
        
        # Strategy-based scraping
        self.strategy: Optional[ScrapingStrategy] = None
        self.strategy_manager = StrategyManager()
        
        # Initialize strategy if config provided
        if retailer_config:
            self.strategy = StrategyFactory.create_strategy(retailer_config)
            logger.info(f"Initialized {self.retailer_name} with {self.strategy.strategy_name} strategy")
    
    async def scrape_category_standardized(self, category_url: str, max_pages: int = 5) -> Dict[str, Any]:
        """
        Standardized category scraping that returns a consistent dict format
        
        Returns:
            Dict with keys: total, success, failed, products
        """
        try:
            # Use strategy if available
            if self.strategy:
                result = await self.strategy.scrape_category(category_url, max_pages)
                return self._convert_strategy_result_to_legacy_format(result, 'category')
            
            # Fall back to original implementation
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
    
    async def scrape_product_standardized(self, product_url: str) -> Dict[str, Any]:
        """
        Standardized product scraping using strategy
        
        Returns:
            Dict with product data or error information
        """
        try:
            # Use strategy if available
            if self.strategy:
                result = await self.strategy.scrape_product(product_url)
                return self._convert_strategy_result_to_legacy_format(result, 'product')
            
            # Fall back to original implementation
            result = await self.scrape_product(product_url)
            
            # Ensure result is a dict
            if not isinstance(result, dict):
                logger.warning(f"Product scraping returned non-dict result: {type(result)}")
                return {
                    'url': product_url,
                    'error': f'Unexpected result type: {type(result)}',
                    'success': False
                }
            
            # Add success flag if not present
            if 'success' not in result:
                result['success'] = bool(result.get('name') or result.get('title'))
            
            return result
            
        except Exception as e:
            logger.error(f"Error in {self.retailer_name} scrape_product: {str(e)}")
            return {
                'url': product_url,
                'error': str(e),
                'success': False
            }
    
    async def scrape_search_standardized(self, search_query: str, max_pages: int = 5) -> Dict[str, Any]:
        """
        Standardized search scraping using strategy
        
        Returns:
            Dict with search results
        """
        try:
            # Use strategy if available
            if self.strategy:
                result = await self.strategy.scrape_search(search_query, max_pages)
                return self._convert_strategy_result_to_legacy_format(result, 'search')
            
            # Fall back to original implementation if exists
            if hasattr(self, 'scrape_search'):
                result = await self.scrape_search(search_query, max_pages)
                return result
            
            # No search implementation available
            return {
                'search_query': search_query,
                'error': 'Search not implemented',
                'success': False,
                'product_urls': []
            }
            
        except Exception as e:
            logger.error(f"Error in {self.retailer_name} scrape_search: {str(e)}")
            return {
                'search_query': search_query,
                'error': str(e),
                'success': False,
                'product_urls': []
            }
    
    def _convert_strategy_result_to_legacy_format(self, result: ScrapeResult, scrape_type: str) -> Dict[str, Any]:
        """Convert strategy result to legacy format"""
        if scrape_type == 'category':
            if result.success:
                product_urls = result.data.get('product_urls', [])
                return {
                    'total': len(product_urls),
                    'success': len(product_urls),
                    'failed': 0,
                    'products': product_urls,
                    'category_url': result.url,
                    'strategy_used': result.strategy_used,
                    'response_time': result.response_time
                }
            else:
                return {
                    'total': 0,
                    'success': 0,
                    'failed': 1,
                    'products': [],
                    'category_url': result.url,
                    'error': result.error,
                    'strategy_used': result.strategy_used,
                    'response_time': result.response_time
                }
        
        elif scrape_type == 'product':
            legacy_result = result.data.copy() if result.success else {}
            legacy_result.update({
                'url': result.url,
                'success': result.success,
                'strategy_used': result.strategy_used,
                'response_time': result.response_time
            })
            
            if result.error:
                legacy_result['error'] = result.error
            
            return legacy_result
        
        elif scrape_type == 'search':
            if result.success:
                return {
                    'search_query': result.data.get('search_query', ''),
                    'success': True,
                    'product_urls': result.data.get('product_urls', []),
                    'total_results': result.data.get('total_results', 0),
                    'strategy_used': result.strategy_used,
                    'response_time': result.response_time
                }
            else:
                return {
                    'search_query': result.url,
                    'success': False,
                    'product_urls': [],
                    'total_results': 0,
                    'error': result.error,
                    'strategy_used': result.strategy_used,
                    'response_time': result.response_time
                }
        
        return {'error': f'Unknown scrape type: {scrape_type}'}
    
    def set_strategy(self, strategy: ScrapingStrategy):
        """Set the scraping strategy"""
        self.strategy = strategy
        logger.info(f"Set {strategy.strategy_name} strategy for {self.retailer_name}")
    
    def get_strategy_info(self) -> Dict[str, Any]:
        """Get information about the current strategy"""
        if self.strategy:
            return self.strategy.get_strategy_info()
        return {'strategy': 'None', 'retailer': self.retailer_name}
    
    def get_strategy_stats(self) -> Dict[str, Any]:
        """Get statistics from the current strategy"""
        if self.strategy:
            return self.strategy.get_stats()
        return {}
    
    async def close_strategy(self):
        """Close the current strategy"""
        if self.strategy:
            await self.strategy.close()
            logger.info(f"Closed strategy for {self.retailer_name}")
    
    # Abstract methods for backward compatibility
    @abstractmethod
    async def scrape_category(self, category_url: str, max_pages: int = 5):
        """Each scraper must implement this method"""
        pass
    
    @abstractmethod
    async def scrape_product(self, product_url: str):
        """Each scraper must implement this method"""
        pass
    
    # Optional methods
    async def scrape_search(self, search_query: str, max_pages: int = 5):
        """Optional search implementation"""
        raise NotImplementedError("Search not implemented for this scraper")
    
    def __repr__(self) -> str:
        strategy_name = self.strategy.strategy_name if self.strategy else "None"
        return f"{self.retailer_name}Scraper(strategy={strategy_name})"