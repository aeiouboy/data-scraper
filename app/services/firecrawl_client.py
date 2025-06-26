"""
Firecrawl API client with rate limiting and retry logic
"""
import asyncio
import httpx
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import logging
from config import get_settings

logger = logging.getLogger(__name__)


class RateLimiter:
    """Simple rate limiter for API calls"""
    
    def __init__(self, calls_per_minute: int = 30):
        self.calls_per_minute = calls_per_minute
        self.calls = []
        self.lock = asyncio.Lock()
    
    async def acquire(self):
        """Wait if necessary to respect rate limits"""
        async with self.lock:
            now = datetime.now()
            # Remove calls older than 1 minute
            self.calls = [call for call in self.calls if now - call < timedelta(minutes=1)]
            
            if len(self.calls) >= self.calls_per_minute:
                # Wait until the oldest call is 1 minute old
                wait_time = 60 - (now - self.calls[0]).total_seconds()
                if wait_time > 0:
                    logger.info(f"Rate limit reached, waiting {wait_time:.1f}s")
                    await asyncio.sleep(wait_time)
                    self.calls.pop(0)
            
            self.calls.append(now)


class FirecrawlClient:
    """Client for Firecrawl API with retry logic and rate limiting"""
    
    def __init__(self, api_key: Optional[str] = None):
        settings = get_settings()
        self.api_key = api_key or settings.firecrawl_api_key
        self.base_url = "https://api.firecrawl.dev/v0"
        self.rate_limiter = RateLimiter(calls_per_minute=30)
        self.client = httpx.AsyncClient(
            headers={"Authorization": f"Bearer {self.api_key}"},
            timeout=30.0
        )
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.client.aclose()
    
    async def scrape(self, url: str, retry_count: int = 3) -> Dict[str, Any]:
        """
        Scrape a single URL with retry logic
        
        Args:
            url: URL to scrape
            retry_count: Number of retries on failure
            
        Returns:
            Scraped data dictionary
        """
        await self.rate_limiter.acquire()
        
        for attempt in range(retry_count):
            try:
                response = await self.client.post(
                    f"{self.base_url}/scrape",
                    json={
                        "url": url,
                        "pageOptions": {
                            "includeHtml": False,
                            "onlyMainContent": True,
                            "screenshot": False,
                            "waitFor": 2000  # Wait for page to load
                        }
                    }
                )
                
                if response.status_code == 200:
                    data = response.json()
                    logger.info(f"Successfully scraped: {url}")
                    scraped_data = data.get("data", {})
                    
                    # Log what we got
                    if scraped_data:
                        logger.debug(f"Raw data keys: {list(scraped_data.keys())}")
                        # Log first 500 chars of markdown to see content
                        markdown = scraped_data.get("markdown", "")
                        if markdown:
                            logger.debug(f"Markdown preview: {markdown[:500]}...")
                    
                    return scraped_data
                elif response.status_code == 429:
                    # Rate limit hit, wait longer
                    wait_time = int(response.headers.get("Retry-After", 60))
                    logger.warning(f"Rate limit hit, waiting {wait_time}s")
                    await asyncio.sleep(wait_time)
                else:
                    logger.error(f"Scrape failed: {response.status_code} - {response.text}")
                    
            except Exception as e:
                logger.error(f"Scrape error attempt {attempt + 1}: {str(e)}")
                if attempt < retry_count - 1:
                    await asyncio.sleep(2 ** attempt)  # Exponential backoff
                else:
                    raise
        
        raise Exception(f"Failed to scrape {url} after {retry_count} attempts")
    
    async def crawl(self, url: str, max_pages: int = 50) -> List[str]:
        """
        Crawl website to discover product URLs
        
        Args:
            url: Starting URL
            max_pages: Maximum pages to crawl
            
        Returns:
            List of discovered URLs
        """
        await self.rate_limiter.acquire()
        
        try:
            response = await self.client.post(
                f"{self.base_url}/crawl",
                json={
                    "url": url,
                    "crawlerOptions": {
                        "includes": ["/product/", "/p/"],  # HomePro product patterns
                        "maxCrawlPages": max_pages
                    }
                }
            )
            
            if response.status_code == 200:
                data = response.json()
                job_id = data.get("jobId")
                
                # Poll for completion
                return await self._poll_crawl_job(job_id)
            else:
                logger.error(f"Crawl failed: {response.status_code}")
                return []
                
        except Exception as e:
            logger.error(f"Crawl error: {str(e)}")
            return []
    
    async def _poll_crawl_job(self, job_id: str, timeout: int = 300) -> List[str]:
        """Poll crawl job status until completion"""
        start_time = datetime.now()
        
        while (datetime.now() - start_time).total_seconds() < timeout:
            await asyncio.sleep(5)  # Check every 5 seconds
            
            try:
                response = await self.client.get(f"{self.base_url}/crawl/status/{job_id}")
                
                if response.status_code == 200:
                    data = response.json()
                    status = data.get("status")
                    
                    if status == "completed":
                        # Handle different response formats
                        crawl_data = data.get("data", [])
                        urls = []
                        logger.info(f"Crawl completed with {len(crawl_data)} items")
                        
                        for item in crawl_data:
                            if isinstance(item, dict):
                                # Log the first item to see structure
                                if not urls:
                                    logger.debug(f"Sample item structure: {list(item.keys())}")
                                # Try different possible keys
                                url = item.get("url") or item.get("sourceUrl") or item.get("link")
                                if url:
                                    urls.append(url)
                            elif isinstance(item, str):
                                urls.append(item)
                        
                        logger.info(f"Extracted {len(urls)} URLs from crawl")
                        return urls
                    elif status == "failed":
                        logger.error(f"Crawl job failed: {job_id}")
                        return []
                        
            except Exception as e:
                logger.error(f"Poll error: {str(e)}")
        
        logger.warning(f"Crawl job timeout: {job_id}")
        return []
    
    async def batch_scrape(self, urls: List[str], max_concurrent: int = 5) -> List[Dict[str, Any]]:
        """
        Scrape multiple URLs concurrently with rate limiting
        
        Args:
            urls: List of URLs to scrape
            max_concurrent: Maximum concurrent requests
            
        Returns:
            List of scraped data
        """
        semaphore = asyncio.Semaphore(max_concurrent)
        
        async def scrape_with_semaphore(url: str) -> Optional[Dict[str, Any]]:
            async with semaphore:
                try:
                    return await self.scrape(url)
                except Exception as e:
                    logger.error(f"Failed to scrape {url}: {str(e)}")
                    return None
        
        tasks = [scrape_with_semaphore(url) for url in urls]
        results = await asyncio.gather(*tasks)
        
        # Filter out None values
        return [r for r in results if r is not None]