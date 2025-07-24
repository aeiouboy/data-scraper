"""
Base strategy interface for scraping
"""
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

@dataclass
class ScrapeResult:
    """Result from a scraping operation"""
    url: str
    success: bool
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    strategy_used: Optional[str] = None
    response_time: Optional[float] = None
    scraped_at: datetime = None
    
    def __post_init__(self):
        if self.scraped_at is None:
            self.scraped_at = datetime.now()

class BaseScrapeStrategy(ABC):
    """Base class for scraping strategies"""
    
    def __init__(self, name: str):
        self.name = name
        self.stats = {
            'total_requests': 0,
            'successful_requests': 0,
            'failed_requests': 0,
            'total_response_time': 0.0
        }
    
    @abstractmethod
    async def scrape_url(self, url: str, **kwargs) -> ScrapeResult:
        """Scrape a single URL"""
        pass
    
    @abstractmethod
    async def scrape_batch(self, urls: List[str], max_concurrent: int = 5, **kwargs) -> List[ScrapeResult]:
        """Scrape multiple URLs"""
        pass
    
    @abstractmethod
    async def discover_urls(self, category_url: str, max_pages: int = 5, **kwargs) -> List[str]:
        """Discover product URLs from category page"""
        pass
    
    def update_stats(self, result: ScrapeResult):
        """Update strategy statistics"""
        self.stats['total_requests'] += 1
        if result.success:
            self.stats['successful_requests'] += 1
        else:
            self.stats['failed_requests'] += 1
        
        if result.response_time:
            self.stats['total_response_time'] += result.response_time
    
    def get_success_rate(self) -> float:
        """Get success rate percentage"""
        if self.stats['total_requests'] == 0:
            return 0.0
        return (self.stats['successful_requests'] / self.stats['total_requests']) * 100
    
    def get_avg_response_time(self) -> float:
        """Get average response time"""
        if self.stats['total_requests'] == 0:
            return 0.0
        return self.stats['total_response_time'] / self.stats['total_requests']
    
    def get_stats(self) -> Dict[str, Any]:
        """Get strategy statistics"""
        return {
            'name': self.name,
            'total_requests': self.stats['total_requests'],
            'successful_requests': self.stats['successful_requests'],
            'failed_requests': self.stats['failed_requests'],
            'success_rate': self.get_success_rate(),
            'avg_response_time': self.get_avg_response_time()
        }