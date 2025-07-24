"""
Native scraping strategy using aiohttp and BeautifulSoup
"""
import asyncio
import aiohttp
import ssl
import random
import time
from typing import List, Dict, Any, Optional
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import re
import logging
import json

from .base_strategy import BaseScrapeStrategy, ScrapeResult

logger = logging.getLogger(__name__)

class NativeStrategy(BaseScrapeStrategy):
    """Native scraping strategy using aiohttp and BeautifulSoup"""
    
    def __init__(self, retailer_config: Dict[str, Any] = None):
        super().__init__("native")
        self.config = retailer_config or self._get_default_config()
        self.session = None
        
        # User-Agent rotation for anti-detection
        self.user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:120.0) Gecko/20100101 Firefox/120.0",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:120.0) Gecko/20100101 Firefox/120.0",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15"
        ]
    
    def _get_default_config(self) -> Dict[str, Any]:
        """Get default configuration for HomePro"""
        return {
            'name': 'HomePro',
            'code': 'HP',
            'base_url': 'https://www.homepro.co.th',
            'rate_limit_delay': 2.0,
            'max_concurrent': 3,
            'timeout': 30,
            'retry_attempts': 2
        }
    
    async def _create_session(self):
        """Create HTTP session with anti-detection features"""
        if self.session and not self.session.closed:
            return
        
        # Create SSL context
        ssl_context = ssl.create_default_context()
        ssl_context.check_hostname = False
        ssl_context.verify_mode = ssl.CERT_NONE
        
        connector = aiohttp.TCPConnector(
            limit=self.config['max_concurrent'],
            limit_per_host=1,
            ttl_dns_cache=300,
            use_dns_cache=True,
            keepalive_timeout=30,
            enable_cleanup_closed=True,
            ssl=ssl_context
        )
        
        timeout = aiohttp.ClientTimeout(
            total=self.config['timeout'],
            connect=15,
            sock_read=20
        )
        
        self.session = aiohttp.ClientSession(
            connector=connector,
            timeout=timeout,
            headers=self._get_headers(),
            cookie_jar=aiohttp.CookieJar(unsafe=True),
            trust_env=True,
            auto_decompress=True
        )
        
        logger.debug(f"Created native session for {self.config['name']}")
    
    def _get_headers(self) -> Dict[str, str]:
        """Get randomized headers for anti-detection"""
        return {
            'User-Agent': random.choice(self.user_agents),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
            'Accept-Language': 'th-TH,th;q=0.9,en-US;q=0.8,en;q=0.7',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-User': '?1',
            'Cache-Control': 'no-cache',
            'DNT': '1'
        }
    
    async def scrape_url(self, url: str, **kwargs) -> ScrapeResult:
        """Scrape a single URL using native method"""
        start_time = time.time()
        
        try:
            await self._create_session()
            
            for attempt in range(self.config.get('retry_attempts', 2)):
                try:
                    # Rotate headers for each attempt
                    self.session.headers.update(self._get_headers())
                    
                    async with self.session.get(url) as response:
                        response_time = time.time() - start_time
                        
                        if response.status == 200:
                            content = await response.text(encoding='utf-8', errors='ignore')
                            
                            # Check for blocking
                            if self._is_blocked(content):
                                logger.warning(f"Native: Detected blocking for {url}")
                                await asyncio.sleep(random.uniform(5, 15))
                                continue
                            
                            # Parse content
                            data = await self._parse_content(content, url, response)
                            
                            if data:
                                result = ScrapeResult(
                                    url=url,
                                    success=True,
                                    data=data,
                                    strategy_used="native",
                                    response_time=response_time
                                )
                                self.update_stats(result)
                                return result
                        
                        elif response.status in [403, 429, 503]:
                            logger.warning(f"Native: Rate limited ({response.status}) for {url}")
                            wait_time = (2 ** attempt) * random.uniform(3, 8)
                            await asyncio.sleep(wait_time)
                            continue
                        
                        else:
                            logger.warning(f"Native: HTTP {response.status} for {url}")
                            
                except asyncio.TimeoutError:
                    logger.warning(f"Native: Timeout for {url} (attempt {attempt + 1})")
                    await asyncio.sleep(random.uniform(2, 5))
                    continue
                    
                except Exception as e:
                    logger.warning(f"Native: Error for {url}: {str(e)}")
                    await asyncio.sleep(random.uniform(1, 3))
                    continue
            
            # All attempts failed
            response_time = time.time() - start_time
            result = ScrapeResult(
                url=url,
                success=False,
                error="All native scraping attempts failed",
                strategy_used="native",
                response_time=response_time
            )
            self.update_stats(result)
            return result
            
        except Exception as e:
            response_time = time.time() - start_time
            result = ScrapeResult(
                url=url,
                success=False,
                error=f"Native scraping error: {str(e)}",
                strategy_used="native",
                response_time=response_time
            )
            self.update_stats(result)
            return result
    
    def _is_blocked(self, content: str) -> bool:
        """Check if content indicates blocking"""
        content_lower = content.lower()
        blocking_indicators = [
            'captcha', 'cloudflare', 'access denied', 'forbidden',
            'blocked', 'security check', 'bot detection', 'rate limit',
            'unusual traffic', 'verify you are human'
        ]
        
        for indicator in blocking_indicators:
            if indicator in content_lower:
                return True
        
        # Check for very short content (likely error page)
        if len(content) < 1000:
            return True
        
        return False
    
    async def _parse_content(self, content: str, url: str, response) -> Optional[Dict[str, Any]]:
        """Parse HTML content and extract data"""
        try:
            soup = BeautifulSoup(content, 'html.parser')
            
            data = {
                'url': url,
                'content_length': len(content),
                'response_headers': dict(response.headers),
                'strategy': 'native'
            }
            
            # Extract basic page info
            title = soup.find('title')
            if title:
                data['title'] = title.get_text(strip=True)
            
            # Extract meta description
            meta_desc = soup.find('meta', {'name': 'description'})
            if meta_desc:
                data['meta_description'] = meta_desc.get('content', '')
            
            # Detect page type and extract specific data
            page_type = self._detect_page_type(url, soup)
            data['page_type'] = page_type
            
            if page_type == 'product':
                product_data = self._extract_product_data(soup)
                data.update(product_data)
            elif page_type == 'category':
                category_data = self._extract_category_data(soup, url)
                data.update(category_data)
            
            return data
            
        except Exception as e:
            logger.error(f"Native: Error parsing content from {url}: {str(e)}")
            return None
    
    def _detect_page_type(self, url: str, soup: BeautifulSoup) -> str:
        """Detect the type of page based on URL and content"""
        if '/p/' in url or '/product/' in url:
            return 'product'
        elif '/c/' in url or '/category/' in url:
            return 'category'
        elif url.rstrip('/').endswith(('homepro.co.th', 'homepro.co.th/th')):
            return 'homepage'
        elif '/search' in url:
            return 'search'
        return 'other'
    
    def _extract_product_data(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """Extract product-specific data"""
        data = {}
        
        # Product name
        name_selectors = [
            'h1.product-title', 'h1.product-name', '.product-title',
            '.product-name', 'h1', '.pdp-title'
        ]
        for selector in name_selectors:
            element = soup.select_one(selector)
            if element and element.get_text(strip=True):
                data['name'] = element.get_text(strip=True)
                break
        
        # Price extraction with original vs sale price logic
        current_price = None
        original_price = None
        
        # First try to find original price with HomePro-specific selectors
        homepro_original_price_selectors = [
            '.product-price .price-regular',
            '.product-price .price-original',
            '.original-price', 
            '.regular-price', 
            '.list-price', 
            '.was-price',
            'span.price-regular',
            'span.price-original',
            '.price-container .price-regular',
            '.price-container .price-original'
        ]
        for selector in homepro_original_price_selectors:
            element = soup.select_one(selector)
            if element:
                price_text = element.get_text(strip=True)
                # Extract price from "฿9,990คุณประหยัดไป฿1,300(-13%)" format
                price_match = re.search(r'฿\s*([0-9,]+)', price_text)
                if price_match:
                    try:
                        price_val = float(price_match.group(1).replace(',', ''))
                        # Validate price range and ensure it's higher than current_price
                        if 1000 <= price_val <= 100000 and (not current_price or price_val > current_price):
                            original_price = price_val
                            break
                    except ValueError:
                        continue
        
        # Enhanced price extraction for HomePro - prioritize JSON-LD structured data
        # First try to get price from JSON-LD structured data (most reliable)
        scripts = soup.find_all('script', type='application/ld+json')
        for script in scripts:
            if script.string:
                try:
                    json_data = json.loads(script.string)
                    if isinstance(json_data, dict) and json_data.get('@type') == 'Product':
                        offers = json_data.get('offers')
                        if isinstance(offers, dict):
                            price_str = offers.get('price')
                            if price_str:
                                try:
                                    price_val = float(price_str)
                                    if 1000 <= price_val <= 100000:
                                        current_price = price_val
                                        break
                                except ValueError:
                                    continue
                        elif isinstance(offers, list) and offers:
                            price_str = offers[0].get('price')
                            if price_str:
                                try:
                                    price_val = float(price_str)
                                    if 1000 <= price_val <= 100000:
                                        current_price = price_val
                                        break
                                except ValueError:
                                    continue
                except (json.JSONDecodeError, KeyError):
                    continue
        
        # If JSON-LD fails, try HomePro-specific price selectors
        if not current_price:
            homepro_current_price_selectors = [
                '.product-price .price-sale',
                '.product-price .price-current',
                '.price-now',
                '.current-price',
                '.sale-price',
                '.product-price-value',
                'span.price-sale',
                'span.price-current',
                '.price-container .price-sale',
                '.price-container .price-current'
            ]
            
            for selector in homepro_current_price_selectors:
                element = soup.select_one(selector)
                if element:
                    price_text = element.get_text(strip=True)
                    price_match = re.search(r'฿\s*([0-9,]+)', price_text)
                    if price_match:
                        try:
                            price_val = float(price_match.group(1).replace(',', ''))
                            # Validate price range for HomePro products (1000-100000 baht)
                            if 1000 <= price_val <= 100000:
                                current_price = price_val
                                break
                        except ValueError:
                            continue
        
        # Last resort: gtmPrice (known to be unreliable for HomePro)
        if not current_price:
            gtm_price_input = soup.find('input', {'id': re.compile(r'gtmPrice-\d+')})
            if gtm_price_input:
                try:
                    price_val = float(gtm_price_input.get('value', 0))
                    if 1000 <= price_val <= 100000:  # Validate range
                        current_price = price_val
                except (ValueError, TypeError):
                    pass
        
        # Look for original price in currency containers
        currency_containers = soup.find_all('span', class_='currency-container')
        for container in currency_containers:
            amount_span = container.find('span', class_='amount')
            if amount_span:
                try:
                    price_val = float(amount_span.get_text(strip=True).replace(',', ''))
                    if price_val != current_price and price_val > current_price:
                        original_price = price_val
                        break
                except (ValueError, TypeError):
                    continue
        
        # If no current price found via selectors, use improved text extraction with better validation
        if not current_price:
            # Look for price in structured elements with HomePro-specific context
            price_elements = soup.find_all(['span', 'div', 'p'], string=re.compile(r'฿\s*[0-9,]+'))
            
            # Filter prices to HomePro product range (1000-100000 baht)
            found_prices = []
            for elem in price_elements:
                price_text = elem.get_text(strip=True)
                price_match = re.search(r'฿\s*([0-9,]+)', price_text)
                if price_match:
                    try:
                        price_val = float(price_match.group(1).replace(',', ''))
                        # More restrictive range for HomePro products to avoid discount amounts
                        if 1000 <= price_val <= 100000:
                            found_prices.append(price_val)
                    except ValueError:
                        continue
            
            # Remove duplicates and sort
            found_prices = sorted(list(set(found_prices)))
            
            if found_prices:
                # For HomePro, if we have multiple prices, take the highest one as current price
                # This assumes the main product price is the most prominent/highest value
                current_price = max(found_prices)
                
                # If we have more than one price, the second highest might be original price
                if len(found_prices) >= 2:
                    sorted_desc = sorted(found_prices, reverse=True)
                    potential_original = sorted_desc[1]
                    # Only set as original if it's higher than current (discount scenario)
                    if potential_original > current_price:
                        original_price = potential_original
                        current_price = sorted_desc[0]  # Take the lower one as current
        
        # Store price data
        if current_price:
            data['price'] = current_price
            data['current_price'] = current_price
        if original_price:
            data['original_price'] = original_price
        
        # Calculate discount
        if current_price and original_price and original_price > current_price:
            discount_amount = original_price - current_price
            discount_percentage = (discount_amount / original_price) * 100
            data['discount_amount'] = discount_amount
            data['discount_percentage'] = round(discount_percentage, 2)
        
        # Brand extraction - look for structured data first
        brand = None
        
        # Try to find brand from JSON-LD structured data
        scripts = soup.find_all('script', type='application/ld+json')
        for script in scripts:
            if script.string:
                try:
                    json_data = json.loads(script.string)
                    if isinstance(json_data, dict) and json_data.get('@type') == 'Product':
                        brand_info = json_data.get('brand')
                        if isinstance(brand_info, dict):
                            brand = brand_info.get('name')
                        elif isinstance(brand_info, str):
                            brand = brand_info
                        if brand:
                            break
                except (json.JSONDecodeError, KeyError):
                    continue
        
        # Fallback to selector-based brand extraction
        if not brand:
            brand_selectors = ['.brand-name', '.product-brand', '.manufacturer', '[data-brand]']
            for selector in brand_selectors:
                element = soup.select_one(selector)
                if element and element.get_text(strip=True):
                    potential_brand = element.get_text(strip=True)
                    # Filter out obviously wrong brands (like "LED" or category names)
                    if len(potential_brand) > 2 and not re.match(r'^(LED|LCD|TV|ทีวี)$', potential_brand, re.IGNORECASE):
                        brand = potential_brand
                        break
        
        # Extract brand from product name as last resort
        if not brand and data.get('name'):
            name = data['name']
            # Common brand patterns in HomePro product names
            brand_patterns = [
                r'^([A-Z][a-z]+)\s',  # Brand at start (capitalized)
                r'\b(SAMSUNG|LG|SONY|PANASONIC|SHARP|TCL|HAIER|NANO)\b',  # Known brands
            ]
            for pattern in brand_patterns:
                match = re.search(pattern, name, re.IGNORECASE)
                if match:
                    brand = match.group(1).upper()
                    break
        
        if brand:
            data['brand'] = brand
        
        # Extract category from breadcrumb or navigation
        category = None
        category_selectors = [
            '.breadcrumb a:not(:first-child)',
            '.breadcrumbs a:not(:first-child)', 
            '.nav-breadcrumb a:not(:first-child)',
            '.category-path a',
            '[data-category]'
        ]
        
        for selector in category_selectors:
            elements = soup.select(selector)
            if elements:
                # Get the last meaningful breadcrumb (most specific category)
                categories = [elem.get_text(strip=True) for elem in elements if elem.get_text(strip=True)]
                if categories:
                    category = categories[-1]  # Take only the most specific category (last one)
                    break
        
        if category:
            data['category'] = category
        
        # Extract product description and specifications
        description_parts = []
        spec_data = {}
        
        # Try to find description sections
        desc_selectors = [
            '.product-description',
            '.product-details', 
            '.product-info',
            '.description',
            '#description'
        ]
        
        for selector in desc_selectors:
            element = soup.select_one(selector)
            if element:
                desc_text = element.get_text(strip=True)
                if desc_text and len(desc_text) > 10:
                    description_parts.append(desc_text)
        
        # Extract specifications from tables or lists
        spec_tables = soup.find_all(['table', 'dl', 'ul'], class_=re.compile(r'spec|detail|info', re.I))
        for table in spec_tables:
            if table.name == 'table':
                rows = table.find_all('tr')
                for row in rows:
                    cells = row.find_all(['td', 'th'])
                    if len(cells) >= 2:
                        key = cells[0].get_text(strip=True)
                        value = cells[1].get_text(strip=True)
                        if key and value:
                            spec_data[key] = value
            elif table.name == 'dl':
                terms = table.find_all('dt')
                definitions = table.find_all('dd')
                for term, definition in zip(terms, definitions):
                    key = term.get_text(strip=True)
                    value = definition.get_text(strip=True)
                    if key and value:
                        spec_data[key] = value
        
        if description_parts:
            data['description'] = ' '.join(description_parts[:3])  # Limit to avoid too much text
        
        if spec_data:
            data['specifications'] = spec_data
        
        # Extract product images
        images = []
        image_selectors = [
            '.product-image img',
            '.product-gallery img',
            '.product-photos img',
            '[data-product-image] img'
        ]
        
        for selector in image_selectors:
            elements = soup.select(selector)
            for img in elements:
                src = img.get('src') or img.get('data-src') or img.get('data-lazy')
                if src and src not in images:
                    if src.startswith('//'):
                        src = 'https:' + src
                    elif src.startswith('/'):
                        src = self.config['base_url'] + src
                    if src.startswith('http'):
                        images.append(src)
        
        if images:
            data['images'] = images[:10]  # Limit to 10 images
        
        # Enhanced availability detection
        page_text = soup.get_text().lower()
        availability_indicators = {
            'in_stock': ['มีสินค้า', 'in stock', 'available', 'พร้อมส่ง', 'มีในสต็อก'],
            'out_of_stock': ['หมดสินค้า', 'out of stock', 'unavailable', 'สินค้าหมด'],
            'limited_stock': ['สินค้าเหลือน้อย', 'limited stock', 'few left'],
            'preorder': ['สั่งจอง', 'preorder', 'pre-order']
        }
        
        availability = 'unknown'
        for status, indicators in availability_indicators.items():
            if any(indicator in page_text for indicator in indicators):
                availability = status
                break
        
        # If still unknown but we have a current price, assume in stock
        if availability == 'unknown' and current_price:
            availability = 'in_stock'
        
        data['availability'] = availability
        
        return data
    
    def _extract_category_data(self, soup: BeautifulSoup, url: str) -> Dict[str, Any]:
        """Extract category-specific data"""
        data = {}
        
        # Category name
        name_selectors = ['h1', '.category-title', '.page-title', '.category-name']
        for selector in name_selectors:
            element = soup.select_one(selector)
            if element and element.get_text(strip=True):
                data['category_name'] = element.get_text(strip=True)
                break
        
        # Product links
        product_links = []
        link_selectors = [
            'a[href*="/p/"]', 'a[href*="/product/"]',
            '.product-item a', '.product-card a'
        ]
        
        for selector in link_selectors:
            elements = soup.select(selector)
            for element in elements:
                href = element.get('href')
                if href:
                    if href.startswith('/'):
                        href = self.config['base_url'] + href
                    if href not in product_links:
                        product_links.append(href)
        
        data['product_links'] = product_links  # Remove artificial limit
        data['products_found'] = len(product_links)
        
        return data
    
    async def scrape_batch(self, urls: List[str], max_concurrent: int = 5, **kwargs) -> List[ScrapeResult]:
        """Scrape multiple URLs concurrently"""
        await self._create_session()
        
        semaphore = asyncio.Semaphore(min(max_concurrent, self.config['max_concurrent']))
        
        async def scrape_with_semaphore(url: str) -> ScrapeResult:
            async with semaphore:
                result = await self.scrape_url(url)
                # Add delay between requests
                await asyncio.sleep(random.uniform(1, 3))
                return result
        
        results = await asyncio.gather(
            *[scrape_with_semaphore(url) for url in urls],
            return_exceptions=True
        )
        
        # Handle exceptions
        final_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                final_results.append(ScrapeResult(
                    url=urls[i],
                    success=False,
                    error=f"Exception during scraping: {str(result)}",
                    strategy_used="native"
                ))
            else:
                final_results.append(result)
        
        return final_results
    
    async def discover_urls(self, category_url: str, max_pages: int = 5, **kwargs) -> List[str]:
        """Discover product URLs from category pages with pagination support"""
        discovered_urls = []
        
        try:
            logger.info(f"Native: Starting URL discovery from {category_url} (max {max_pages} pages)")
            
            for page in range(1, max_pages + 1):
                # Build paginated URL
                if '?' in category_url:
                    page_url = f"{category_url}&page={page}"
                else:
                    page_url = f"{category_url}?page={page}"
                
                logger.debug(f"Native: Scraping page {page}: {page_url}")
                
                # Scrape this page
                result = await self.scrape_url(page_url)
                
                if result.success and result.data:
                    product_links = result.data.get('product_links', [])
                    
                    if not product_links:
                        logger.info(f"Native: No products found on page {page}, stopping pagination")
                        break
                    
                    # Add new URLs (avoid duplicates)
                    new_urls = [url for url in product_links if url not in discovered_urls]
                    discovered_urls.extend(new_urls)
                    
                    logger.info(f"Native: Page {page}: found {len(product_links)} URLs, {len(new_urls)} new (total: {len(discovered_urls)})")
                    
                    # Small delay between pages to be respectful
                    if page < max_pages:
                        await asyncio.sleep(0.5)
                else:
                    logger.warning(f"Native: Failed to scrape page {page}: {result.error}")
                    # Continue to next page instead of stopping
                    continue
            
            logger.info(f"Native: Discovered {len(discovered_urls)} URLs from {category_url} ({max_pages} pages)")
            return discovered_urls
            
        except Exception as e:
            logger.error(f"Native: URL discovery error for {category_url}: {str(e)}")
            return discovered_urls  # Return what we have so far
    
    async def close(self):
        """Close the HTTP session"""
        if self.session and not self.session.closed:
            await self.session.close()
            logger.debug("Native session closed")