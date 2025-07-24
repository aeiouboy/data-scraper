"""
Native web scraping engine for cost-effective product data extraction
"""
import asyncio
import logging
from typing import Dict, List, Any, Optional, Union
from dataclasses import dataclass
from urllib.parse import urljoin, urlparse
import aiohttp
from bs4 import BeautifulSoup
import re
import json
from datetime import datetime

from .browser_session_manager import BrowserSessionManager
from .rate_limiter import RateLimiter
from .html_parser import HTMLParser

logger = logging.getLogger(__name__)


@dataclass
class ScrapeResult:
    """Standardized result from native scraping"""
    url: str
    success: bool
    data: Dict[str, Any]
    error: Optional[str] = None
    response_time: float = 0.0
    status_code: Optional[int] = None
    retry_count: int = 0


class NativeScraperEngine:
    """Core native scraping engine with browser simulation and intelligent parsing"""
    
    def __init__(self, retailer_config: Dict[str, Any]):
        self.retailer_config = retailer_config
        self.retailer_code = retailer_config.get('code', 'unknown')
        self.base_url = retailer_config.get('base_url', '')
        
        # Initialize components
        self.session_manager = BrowserSessionManager()
        self.rate_limiter = RateLimiter(
            delay=retailer_config.get('rate_limit_delay', 1.0),
            max_concurrent=retailer_config.get('max_concurrent', 5)
        )
        self.html_parser = HTMLParser()
        
        # Scraping configuration
        self.max_retries = retailer_config.get('retry_attempts', 3)
        self.timeout = retailer_config.get('timeout', 30)
        self.selectors = retailer_config.get('selectors', {})
        
        # Statistics
        self.stats = {
            'total_requests': 0,
            'successful_requests': 0,
            'failed_requests': 0,
            'average_response_time': 0.0,
            'last_request_time': None
        }
    
    async def scrape_url(self, url: str, scrape_type: str = 'product') -> ScrapeResult:
        """
        Scrape a single URL with retry logic and error handling
        
        Args:
            url: URL to scrape
            scrape_type: Type of scraping ('product', 'category', 'search')
            
        Returns:
            ScrapeResult with scraped data or error information
        """
        start_time = asyncio.get_event_loop().time()
        retry_count = 0
        last_error = None
        
        # Apply rate limiting
        await self.rate_limiter.acquire()
        
        while retry_count <= self.max_retries:
            try:
                # Get browser session
                session = await self.session_manager.get_session()
                headers = self.session_manager.get_headers()
                
                # Make request
                async with session.get(
                    url,
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=self.timeout)
                ) as response:
                    response_time = asyncio.get_event_loop().time() - start_time
                    
                    # Check response status
                    if response.status == 200:
                        html_content = await response.text()
                        
                        # Parse content based on scrape type
                        if scrape_type == 'product':
                            data = await self._parse_product_page(html_content, url)
                        elif scrape_type == 'category':
                            data = await self._parse_category_page(html_content, url)
                        elif scrape_type == 'search':
                            data = await self._parse_search_page(html_content, url)
                        else:
                            data = await self._parse_generic_page(html_content, url)
                        
                        # Update statistics
                        self._update_stats(True, response_time)
                        
                        return ScrapeResult(
                            url=url,
                            success=True,
                            data=data,
                            response_time=response_time,
                            status_code=response.status,
                            retry_count=retry_count
                        )
                    
                    elif response.status == 429:  # Rate limited
                        await self._handle_rate_limit(response)
                        retry_count += 1
                        continue
                    
                    elif response.status in [403, 404, 410]:  # Permanent errors
                        error_msg = f"HTTP {response.status} - {url}"
                        self._update_stats(False, response_time)
                        
                        return ScrapeResult(
                            url=url,
                            success=False,
                            data={},
                            error=error_msg,
                            response_time=response_time,
                            status_code=response.status,
                            retry_count=retry_count
                        )
                    
                    else:  # Other HTTP errors - retry
                        last_error = f"HTTP {response.status}"
                        retry_count += 1
                        await asyncio.sleep(2 ** retry_count)  # Exponential backoff
                        continue
                        
            except aiohttp.ClientError as e:
                last_error = f"Client error: {str(e)}"
                retry_count += 1
                await asyncio.sleep(2 ** retry_count)
                continue
                
            except asyncio.TimeoutError:
                last_error = "Request timeout"
                retry_count += 1
                await asyncio.sleep(2 ** retry_count)
                continue
                
            except Exception as e:
                last_error = f"Unexpected error: {str(e)}"
                logger.error(f"Unexpected error scraping {url}: {str(e)}")
                break
        
        # All retries failed
        response_time = asyncio.get_event_loop().time() - start_time
        self._update_stats(False, response_time)
        
        return ScrapeResult(
            url=url,
            success=False,
            data={},
            error=last_error or "Max retries exceeded",
            response_time=response_time,
            retry_count=retry_count
        )
    
    async def scrape_multiple_urls(self, urls: List[str], scrape_type: str = 'product') -> List[ScrapeResult]:
        """
        Scrape multiple URLs concurrently with proper rate limiting
        
        Args:
            urls: List of URLs to scrape
            scrape_type: Type of scraping for all URLs
            
        Returns:
            List of ScrapeResult objects
        """
        semaphore = asyncio.Semaphore(self.rate_limiter.max_concurrent)
        
        async def scrape_with_semaphore(url: str) -> ScrapeResult:
            async with semaphore:
                return await self.scrape_url(url, scrape_type)
        
        # Create tasks for all URLs
        tasks = [scrape_with_semaphore(url) for url in urls]
        
        # Execute with progress tracking
        results = []
        for i, task in enumerate(asyncio.as_completed(tasks)):
            result = await task
            results.append(result)
            
            # Log progress
            if (i + 1) % 10 == 0:
                logger.info(f"Completed {i + 1}/{len(urls)} URLs for {self.retailer_code}")
        
        return results
    
    async def _parse_product_page(self, html_content: str, url: str) -> Dict[str, Any]:
        """Parse product page HTML content"""
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Extract basic product information
            product_data = {
                'url': url,
                'scraped_at': datetime.now().isoformat(),
                'retailer_code': self.retailer_code,
                'name': self._extract_product_name(soup),
                'price': self._extract_price(soup),
                'brand': self._extract_brand(soup),
                'sku': self._extract_sku(soup),
                'category': self._extract_category(soup),
                'description': self._extract_description(soup),
                'specifications': self._extract_specifications(soup),
                'images': self._extract_images(soup, url),
                'availability': self._extract_availability(soup),
                'rating': self._extract_rating(soup),
                'reviews_count': self._extract_reviews_count(soup)
            }
            
            # Clean and validate data
            product_data = self._clean_product_data(product_data)
            
            return product_data
            
        except Exception as e:
            logger.error(f"Error parsing product page {url}: {str(e)}")
            return {'error': str(e), 'url': url}
    
    async def _parse_category_page(self, html_content: str, url: str) -> Dict[str, Any]:
        """Parse category page HTML content"""
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Extract category information
            category_data = {
                'url': url,
                'scraped_at': datetime.now().isoformat(),
                'retailer_code': self.retailer_code,
                'category_name': self._extract_category_name(soup),
                'product_urls': self._extract_product_urls(soup, url),
                'pagination': self._extract_pagination_info(soup, url),
                'total_products': self._extract_total_products(soup),
                'filters': self._extract_filters(soup)
            }
            
            return category_data
            
        except Exception as e:
            logger.error(f"Error parsing category page {url}: {str(e)}")
            return {'error': str(e), 'url': url}
    
    async def _parse_search_page(self, html_content: str, url: str) -> Dict[str, Any]:
        """Parse search results page HTML content"""
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Extract search results
            search_data = {
                'url': url,
                'scraped_at': datetime.now().isoformat(),
                'retailer_code': self.retailer_code,
                'search_term': self._extract_search_term(soup, url),
                'results_count': self._extract_results_count(soup),
                'product_urls': self._extract_product_urls(soup, url),
                'pagination': self._extract_pagination_info(soup, url),
                'suggestions': self._extract_search_suggestions(soup)
            }
            
            return search_data
            
        except Exception as e:
            logger.error(f"Error parsing search page {url}: {str(e)}")
            return {'error': str(e), 'url': url}
    
    async def _parse_generic_page(self, html_content: str, url: str) -> Dict[str, Any]:
        """Parse generic page HTML content"""
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Extract basic page information
            page_data = {
                'url': url,
                'scraped_at': datetime.now().isoformat(),
                'retailer_code': self.retailer_code,
                'title': self._extract_page_title(soup),
                'content': self._extract_page_content(soup),
                'links': self._extract_links(soup, url),
                'meta_description': self._extract_meta_description(soup)
            }
            
            return page_data
            
        except Exception as e:
            logger.error(f"Error parsing generic page {url}: {str(e)}")
            return {'error': str(e), 'url': url}
    
    def _extract_product_name(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract product name using configured selectors"""
        selectors = self.selectors.get('product_name', [])
        return self.html_parser.extract_text_by_selectors(soup, selectors)
    
    def _extract_price(self, soup: BeautifulSoup) -> Optional[float]:
        """Extract product price using configured selectors"""
        selectors = self.selectors.get('price', [])
        price_text = self.html_parser.extract_text_by_selectors(soup, selectors)
        if price_text:
            return self.html_parser.parse_price(price_text)
        return None
    
    def _extract_brand(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract product brand using configured selectors"""
        selectors = self.selectors.get('brand', [])
        return self.html_parser.extract_text_by_selectors(soup, selectors)
    
    def _extract_sku(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract product SKU using configured selectors"""
        selectors = self.selectors.get('sku', [])
        return self.html_parser.extract_text_by_selectors(soup, selectors)
    
    def _extract_category(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract product category using configured selectors"""
        selectors = self.selectors.get('category', [])
        return self.html_parser.extract_text_by_selectors(soup, selectors)
    
    def _extract_description(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract product description using configured selectors"""
        selectors = self.selectors.get('description', [])
        return self.html_parser.extract_text_by_selectors(soup, selectors)
    
    def _extract_specifications(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """Extract product specifications using configured selectors"""
        selectors = self.selectors.get('specifications', [])
        return self.html_parser.extract_specifications(soup, selectors)
    
    def _extract_images(self, soup: BeautifulSoup, base_url: str) -> List[str]:
        """Extract product images using configured selectors"""
        selectors = self.selectors.get('images', [])
        return self.html_parser.extract_images(soup, selectors, base_url)
    
    def _extract_availability(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract product availability using configured selectors"""
        selectors = self.selectors.get('availability', [])
        return self.html_parser.extract_text_by_selectors(soup, selectors)
    
    def _extract_rating(self, soup: BeautifulSoup) -> Optional[float]:
        """Extract product rating using configured selectors"""
        selectors = self.selectors.get('rating', [])
        rating_text = self.html_parser.extract_text_by_selectors(soup, selectors)
        if rating_text:
            return self.html_parser.parse_rating(rating_text)
        return None
    
    def _extract_reviews_count(self, soup: BeautifulSoup) -> Optional[int]:
        """Extract reviews count using configured selectors"""
        selectors = self.selectors.get('reviews_count', [])
        count_text = self.html_parser.extract_text_by_selectors(soup, selectors)
        if count_text:
            return self.html_parser.parse_number(count_text)
        return None
    
    def _extract_category_name(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract category name using configured selectors"""
        selectors = self.selectors.get('category_name', [])
        return self.html_parser.extract_text_by_selectors(soup, selectors)
    
    def _extract_product_urls(self, soup: BeautifulSoup, base_url: str) -> List[str]:
        """Extract product URLs from listing pages"""
        selectors = self.selectors.get('product_links', [])
        return self.html_parser.extract_links(soup, selectors, base_url)
    
    def _extract_pagination_info(self, soup: BeautifulSoup, base_url: str) -> Dict[str, Any]:
        """Extract pagination information"""
        selectors = self.selectors.get('pagination', [])
        return self.html_parser.extract_pagination(soup, selectors, base_url)
    
    def _extract_total_products(self, soup: BeautifulSoup) -> Optional[int]:
        """Extract total products count"""
        selectors = self.selectors.get('total_products', [])
        count_text = self.html_parser.extract_text_by_selectors(soup, selectors)
        if count_text:
            return self.html_parser.parse_number(count_text)
        return None
    
    def _extract_filters(self, soup: BeautifulSoup) -> List[Dict[str, Any]]:
        """Extract available filters"""
        selectors = self.selectors.get('filters', [])
        return self.html_parser.extract_filters(soup, selectors)
    
    def _extract_search_term(self, soup: BeautifulSoup, url: str) -> Optional[str]:
        """Extract search term from URL or page"""
        # Try URL parameters first
        from urllib.parse import parse_qs, urlparse
        parsed_url = urlparse(url)
        query_params = parse_qs(parsed_url.query)
        
        # Common search parameter names
        search_params = ['q', 'query', 'search', 'keyword', 'term']
        for param in search_params:
            if param in query_params:
                return query_params[param][0]
        
        # Try page selectors
        selectors = self.selectors.get('search_term', [])
        return self.html_parser.extract_text_by_selectors(soup, selectors)
    
    def _extract_results_count(self, soup: BeautifulSoup) -> Optional[int]:
        """Extract search results count"""
        selectors = self.selectors.get('results_count', [])
        count_text = self.html_parser.extract_text_by_selectors(soup, selectors)
        if count_text:
            return self.html_parser.parse_number(count_text)
        return None
    
    def _extract_search_suggestions(self, soup: BeautifulSoup) -> List[str]:
        """Extract search suggestions"""
        selectors = self.selectors.get('search_suggestions', [])
        return self.html_parser.extract_text_list(soup, selectors)
    
    def _extract_page_title(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract page title"""
        title_tag = soup.find('title')
        return title_tag.get_text().strip() if title_tag else None
    
    def _extract_page_content(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract main page content"""
        # Remove scripts and styles
        for script in soup(["script", "style"]):
            script.decompose()
        
        # Get main content
        main_content = soup.get_text()
        return ' '.join(main_content.split())
    
    def _extract_links(self, soup: BeautifulSoup, base_url: str) -> List[str]:
        """Extract all links from page"""
        links = []
        for link in soup.find_all('a', href=True):
            href = link['href']
            full_url = urljoin(base_url, href)
            links.append(full_url)
        return links
    
    def _extract_meta_description(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract meta description"""
        meta_desc = soup.find('meta', attrs={'name': 'description'})
        return meta_desc.get('content') if meta_desc else None
    
    def _clean_product_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Clean and validate product data"""
        # Remove None values
        cleaned_data = {k: v for k, v in data.items() if v is not None}
        
        # Validate required fields
        required_fields = ['name', 'price']
        for field in required_fields:
            if field not in cleaned_data or not cleaned_data[field]:
                cleaned_data[field] = None
        
        # Ensure price is numeric
        if 'price' in cleaned_data and cleaned_data['price']:
            try:
                cleaned_data['price'] = float(cleaned_data['price'])
            except (ValueError, TypeError):
                cleaned_data['price'] = None
        
        return cleaned_data
    
    async def _handle_rate_limit(self, response: aiohttp.ClientResponse):
        """Handle rate limiting responses"""
        # Check for Retry-After header
        retry_after = response.headers.get('Retry-After')
        if retry_after:
            try:
                delay = int(retry_after)
                logger.warning(f"Rate limited by {self.retailer_code}. Waiting {delay} seconds.")
                await asyncio.sleep(delay)
            except ValueError:
                # If not a number, wait default time
                await asyncio.sleep(60)
        else:
            # Default rate limit backoff
            await asyncio.sleep(60)
        
        # Update rate limiter
        self.rate_limiter.increase_delay()
    
    def _update_stats(self, success: bool, response_time: float):
        """Update scraping statistics"""
        self.stats['total_requests'] += 1
        
        if success:
            self.stats['successful_requests'] += 1
        else:
            self.stats['failed_requests'] += 1
        
        # Update average response time
        total_time = self.stats['average_response_time'] * (self.stats['total_requests'] - 1)
        self.stats['average_response_time'] = (total_time + response_time) / self.stats['total_requests']
        
        self.stats['last_request_time'] = datetime.now().isoformat()
    
    def get_stats(self) -> Dict[str, Any]:
        """Get scraping statistics"""
        return self.stats.copy()
    
    async def close(self):
        """Clean up resources"""
        await self.session_manager.close()