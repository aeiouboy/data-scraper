"""
Firecrawl API client with rate limiting and retry logic
"""
import asyncio
import httpx
import re
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import logging
from urllib.parse import quote, unquote, urlparse, urlunparse
from config.app_config import get_settings

logger = logging.getLogger(__name__)


class RateLimiter:
    """Enhanced rate limiter for API calls with adaptive behavior"""
    
    def __init__(self, calls_per_minute: int = 30):
        self.calls_per_minute = calls_per_minute
        self.calls = []
        self.lock = asyncio.Lock()
        self.consecutive_errors = 0
        self.adaptive_delay = 0
    
    async def acquire(self):
        """Wait if necessary to respect rate limits with adaptive behavior"""
        async with self.lock:
            now = datetime.now()
            # Remove calls older than 1 minute
            self.calls = [call for call in self.calls if now - call < timedelta(minutes=1)]
            
            # Apply adaptive delay for error recovery
            if self.adaptive_delay > 0:
                logger.info(f"Adaptive delay: {self.adaptive_delay:.1f}s (due to {self.consecutive_errors} consecutive errors)")
                await asyncio.sleep(self.adaptive_delay)
                self.adaptive_delay = max(0, self.adaptive_delay - 1)  # Gradually reduce
            
            if len(self.calls) >= self.calls_per_minute:
                # Wait until the oldest call is 1 minute old
                wait_time = 60 - (now - self.calls[0]).total_seconds()
                if wait_time > 0:
                    logger.info(f"Rate limit reached, waiting {wait_time:.1f}s")
                    await asyncio.sleep(wait_time)
                    self.calls.pop(0)
            
            self.calls.append(now)
    
    def on_success(self):
        """Called when a request succeeds"""
        if self.consecutive_errors > 0:
            logger.info(f"Request succeeded, resetting error count from {self.consecutive_errors}")
        self.consecutive_errors = 0
        self.adaptive_delay = 0
    
    def on_error(self):
        """Called when a request fails"""
        self.consecutive_errors += 1
        # Exponential backoff: 2^errors seconds, max 30 seconds
        self.adaptive_delay = min(30, 2 ** min(self.consecutive_errors, 5))
        logger.warning(f"Request failed, consecutive errors: {self.consecutive_errors}, adaptive delay: {self.adaptive_delay}s")


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
    
    def _encode_url(self, url: str) -> str:
        """
        Properly encode URL to handle special characters and international text
        """
        try:
            # Parse the URL
            parsed = urlparse(url)
            
            # Encode the path component while preserving slashes
            path_parts = parsed.path.split('/')
            encoded_parts = []
            for part in path_parts:
                if part:
                    # Encode each part, but preserve certain characters
                    encoded_part = quote(part, safe='')
                    encoded_parts.append(encoded_part)
                else:
                    encoded_parts.append(part)
            
            # Reconstruct the path
            encoded_path = '/'.join(encoded_parts)
            
            # Handle query string if present
            query = quote(parsed.query, safe='=&') if parsed.query else ''
            
            # Reconstruct the URL
            encoded_url = urlunparse((
                parsed.scheme,
                parsed.netloc,
                encoded_path,
                parsed.params,
                query,
                parsed.fragment
            ))
            
            logger.info(f"Encoded URL: {url} -> {encoded_url}")
            return encoded_url
            
        except Exception as e:
            logger.warning(f"Failed to encode URL {url}: {e}, using original")
            return url
    
    async def scrape(self, url: str, retry_count: int = 3) -> Dict[str, Any]:
        """
        Scrape a single URL with retry logic
        
        Args:
            url: URL to scrape
            retry_count: Number of retries on failure
            
        Returns:
            Scraped data dictionary
        """
        # Encode URL to handle special characters
        encoded_url = self._encode_url(url)
        
        await self.rate_limiter.acquire()
        
        for attempt in range(retry_count):
            try:
                print(f"      🌐 Firecrawl API call (attempt {attempt + 1}/{retry_count})")
                
                response = await self.client.post(
                    f"{self.base_url}/scrape",
                    json={
                        "url": encoded_url,
                        "pageOptions": {
                            "includeHtml": True,
                            "onlyMainContent": False,
                            "screenshot": False,
                            "waitFor": 5000,  # Wait longer for page to load
                            "removeTags": ["script", "style"]
                        },
                        "formats": ["markdown", "html", "links"]
                    }
                )
                
                if response.status_code == 200:
                    data = response.json()
                    self.rate_limiter.on_success()  # Reset error tracking
                    print(f"      ✅ Firecrawl success!")
                    logger.info(f"Successfully scraped: {url}")
                    scraped_data = data.get("data", {})
                    
                    # Log what we got
                    if scraped_data:
                        logger.debug(f"Raw data keys: {list(scraped_data.keys())}")
                        # Log first 1000 chars of markdown to see content
                        markdown = scraped_data.get("markdown", "")
                        if markdown:
                            logger.debug(f"Markdown length: {len(markdown)} chars")
                    
                    return scraped_data
                elif response.status_code == 429:
                    # Rate limit hit, wait longer
                    wait_time = int(response.headers.get("Retry-After", 60))
                    print(f"      ⏳ Rate limit hit, waiting {wait_time}s")
                    logger.warning(f"Rate limit hit, waiting {wait_time}s")
                    await asyncio.sleep(wait_time)
                else:
                    self.rate_limiter.on_error()  # Track error for adaptive behavior
                    print(f"      ❌ API error: {response.status_code}")
                    logger.error(f"Scrape failed: {response.status_code} - {response.text}")
                    
            except Exception as e:
                self.rate_limiter.on_error()  # Track error for adaptive behavior
                print(f"      ❌ Network error: {str(e)[:50]}...")
                logger.error(f"Scrape error attempt {attempt + 1}: {str(e)}")
                if attempt < retry_count - 1:
                    wait_time = 2 ** attempt
                    print(f"      ⏳ Retrying in {wait_time}s...")
                    await asyncio.sleep(wait_time)  # Exponential backoff
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
        # Encode URL to handle special characters
        encoded_url = self._encode_url(url)
        
        await self.rate_limiter.acquire()
        
        try:
            response = await self.client.post(
                f"{self.base_url}/crawl",
                json={
                    "url": encoded_url,
                    "crawlerOptions": {
                        "includes": ["/p/"],  # HomePro uses /p/ pattern
                        "maxCrawlPages": max_pages,
                        "waitFor": 5000  # Wait for JS
                    },
                    "pageOptions": {
                        "includeHtml": True,
                        "onlyMainContent": False,
                        "removeTags": ["script", "style"]
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
                                    logger.info(f"Sample item structure: {list(item.keys())}")
                                    if "metadata" in item:
                                        logger.info(f"Metadata keys: {list(item['metadata'].keys())}")
                                    if "linksOnPage" in item:
                                        logger.info(f"Number of links: {len(item['linksOnPage'])}")
                                        # Log first few links
                                        for i, link in enumerate(item['linksOnPage'][:5]):
                                            logger.info(f"Sample link {i}: {link}")
                                
                                # Try to get URL from metadata
                                metadata = item.get("metadata", {})
                                url = metadata.get("sourceURL") or metadata.get("url") or item.get("url") or item.get("sourceUrl")
                                
                                if url:
                                    urls.append(url)
                                    logger.info(f"Found URL from metadata: {url}")
                                    
                                # Also extract links from linksOnPage
                                links = item.get("linksOnPage", [])
                                product_links = []
                                
                                for link in links:
                                    if isinstance(link, str):
                                        # HomePro uses /p/[number] pattern for products
                                        if '/p/' in link:
                                            if link.startswith('http'):
                                                product_links.append(link)
                                            elif link.startswith('/'):
                                                product_links.append(f"https://www.homepro.co.th{link}")
                                
                                if product_links:
                                    logger.info(f"Found {len(product_links)} product links from linksOnPage")
                                    urls.extend(product_links)
                                
                                # Also check HTML content for product links
                                html_content = item.get("html", "")
                                if html_content:
                                    # Extract product links from HTML
                                    html_product_links = re.findall(r'href=["\']([^"\']*?/p/\d+[^"\']*?)["\']', html_content)
                                    for link in html_product_links:
                                        if link.startswith('http'):
                                            if link not in urls:
                                                urls.append(link)
                                        elif link.startswith('/'):
                                            full_link = f"https://www.homepro.co.th{link}"
                                            if full_link not in urls:
                                                urls.append(full_link)
                                    
                                    if html_product_links:
                                        logger.info(f"Found {len(html_product_links)} additional product links from HTML")
                                            
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