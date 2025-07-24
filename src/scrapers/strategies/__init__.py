"""
Scraping strategies for hybrid native/Firecrawl approach
"""
from .base_strategy import BaseScrapeStrategy, ScrapeResult
from .native_strategy import NativeStrategy
from .firecrawl_strategy import FirecrawlStrategy
from .hybrid_strategy import HybridStrategy

__all__ = [
    'BaseScrapeStrategy',
    'ScrapeResult',
    'NativeStrategy', 
    'FirecrawlStrategy',
    'HybridStrategy'
]