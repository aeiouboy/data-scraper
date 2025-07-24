"""
Firecrawl API strategy (existing functionality)
"""
import time
from typing import List, Dict, Any, Optional
import logging

from .base_strategy import BaseScrapeStrategy, ScrapeResult
from src.services.firecrawl_client import FirecrawlClient

logger = logging.getLogger(__name__)

class FirecrawlStrategy(BaseScrapeStrategy):
    """Firecrawl API strategy using existing client"""
    
    def __init__(self):
        super().__init__("firecrawl")
        self.client = None
    
    async def _get_client(self) -> FirecrawlClient:
        """Get or create Firecrawl client"""
        if self.client is None:
            self.client = FirecrawlClient()
        return self.client
    
    async def scrape_url(self, url: str, **kwargs) -> ScrapeResult:
        """Scrape a single URL using Firecrawl API"""
        start_time = time.time()
        
        try:
            client = await self._get_client()
            
            # Use existing Firecrawl client method
            async with client:
                raw_data = await client.scrape(url)
            
            response_time = time.time() - start_time
            
            if raw_data:
                # Process Firecrawl response
                data = self._process_firecrawl_data(raw_data, url)
                
                result = ScrapeResult(
                    url=url,
                    success=True,
                    data=data,
                    strategy_used="firecrawl",
                    response_time=response_time
                )
                self.update_stats(result)
                return result
            else:
                result = ScrapeResult(
                    url=url,
                    success=False,
                    error="Firecrawl returned no data",
                    strategy_used="firecrawl",
                    response_time=response_time
                )
                self.update_stats(result)
                return result
                
        except Exception as e:
            response_time = time.time() - start_time
            result = ScrapeResult(
                url=url,
                success=False,
                error=f"Firecrawl error: {str(e)}",
                strategy_used="firecrawl",
                response_time=response_time
            )
            self.update_stats(result)
            return result
    
    def _process_firecrawl_data(self, raw_data: Dict[str, Any], url: str) -> Dict[str, Any]:
        """Process raw Firecrawl data into standard format"""
        data = {
            'url': url,
            'strategy': 'firecrawl'
        }
        
        # Extract metadata from Firecrawl response
        metadata = raw_data.get('metadata', {})
        if metadata:
            data['title'] = metadata.get('title', '')
            data['meta_description'] = metadata.get('description', '')
        
        # Extract markdown content
        markdown = raw_data.get('markdown', '')
        if markdown:
            data['markdown'] = markdown
            data['content_length'] = len(markdown)
        
        # Extract HTML content
        html = raw_data.get('content', '')
        if html:
            data['html'] = html
            if 'content_length' not in data:
                data['content_length'] = len(html)
        
        # Detect page type based on URL
        data['page_type'] = self._detect_page_type(url)
        
        # Extract structured data if available
        if 'structuredData' in raw_data:
            data['structured_data'] = raw_data['structuredData']
        
        return data
    
    def _detect_page_type(self, url: str) -> str:
        """Detect page type from URL"""
        if '/p/' in url or '/product/' in url:
            return 'product'
        elif '/c/' in url or '/category/' in url:
            return 'category'
        elif url.rstrip('/').endswith(('homepro.co.th', 'homepro.co.th/th')):
            return 'homepage'
        elif '/search' in url:
            return 'search'
        return 'other'
    
    async def scrape_batch(self, urls: List[str], max_concurrent: int = 5, **kwargs) -> List[ScrapeResult]:
        """Scrape multiple URLs using Firecrawl batch API"""
        try:
            client = await self._get_client()
            
            async with client:
                # Use existing batch scrape method
                raw_results = await client.batch_scrape(urls, max_concurrent)
            
            results = []
            for i, raw_data in enumerate(raw_results):
                url = urls[i] if i < len(urls) else f"unknown_url_{i}"
                
                if raw_data:
                    data = self._process_firecrawl_data(raw_data, url)
                    result = ScrapeResult(
                        url=url,
                        success=True,
                        data=data,
                        strategy_used="firecrawl"
                    )
                else:
                    result = ScrapeResult(
                        url=url,
                        success=False,
                        error="Firecrawl batch returned no data",
                        strategy_used="firecrawl"
                    )
                
                self.update_stats(result)
                results.append(result)
            
            return results
            
        except Exception as e:
            logger.error(f"Firecrawl batch scrape error: {str(e)}")
            # Return failed results for all URLs
            results = []
            for url in urls:
                result = ScrapeResult(
                    url=url,
                    success=False,
                    error=f"Firecrawl batch error: {str(e)}",
                    strategy_used="firecrawl"
                )
                self.update_stats(result)
                results.append(result)
            
            return results
    
    async def discover_urls(self, category_url: str, max_pages: int = 5, **kwargs) -> List[str]:
        """Discover URLs using Firecrawl - limited capability"""
        # Firecrawl doesn't have built-in URL discovery
        # We need to scrape the category page and extract links
        try:
            result = await self.scrape_url(category_url)
            
            if result.success and result.data:
                # Try to extract product links from the scraped content
                # This is basic - native strategy is better for discovery
                html = result.data.get('html', '')
                markdown = result.data.get('markdown', '')
                
                # Simple URL extraction from content
                import re
                product_urls = []
                
                # Look for product URLs in HTML
                if html:
                    product_pattern = r'href=["\']([^"\']*(?:/p/|/product/)[^"\']*)["\']'
                    matches = re.findall(product_pattern, html)
                    product_urls.extend(matches)
                
                # Clean and deduplicate URLs
                base_url = category_url.split('/')[0] + '//' + category_url.split('/')[2]
                cleaned_urls = []
                for url in product_urls:
                    if url.startswith('/'):
                        url = base_url + url
                    if url not in cleaned_urls:
                        cleaned_urls.append(url)
                
                logger.info(f"Firecrawl: Discovered {len(cleaned_urls)} URLs from {category_url}")
                return cleaned_urls[:50]  # Limit to 50
            
            return []
            
        except Exception as e:
            logger.error(f"Firecrawl: URL discovery error for {category_url}: {str(e)}")
            return []
    
    async def close(self):
        """Close the Firecrawl client"""
        if self.client:
            # Firecrawl client doesn't need explicit closing in our implementation
            self.client = None
            logger.debug("Firecrawl strategy closed")