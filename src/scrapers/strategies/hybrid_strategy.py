"""
Hybrid strategy that uses native first, then falls back to Firecrawl
"""
import asyncio
from typing import List, Dict, Any, Optional
import logging

from .base_strategy import BaseScrapeStrategy, ScrapeResult
from .native_strategy import NativeStrategy
from .firecrawl_strategy import FirecrawlStrategy

logger = logging.getLogger(__name__)

class HybridStrategy(BaseScrapeStrategy):
    """Hybrid strategy: Native first, Firecrawl fallback"""
    
    def __init__(self, retailer_config: Dict[str, Any] = None):
        super().__init__("hybrid")
        
        # Initialize both strategies
        self.native_strategy = NativeStrategy(retailer_config)
        self.firecrawl_strategy = FirecrawlStrategy()
        
        # Configuration for fallback behavior
        self.config = {
            'native_success_threshold': 0.7,  # If native success rate < 70%, use Firecrawl more
            'native_timeout_threshold': 10.0,  # If native takes >10s, try Firecrawl
            'max_native_failures': 3,  # Max consecutive native failures before switching
            'fallback_probability': 0.2  # 20% chance to use Firecrawl even if native works
        }
        
        # Track performance
        self.consecutive_native_failures = 0
        self.session_stats = {
            'native_attempts': 0,
            'native_successes': 0,
            'firecrawl_attempts': 0,
            'firecrawl_successes': 0,
            'fallback_triggers': 0
        }
    
    def _should_use_firecrawl_first(self, url: str) -> bool:
        """Determine if we should skip native and go directly to Firecrawl"""
        # If native has been failing consistently
        if self.consecutive_native_failures >= self.config['max_native_failures']:
            logger.info(f"Hybrid: Using Firecrawl first due to native failures ({self.consecutive_native_failures})")
            return True
        
        # If native success rate is too low
        native_success_rate = self.native_strategy.get_success_rate()
        if (self.native_strategy.stats['total_requests'] > 5 and 
            native_success_rate < self.config['native_success_threshold'] * 100):
            logger.info(f"Hybrid: Using Firecrawl first due to low native success rate ({native_success_rate:.1f}%)")
            return True
        
        return False
    
    async def scrape_url(self, url: str, **kwargs) -> ScrapeResult:
        """Scrape URL with hybrid approach"""
        # Check if we should use Firecrawl first
        if self._should_use_firecrawl_first(url):
            return await self._scrape_with_firecrawl_first(url, **kwargs)
        else:
            return await self._scrape_with_native_first(url, **kwargs)
    
    async def _scrape_with_native_first(self, url: str, **kwargs) -> ScrapeResult:
        """Try native first, fallback to Firecrawl"""
        self.session_stats['native_attempts'] += 1
        
        # Try native strategy
        logger.debug(f"Hybrid: Trying native for {url}")
        native_result = await self.native_strategy.scrape_url(url, **kwargs)
        
        if native_result.success:
            # Native succeeded
            self.consecutive_native_failures = 0
            self.session_stats['native_successes'] += 1
            
            # Mark as hybrid strategy
            native_result.strategy_used = "hybrid_native"
            self.update_stats(native_result)
            
            logger.info(f"Hybrid: Native success for {url} ({native_result.response_time:.2f}s)")
            return native_result
        
        else:
            # Native failed, try Firecrawl
            self.consecutive_native_failures += 1
            self.session_stats['fallback_triggers'] += 1
            
            logger.warning(f"Hybrid: Native failed for {url}, trying Firecrawl. Error: {native_result.error}")
            return await self._scrape_with_firecrawl_fallback(url, native_result, **kwargs)
    
    async def _scrape_with_firecrawl_first(self, url: str, **kwargs) -> ScrapeResult:
        """Use Firecrawl first (when native is unreliable)"""
        self.session_stats['firecrawl_attempts'] += 1
        
        logger.debug(f"Hybrid: Using Firecrawl first for {url}")
        firecrawl_result = await self.firecrawl_strategy.scrape_url(url, **kwargs)
        
        if firecrawl_result.success:
            self.session_stats['firecrawl_successes'] += 1
            firecrawl_result.strategy_used = "hybrid_firecrawl"
            self.update_stats(firecrawl_result)
            
            logger.info(f"Hybrid: Firecrawl success for {url} ({firecrawl_result.response_time:.2f}s)")
            return firecrawl_result
        
        else:
            # Firecrawl failed, try native as backup
            logger.warning(f"Hybrid: Firecrawl failed for {url}, trying native as backup")
            native_result = await self.native_strategy.scrape_url(url, **kwargs)
            
            if native_result.success:
                self.consecutive_native_failures = 0
                native_result.strategy_used = "hybrid_native_backup"
                self.update_stats(native_result)
                return native_result
            else:
                # Both failed
                self.consecutive_native_failures += 1
                result = ScrapeResult(
                    url=url,
                    success=False,
                    error=f"Both strategies failed. Firecrawl: {firecrawl_result.error}, Native: {native_result.error}",
                    strategy_used="hybrid_failed"
                )
                self.update_stats(result)
                return result
    
    async def _scrape_with_firecrawl_fallback(self, url: str, native_result: ScrapeResult, **kwargs) -> ScrapeResult:
        """Use Firecrawl as fallback after native failure"""
        self.session_stats['firecrawl_attempts'] += 1
        
        firecrawl_result = await self.firecrawl_strategy.scrape_url(url, **kwargs)
        
        if firecrawl_result.success:
            self.session_stats['firecrawl_successes'] += 1
            firecrawl_result.strategy_used = "hybrid_firecrawl_fallback"
            self.update_stats(firecrawl_result)
            
            logger.info(f"Hybrid: Firecrawl fallback success for {url}")
            return firecrawl_result
        
        else:
            # Both strategies failed
            result = ScrapeResult(
                url=url,
                success=False,
                error=f"Both strategies failed. Native: {native_result.error}, Firecrawl: {firecrawl_result.error}",
                strategy_used="hybrid_failed",
                response_time=(native_result.response_time or 0) + (firecrawl_result.response_time or 0)
            )
            self.update_stats(result)
            
            logger.error(f"Hybrid: Both strategies failed for {url}")
            return result
    
    async def scrape_batch(self, urls: List[str], max_concurrent: int = 5, **kwargs) -> List[ScrapeResult]:
        """Scrape multiple URLs with intelligent strategy selection"""
        results = []
        
        # Process in smaller batches to allow strategy adjustment
        batch_size = min(max_concurrent, 3)
        
        for i in range(0, len(urls), batch_size):
            batch_urls = urls[i:i + batch_size]
            
            # Process batch with current strategy preferences
            batch_tasks = [self.scrape_url(url, **kwargs) for url in batch_urls]
            batch_results = await asyncio.gather(*batch_tasks, return_exceptions=True)
            
            # Handle exceptions
            for j, result in enumerate(batch_results):
                if isinstance(result, Exception):
                    error_result = ScrapeResult(
                        url=batch_urls[j],
                        success=False,
                        error=f"Exception during hybrid scraping: {str(result)}",
                        strategy_used="hybrid_exception"
                    )
                    self.update_stats(error_result)
                    results.append(error_result)
                else:
                    results.append(result)
            
            # Log batch progress
            batch_success_rate = sum(1 for r in batch_results if isinstance(r, ScrapeResult) and r.success) / len(batch_results) * 100
            logger.info(f"Hybrid: Batch {i//batch_size + 1} completed. Success rate: {batch_success_rate:.1f}%")
            
            # Small delay between batches
            if i + batch_size < len(urls):
                await asyncio.sleep(1)
        
        return results
    
    async def discover_urls(self, category_url: str, max_pages: int = 5, **kwargs) -> List[str]:
        """Discover URLs using the best available strategy"""
        # Native is generally better for URL discovery due to better HTML parsing
        logger.info(f"Hybrid: Using native strategy for URL discovery from {category_url}")
        
        try:
            urls = await self.native_strategy.discover_urls(category_url, max_pages, **kwargs)
            
            if urls:
                logger.info(f"Hybrid: Native discovery found {len(urls)} URLs")
                return urls
            else:
                # Fallback to Firecrawl if native finds nothing
                logger.info(f"Hybrid: Native found no URLs, trying Firecrawl discovery")
                fallback_urls = await self.firecrawl_strategy.discover_urls(category_url, max_pages, **kwargs)
                logger.info(f"Hybrid: Firecrawl discovery found {len(fallback_urls)} URLs")
                return fallback_urls
                
        except Exception as e:
            logger.error(f"Hybrid: Native discovery failed, trying Firecrawl. Error: {str(e)}")
            try:
                fallback_urls = await self.firecrawl_strategy.discover_urls(category_url, max_pages, **kwargs)
                return fallback_urls
            except Exception as e2:
                logger.error(f"Hybrid: Both discovery strategies failed. Error: {str(e2)}")
                return []
    
    async def close(self):
        """Close both strategies"""
        await self.native_strategy.close()
        await self.firecrawl_strategy.close()
        logger.debug("Hybrid strategy closed")