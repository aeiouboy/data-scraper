"""
URL discovery module for finding product URLs from category pages
"""
import re
import logging
from typing import List, Set
from app.services.firecrawl_client import FirecrawlClient

logger = logging.getLogger(__name__)


class URLDiscovery:
    """Discover product URLs from category and search pages"""
    
    def __init__(self):
        self.client = FirecrawlClient()
        self.discovered_urls: Set[str] = set()
    
    async def discover_from_category(self, category_url: str, max_pages: int = 5) -> List[str]:
        """
        Discover product URLs from a category page
        
        Args:
            category_url: Category page URL
            max_pages: Maximum number of pages to check
            
        Returns:
            List of discovered product URLs
        """
        try:
            logger.info(f"Discovering products from category: {category_url}")
            
            # First, scrape the category page directly
            category_data = await self.client.scrape(category_url)
            
            if not category_data:
                logger.error("Failed to scrape category page")
                return []
            
            # Extract product URLs from the page
            product_urls = self._extract_product_urls(category_data)
            self.discovered_urls.update(product_urls)
            
            logger.info(f"Found {len(product_urls)} products on first page")
            
            # Check for pagination
            if max_pages > 1:
                pagination_urls = self._find_pagination_urls(category_data, category_url)
                
                # Scrape additional pages
                for i, page_url in enumerate(pagination_urls[:max_pages-1]):
                    logger.info(f"Checking page {i+2}: {page_url}")
                    page_data = await self.client.scrape(page_url)
                    
                    if page_data:
                        page_products = self._extract_product_urls(page_data)
                        self.discovered_urls.update(page_products)
                        logger.info(f"Found {len(page_products)} products on page {i+2}")
            
            return list(self.discovered_urls)
            
        except Exception as e:
            logger.error(f"Error discovering URLs: {str(e)}")
            return list(self.discovered_urls)
    
    def _extract_product_urls(self, page_data: dict) -> List[str]:
        """Extract product URLs from page data"""
        urls = []
        
        # Check HTML content
        html = page_data.get('html', '')
        if html:
            # Find all product links
            product_links = re.findall(r'href=["\']([^"\']*?/p/\d+[^"\']*?)["\']', html)
            
            for link in product_links:
                if link.startswith('http'):
                    urls.append(link)
                elif link.startswith('/'):
                    urls.append(f"https://www.homepro.co.th{link}")
        
        # Also check linksOnPage
        links_on_page = page_data.get('linksOnPage', [])
        for link in links_on_page:
            if isinstance(link, str) and '/p/' in link:
                if link not in urls:
                    urls.append(link)
        
        # Clean and deduplicate
        clean_urls = []
        for url in urls:
            # Remove query parameters and fragments
            clean_url = url.split('?')[0].split('#')[0]
            if clean_url not in clean_urls and '/p/' in clean_url:
                clean_urls.append(clean_url)
        
        return clean_urls
    
    def _find_pagination_urls(self, page_data: dict, base_url: str) -> List[str]:
        """Find pagination URLs from the page"""
        pagination_urls = []
        
        html = page_data.get('html', '')
        if not html:
            return pagination_urls
        
        # Common pagination patterns
        # ?page=2, &page=2, /page/2
        page_links = re.findall(r'href=["\']([^"\']*?(?:page[=/]\d+|page=\d+)[^"\']*?)["\']', html, re.IGNORECASE)
        
        for link in page_links:
            if link.startswith('http'):
                pagination_urls.append(link)
            elif link.startswith('/'):
                pagination_urls.append(f"https://www.homepro.co.th{link}")
            elif link.startswith('?'):
                # Append to base URL
                pagination_urls.append(base_url + link)
        
        # Deduplicate and sort
        unique_urls = list(set(pagination_urls))
        unique_urls.sort()
        
        return unique_urls
    
    async def discover_from_search(self, search_query: str, max_results: int = 50) -> List[str]:
        """
        Discover products from search results
        
        Args:
            search_query: Search query
            max_results: Maximum number of results
            
        Returns:
            List of product URLs
        """
        search_url = f"https://www.homepro.co.th/search?q={search_query}"
        
        # Use the category discovery method for search pages too
        return await self.discover_from_category(search_url, max_pages=5)
    
    async def close(self):
        """Close the client connection"""
        await self.client.__aexit__(None, None, None)