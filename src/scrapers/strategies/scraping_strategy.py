"""
Abstract base class for scraping strategies
"""
from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from datetime import datetime


@dataclass
class ScrapeResult:
    """Standardized result from scraping operations"""
    url: str
    success: bool
    data: Dict[str, Any]
    error: Optional[str] = None
    response_time: float = 0.0
    strategy_used: str = "unknown"
    retry_count: int = 0
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


class ScrapingStrategy(ABC):
    """Abstract base class for all scraping strategies"""
    
    def __init__(self, retailer_config: Dict[str, Any]):
        self.retailer_config = retailer_config
        self.retailer_code = retailer_config.get('code', 'unknown')
        self.strategy_name = self.__class__.__name__
        
        # Performance tracking
        self.stats = {
            'total_requests': 0,
            'successful_requests': 0,
            'failed_requests': 0,
            'average_response_time': 0.0,
            'total_response_time': 0.0,
            'created_at': datetime.now().isoformat()
        }
    
    @abstractmethod
    async def scrape_product(self, product_url: str) -> ScrapeResult:
        """
        Scrape a single product page
        
        Args:
            product_url: URL of the product page
            
        Returns:
            ScrapeResult with product data
        """
        pass
    
    @abstractmethod
    async def scrape_category(self, category_url: str, max_pages: int = 5) -> ScrapeResult:
        """
        Scrape a category page to get product listings
        
        Args:
            category_url: URL of the category page
            max_pages: Maximum number of pages to scrape
            
        Returns:
            ScrapeResult with category data and product URLs
        """
        pass
    
    @abstractmethod
    async def scrape_search(self, search_query: str, max_pages: int = 5) -> ScrapeResult:
        """
        Scrape search results
        
        Args:
            search_query: Search query string
            max_pages: Maximum number of pages to scrape
            
        Returns:
            ScrapeResult with search results
        """
        pass
    
    async def scrape_multiple_products(self, product_urls: List[str]) -> List[ScrapeResult]:
        """
        Scrape multiple product pages concurrently
        
        Args:
            product_urls: List of product URLs to scrape
            
        Returns:
            List of ScrapeResult objects
        """
        results = []
        
        # Default implementation - override for better concurrency
        for url in product_urls:
            result = await self.scrape_product(url)
            results.append(result)
        
        return results
    
    async def scrape_category_with_pagination(self, category_url: str, max_pages: int = 5) -> List[ScrapeResult]:
        """
        Scrape category with automatic pagination handling
        
        Args:
            category_url: URL of the category page
            max_pages: Maximum number of pages to scrape
            
        Returns:
            List of ScrapeResult objects, one per page
        """
        results = []
        
        # Start with the first page
        result = await self.scrape_category(category_url, max_pages=1)
        results.append(result)
        
        if not result.success:
            return results
        
        # Check for pagination
        pagination_info = result.data.get('pagination', {})
        next_page_url = pagination_info.get('next_page_url')
        
        page_count = 1
        while next_page_url and page_count < max_pages:
            page_result = await self.scrape_category(next_page_url, max_pages=1)
            results.append(page_result)
            
            if not page_result.success:
                break
            
            # Get next page URL
            next_pagination = page_result.data.get('pagination', {})
            next_page_url = next_pagination.get('next_page_url')
            page_count += 1
        
        return results
    
    def update_stats(self, success: bool, response_time: float):
        """Update strategy statistics"""
        self.stats['total_requests'] += 1
        self.stats['total_response_time'] += response_time
        
        if success:
            self.stats['successful_requests'] += 1
        else:
            self.stats['failed_requests'] += 1
        
        # Update average response time
        self.stats['average_response_time'] = (
            self.stats['total_response_time'] / self.stats['total_requests']
        )
    
    def get_stats(self) -> Dict[str, Any]:
        """Get strategy statistics"""
        stats = self.stats.copy()
        
        # Add calculated metrics
        total_requests = stats['total_requests']
        if total_requests > 0:
            stats['success_rate'] = stats['successful_requests'] / total_requests
            stats['failure_rate'] = stats['failed_requests'] / total_requests
        else:
            stats['success_rate'] = 0.0
            stats['failure_rate'] = 0.0
        
        stats['strategy_name'] = self.strategy_name
        stats['retailer_code'] = self.retailer_code
        
        return stats
    
    def reset_stats(self):
        """Reset strategy statistics"""
        self.stats = {
            'total_requests': 0,
            'successful_requests': 0,
            'failed_requests': 0,
            'average_response_time': 0.0,
            'total_response_time': 0.0,
            'created_at': datetime.now().isoformat()
        }
    
    def get_strategy_info(self) -> Dict[str, Any]:
        """Get information about this strategy"""
        return {
            'name': self.strategy_name,
            'retailer_code': self.retailer_code,
            'retailer_config': self.retailer_config,
            'stats': self.get_stats()
        }
    
    @abstractmethod
    async def close(self):
        """Clean up strategy resources"""
        pass
    
    def __repr__(self) -> str:
        return f"{self.strategy_name}(retailer={self.retailer_code})"