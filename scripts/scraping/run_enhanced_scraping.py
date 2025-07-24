#!/usr/bin/env python3
"""
Enhanced Native Scraping System
Production-ready scraper with advanced anti-detection and proper encoding support
"""
import asyncio
import logging
import sys
import os
from pathlib import Path
from typing import Dict, List, Any, Optional
import json
from datetime import datetime
import argparse
import aiohttp
from bs4 import BeautifulSoup
import random
import time
from urllib.parse import urljoin, urlparse
import re
import ssl

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('enhanced_scraping.log')
    ]
)
logger = logging.getLogger(__name__)

class EnhancedNativeScraper:
    """Enhanced native scraper with proper encoding and anti-detection"""
    
    def __init__(self, retailer_code: str = 'HP'):
        self.retailer_code = retailer_code
        self.config = self.get_retailer_config()
        self.session = None
        self.results = []
        self.stats = {
            'start_time': datetime.now(),
            'total_requests': 0,
            'successful_requests': 0,
            'failed_requests': 0,
            'blocked_requests': 0,
            'encoding_errors': 0,
            'total_response_time': 0,
            'data_extracted': 0
        }
        
        # Enhanced User-Agent rotation
        self.user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:120.0) Gecko/20100101 Firefox/120.0",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:120.0) Gecko/20100101 Firefox/120.0",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15"
        ]
        
        self.current_user_agent = random.choice(self.user_agents)
        
    def get_retailer_config(self) -> Dict[str, Any]:
        """Get enhanced retailer configuration"""
        configs = {
            'HP': {
                'name': 'HomePro',
                'code': 'HP',
                'base_url': 'https://www.homepro.co.th',
                'rate_limit_delay': 3.0,
                'max_concurrent': 1,
                'timeout': 45,
                'retry_attempts': 2,
                'test_urls': [
                    'https://www.homepro.co.th',
                    'https://www.homepro.co.th/th'
                ]
            }
        }
        return configs.get(self.retailer_code, configs['HP'])
    
    def get_enhanced_headers(self) -> Dict[str, str]:
        """Get enhanced headers that mimic real browsers"""
        return {
            'User-Agent': self.current_user_agent,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
            'Accept-Language': 'en-US,en;q=0.9,th;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-User': '?1',
            'Cache-Control': 'no-cache',
            'Pragma': 'no-cache',
            'DNT': '1'
        }
    
    async def create_session(self):
        """Create enhanced HTTP session"""
        # Create SSL context that's more permissive
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
            connect=20,
            sock_read=30
        )
        
        self.session = aiohttp.ClientSession(
            connector=connector,
            timeout=timeout,
            headers=self.get_enhanced_headers(),
            cookie_jar=aiohttp.CookieJar(unsafe=True),
            trust_env=True,
            auto_decompress=True,  # Handle compression automatically
            read_bufsize=65536     # Larger buffer for better performance
        )
        
        logger.info(f"🔧 Enhanced session created for {self.config['name']}")
        logger.info(f"   User-Agent: {self.current_user_agent[:50]}...")
    
    async def scrape_url(self, url: str) -> Dict[str, Any]:
        """Enhanced URL scraping with better error handling"""
        if not self.session:
            await self.create_session()
        
        self.stats['total_requests'] += 1
        start_time = time.time()
        
        for attempt in range(self.config.get('retry_attempts', 2)):
            try:
                # Rotate User-Agent occasionally
                if random.random() < 0.3:  # 30% chance
                    self.current_user_agent = random.choice(self.user_agents)
                    self.session.headers.update({'User-Agent': self.current_user_agent})
                
                logger.info(f"📡 Attempt {attempt + 1}/{self.config['retry_attempts']}: {url}")
                
                async with self.session.get(url) as response:
                    response_time = time.time() - start_time
                    self.stats['total_response_time'] += response_time
                    
                    logger.info(f"   Status: {response.status} | Time: {response_time:.2f}s | Size: {response.headers.get('content-length', 'unknown')}")
                    
                    if response.status == 200:
                        try:
                            # Try to read content with proper encoding handling
                            content = await response.text(encoding='utf-8', errors='ignore')
                            
                            if len(content) < 100:
                                logger.warning(f"⚠️ Very short content ({len(content)} chars) - possible blocking")
                                self.stats['blocked_requests'] += 1
                                continue
                            
                            # Check for blocking indicators
                            if self.is_content_blocked(content):
                                logger.warning(f"🚫 Content appears to be blocked")
                                self.stats['blocked_requests'] += 1
                                await asyncio.sleep(random.uniform(10, 20))
                                continue
                            
                            # Parse and extract data
                            data = await self.parse_enhanced_content(content, url, response)
                            
                            if data:
                                self.stats['successful_requests'] += 1
                                self.stats['data_extracted'] += 1
                                
                                return {
                                    'success': True,
                                    'data': data,
                                    'response_time': response_time,
                                    'attempt': attempt + 1,
                                    'status_code': response.status
                                }
                        
                        except UnicodeDecodeError as e:
                            logger.error(f"🔤 Encoding error: {str(e)}")
                            self.stats['encoding_errors'] += 1
                            continue
                        
                        except Exception as e:
                            logger.error(f"❌ Content processing error: {str(e)}")
                            continue
                    
                    elif response.status in [403, 429, 503, 502, 520]:
                        logger.warning(f"🚫 Server blocking/rate limiting: {response.status}")
                        self.stats['blocked_requests'] += 1
                        
                        # Check response headers for retry info
                        retry_after = response.headers.get('Retry-After')
                        if retry_after:
                            try:
                                wait_time = int(retry_after)
                                logger.info(f"⏰ Retry-After header says wait {wait_time}s")
                                await asyncio.sleep(min(wait_time, 60))  # Cap at 60s
                            except ValueError:
                                await asyncio.sleep(random.uniform(15, 30))
                        else:
                            # Exponential backoff
                            wait_time = (2 ** attempt) * random.uniform(5, 15)
                            logger.info(f"⏰ Exponential backoff: {wait_time:.1f}s")
                            await asyncio.sleep(wait_time)
                        continue
                    
                    elif response.status == 404:
                        logger.warning(f"📭 Page not found: {url}")
                        break  # Don't retry 404s
                    
                    else:
                        logger.error(f"❌ HTTP {response.status}: {url}")
                        await asyncio.sleep(random.uniform(2, 8))
                        continue
                        
            except asyncio.TimeoutError:
                logger.error(f"⏱️ Timeout on attempt {attempt + 1}")
                await asyncio.sleep(random.uniform(5, 15))
                continue
                
            except aiohttp.ClientError as e:
                logger.error(f"🌐 Client error: {str(e)}")
                await asyncio.sleep(random.uniform(3, 10))
                continue
                
            except Exception as e:
                logger.error(f"❌ Unexpected error: {str(e)}")
                await asyncio.sleep(random.uniform(2, 8))
                continue
        
        # All attempts failed
        response_time = time.time() - start_time
        self.stats['failed_requests'] += 1
        
        return {
            'success': False,
            'error': 'All retry attempts failed',
            'response_time': response_time,
            'attempts': self.config.get('retry_attempts', 2)
        }
    
    def is_content_blocked(self, content: str) -> bool:
        """Enhanced blocking detection"""
        content_lower = content.lower()
        
        blocking_indicators = [
            'cloudflare',
            'access denied',
            'forbidden',
            'captcha',
            'verify you are human',
            'unusual traffic',
            'bot detection',
            'security check',
            'rate limit exceeded',
            'temporarily unavailable',
            'please enable javascript',
            'browser check'
        ]
        
        for indicator in blocking_indicators:
            if indicator in content_lower:
                logger.debug(f"Found blocking indicator: {indicator}")
                return True
        
        # Check for suspicious HTML structures
        if '<html' in content_lower and len(content) < 2000:
            # Very short HTML pages are often error/blocking pages
            if any(word in content_lower for word in ['error', 'blocked', 'denied']):
                return True
        
        return False
    
    async def parse_enhanced_content(self, content: str, url: str, response) -> Optional[Dict[str, Any]]:
        """Enhanced content parsing with better data extraction"""
        try:
            soup = BeautifulSoup(content, 'html.parser')
            
            data = {
                'url': url,
                'scraped_at': datetime.now().isoformat(),
                'content_length': len(content),
                'response_headers': dict(response.headers),
                'strategy': 'enhanced_native',
                'retailer': self.config['code']
            }
            
            # Extract basic page info
            title = soup.find('title')
            if title:
                data['title'] = title.get_text(strip=True)
            
            # Extract meta information
            meta_desc = soup.find('meta', {'name': 'description'})
            if meta_desc:
                data['meta_description'] = meta_desc.get('content', '')
            
            meta_keywords = soup.find('meta', {'name': 'keywords'})
            if meta_keywords:
                data['meta_keywords'] = meta_keywords.get('content', '')
            
            # Extract language
            html_tag = soup.find('html')
            if html_tag:
                data['page_language'] = html_tag.get('lang', 'unknown')
            
            # Count various elements
            data['elements_count'] = {
                'links': len(soup.find_all('a', href=True)),
                'images': len(soup.find_all('img')),
                'forms': len(soup.find_all('form')),
                'scripts': len(soup.find_all('script')),
                'stylesheets': len(soup.find_all('link', {'rel': 'stylesheet'}))
            }
            
            # Try to detect page type
            data['page_type'] = self.detect_page_type(url, soup)
            
            # Extract specific data based on page type
            if data['page_type'] == 'product':
                product_data = self.extract_enhanced_product_data(soup)
                data.update(product_data)
            elif data['page_type'] == 'category':
                category_data = self.extract_enhanced_category_data(soup, url)
                data.update(category_data)
            elif data['page_type'] == 'homepage':
                homepage_data = self.extract_homepage_data(soup)
                data.update(homepage_data)
            
            # Extract structured data (JSON-LD)
            structured_data = self.extract_structured_data(soup)
            if structured_data:
                data['structured_data'] = structured_data
            
            # Content quality assessment
            data['content_quality'] = self.assess_content_quality(soup, content)
            
            return data
            
        except Exception as e:
            logger.error(f"Error parsing content from {url}: {str(e)}")
            return None
    
    def detect_page_type(self, url: str, soup: BeautifulSoup) -> str:
        """Detect the type of page"""
        # URL-based detection
        if '/p/' in url or '/product/' in url:
            return 'product'
        elif '/c/' in url or '/category/' in url or '/categories/' in url:
            return 'category'
        elif url.rstrip('/').endswith(('homepro.co.th', 'homepro.co.th/th')):
            return 'homepage'
        elif '/search' in url:
            return 'search'
        elif '/about' in url or '/contact' in url:
            return 'info'
        
        # Content-based detection
        title = soup.find('title')
        if title:
            title_text = title.get_text().lower()
            if 'product' in title_text or 'item' in title_text:
                return 'product'
            elif 'category' in title_text or 'collection' in title_text:
                return 'category'
        
        return 'other'
    
    def extract_enhanced_product_data(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """Enhanced product data extraction"""
        data = {'page_type_confirmed': 'product'}
        
        # Product name (multiple selectors)
        name_selectors = [
            'h1.product-title', 'h1.product-name', '.product-title', 
            '.product-name', 'h1', '.pdp-title'
        ]
        for selector in name_selectors:
            element = soup.select_one(selector)
            if element and element.get_text(strip=True):
                data['product_name'] = element.get_text(strip=True)
                break
        
        # Price extraction with Thai baht support
        price_selectors = [
            '.price-current', '.current-price', '.product-price', 
            '.price', '.sale-price', '.final-price'
        ]
        for selector in price_selectors:
            element = soup.select_one(selector)
            if element:
                price_text = element.get_text(strip=True)
                price_match = re.search(r'฿?\s*([0-9,]+(?:\.[0-9]+)?)', price_text)
                if price_match:
                    try:
                        data['price'] = float(price_match.group(1).replace(',', ''))
                        data['price_text'] = price_text
                        break
                    except ValueError:
                        continue
        
        # Brand extraction
        brand_selectors = [
            '.brand-name', '.product-brand', '.manufacturer', 
            '[data-brand]', '.brand'
        ]
        for selector in brand_selectors:
            element = soup.select_one(selector)
            if element and element.get_text(strip=True):
                data['brand'] = element.get_text(strip=True)
                break
        
        # Availability
        availability_indicators = soup.get_text().lower()
        if 'มีสินค้า' in availability_indicators or 'in stock' in availability_indicators:
            data['availability'] = 'in_stock'
        elif 'หมดสินค้า' in availability_indicators or 'out of stock' in availability_indicators:
            data['availability'] = 'out_of_stock'
        else:
            data['availability'] = 'unknown'
        
        return data
    
    def extract_enhanced_category_data(self, soup: BeautifulSoup, url: str) -> Dict[str, Any]:
        """Enhanced category data extraction"""
        data = {'page_type_confirmed': 'category'}
        
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
        
        data['product_links'] = product_links[:50]  # Limit to 50
        data['products_found'] = len(product_links)
        
        return data
    
    def extract_homepage_data(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """Extract homepage-specific data"""
        data = {'page_type_confirmed': 'homepage'}
        
        # Main navigation links
        nav_links = []
        nav_selectors = ['nav a', '.navigation a', '.menu a', '.nav-link']
        for selector in nav_selectors:
            elements = soup.select(selector)
            for element in elements:
                href = element.get('href')
                text = element.get_text(strip=True)
                if href and text:
                    nav_links.append({'url': href, 'text': text})
        
        data['navigation_links'] = nav_links[:20]  # First 20
        
        # Featured categories
        category_links = []
        category_selectors = ['a[href*="/c/"]', 'a[href*="/category/"]']
        for selector in category_selectors:
            elements = soup.select(selector)
            for element in elements:
                href = element.get('href')
                text = element.get_text(strip=True)
                if href and text:
                    if href.startswith('/'):
                        href = self.config['base_url'] + href
                    category_links.append({'url': href, 'text': text})
        
        data['category_links'] = category_links[:30]  # First 30
        
        return data
    
    def extract_structured_data(self, soup: BeautifulSoup) -> Optional[Dict]:
        """Extract JSON-LD structured data"""
        scripts = soup.find_all('script', {'type': 'application/ld+json'})
        structured_data = []
        
        for script in scripts:
            try:
                if script.string:
                    json_data = json.loads(script.string)
                    structured_data.append(json_data)
            except json.JSONDecodeError:
                continue
        
        return structured_data if structured_data else None
    
    def assess_content_quality(self, soup: BeautifulSoup, content: str) -> Dict[str, Any]:
        """Assess the quality and completeness of extracted content"""
        return {
            'has_title': bool(soup.find('title')),
            'has_meta_description': bool(soup.find('meta', {'name': 'description'})),
            'content_length': len(content),
            'text_length': len(soup.get_text()),
            'has_images': len(soup.find_all('img')) > 0,
            'has_links': len(soup.find_all('a', href=True)) > 0,
            'has_forms': len(soup.find_all('form')) > 0,
            'quality_score': self.calculate_quality_score(soup, content)
        }
    
    def calculate_quality_score(self, soup: BeautifulSoup, content: str) -> float:
        """Calculate a quality score for the scraped content"""
        score = 0.0
        
        # Basic structure checks
        if soup.find('title'): score += 0.2
        if soup.find('meta', {'name': 'description'}): score += 0.1
        if len(soup.get_text()) > 1000: score += 0.2
        if len(soup.find_all('a', href=True)) > 5: score += 0.1
        if len(soup.find_all('img')) > 0: score += 0.1
        
        # Content quality checks
        if 'product' in content.lower() or 'category' in content.lower(): score += 0.2
        if '฿' in content or 'price' in content.lower(): score += 0.1
        
        return min(1.0, score)
    
    async def run_enhanced_session(self, mode: str = 'test', limit: int = 3):
        """Run enhanced scraping session"""
        logger.info(f"🚀 Starting Enhanced Native Scraping Session")
        logger.info(f"Retailer: {self.config['name']} ({self.config['code']})")
        logger.info(f"Mode: {mode}, Limit: {limit}")
        logger.info("=" * 80)
        
        try:
            # Test connectivity
            await self.test_enhanced_connectivity()
            
            if mode == 'test':
                await self.run_test_mode(limit)
            elif mode == 'explore':
                await self.run_exploration_mode(limit)
            else:
                logger.error(f"Unknown mode: {mode}")
                return
            
            await self.generate_enhanced_report()
            
        except Exception as e:
            logger.error(f"❌ Enhanced session failed: {str(e)}")
            import traceback
            traceback.print_exc()
        
        finally:
            if self.session:
                await self.session.close()
                logger.info("🔐 Session closed")
    
    async def test_enhanced_connectivity(self):
        """Test connectivity with enhanced error handling"""
        logger.info(f"🔍 Testing enhanced connectivity to {self.config['name']}...")
        
        test_urls = self.config.get('test_urls', [self.config['base_url']])
        
        for i, test_url in enumerate(test_urls, 1):
            logger.info(f"🌐 Test {i}/{len(test_urls)}: {test_url}")
            
            result = await self.scrape_url(test_url)
            
            if result['success']:
                data = result['data']
                logger.info(f"✅ Connection successful!")
                logger.info(f"   Title: {data.get('title', 'N/A')}")
                logger.info(f"   Page type: {data.get('page_type', 'N/A')}")
                logger.info(f"   Content length: {data.get('content_length', 0):,} chars")
                logger.info(f"   Quality score: {data.get('content_quality', {}).get('quality_score', 0):.2f}")
                logger.info(f"   Response time: {result['response_time']:.2f}s")
                return True
            else:
                logger.error(f"❌ Connection failed: {result.get('error', 'Unknown error')}")
        
        logger.error("❌ All connectivity tests failed")
        return False
    
    async def run_test_mode(self, limit: int):
        """Run safe test mode"""
        logger.info("🧪 Running enhanced test mode...")
        
        test_urls = [
            self.config['base_url'],
            f"{self.config['base_url']}/th",
            f"{self.config['base_url']}/about-us",
            f"{self.config['base_url']}/contact-us"
        ]
        
        for i, url in enumerate(test_urls[:limit], 1):
            logger.info(f"\n🔍 Test {i}/{min(limit, len(test_urls))}: {url}")
            
            result = await self.scrape_url(url)
            self.results.append(result)
            
            if result['success']:
                data = result['data']
                logger.info(f"✅ Success: {data.get('title', 'N/A')}")
                logger.info(f"   Page type: {data.get('page_type', 'unknown')}")
                logger.info(f"   Quality: {data.get('content_quality', {}).get('quality_score', 0):.2f}")
                
                if data.get('page_type') == 'homepage' and data.get('category_links'):
                    logger.info(f"   Categories found: {len(data['category_links'])}")
                    for cat in data['category_links'][:3]:
                        logger.info(f"     - {cat['text']}: {cat['url']}")
                        
            else:
                logger.error(f"❌ Failed: {result.get('error', 'Unknown error')}")
            
            # Enhanced delay with randomization
            delay = self.config['rate_limit_delay'] + random.uniform(-1, 2)
            logger.info(f"⏰ Waiting {delay:.1f}s...")
            await asyncio.sleep(delay)
    
    async def run_exploration_mode(self, limit: int):
        """Run exploration mode to discover site structure"""
        logger.info("🔍 Running exploration mode...")
        logger.info("⚠️  This mode attempts to map site structure")
        
        # Start with homepage
        homepage_result = await self.scrape_url(self.config['base_url'])
        self.results.append(homepage_result)
        
        if homepage_result['success']:
            data = homepage_result['data']
            logger.info(f"✅ Homepage mapped: {data.get('title', 'N/A')}")
            
            # Explore categories found on homepage
            category_links = data.get('category_links', [])
            if category_links:
                logger.info(f"🔍 Found {len(category_links)} categories to explore")
                
                for i, category in enumerate(category_links[:limit-1], 1):
                    logger.info(f"\n📂 Exploring category {i}: {category['text']}")
                    
                    await asyncio.sleep(random.uniform(3, 8))  # Longer delay for exploration
                    
                    cat_result = await self.scrape_url(category['url'])
                    self.results.append(cat_result)
                    
                    if cat_result['success']:
                        cat_data = cat_result['data']
                        logger.info(f"✅ Category mapped: {cat_data.get('category_name', 'N/A')}")
                        if cat_data.get('products_found', 0) > 0:
                            logger.info(f"   Products found: {cat_data['products_found']}")
                    else:
                        logger.error(f"❌ Category exploration failed")
        else:
            logger.error("❌ Homepage exploration failed")
    
    async def generate_enhanced_report(self):
        """Generate comprehensive enhanced report"""
        logger.info("\n📊 ENHANCED SCRAPING REPORT")
        logger.info("=" * 80)
        
        end_time = datetime.now()
        duration = (end_time - self.stats['start_time']).total_seconds()
        
        # Calculate metrics
        total_requests = self.stats['total_requests']
        if total_requests > 0:
            success_rate = (self.stats['successful_requests'] / total_requests) * 100
            block_rate = (self.stats['blocked_requests'] / total_requests) * 100
            encoding_error_rate = (self.stats['encoding_errors'] / total_requests) * 100
            avg_response_time = self.stats['total_response_time'] / total_requests
        else:
            success_rate = block_rate = encoding_error_rate = avg_response_time = 0
        
        logger.info(f"📈 Performance Metrics:")
        logger.info(f"   Retailer: {self.config['name']}")
        logger.info(f"   Session Duration: {duration:.1f} seconds")
        logger.info(f"   Total Requests: {total_requests}")
        logger.info(f"   Successful: {self.stats['successful_requests']}")
        logger.info(f"   Failed: {self.stats['failed_requests']}")
        logger.info(f"   Blocked: {self.stats['blocked_requests']}")
        logger.info(f"   Encoding Errors: {self.stats['encoding_errors']}")
        logger.info(f"   Success Rate: {success_rate:.1f}%")
        logger.info(f"   Block Rate: {block_rate:.1f}%")
        logger.info(f"   Encoding Error Rate: {encoding_error_rate:.1f}%")
        logger.info(f"   Avg Response Time: {avg_response_time:.2f}s")
        logger.info(f"   Data Extracted: {self.stats['data_extracted']} pages")
        
        # Data quality analysis
        successful_results = [r for r in self.results if r['success']]
        if successful_results:
            avg_quality = sum(r['data'].get('content_quality', {}).get('quality_score', 0) 
                            for r in successful_results) / len(successful_results)
            
            page_types = {}
            for result in successful_results:
                page_type = result['data'].get('page_type', 'unknown')
                page_types[page_type] = page_types.get(page_type, 0) + 1
            
            logger.info(f"\n📊 Data Quality Analysis:")
            logger.info(f"   Average Quality Score: {avg_quality:.2f}/1.0")
            logger.info(f"   Page Types Discovered:")
            for page_type, count in page_types.items():
                logger.info(f"     {page_type}: {count}")
        
        # Technical analysis
        logger.info(f"\n🔧 Technical Analysis:")
        logger.info(f"   Encoding: UTF-8 with error handling")
        logger.info(f"   Compression: Brotli, gzip, deflate supported")
        logger.info(f"   SSL: Custom context with relaxed verification")
        logger.info(f"   User-Agent: Rotated {len(self.user_agents)} variants")
        
        # Recommendations
        logger.info(f"\n💡 Recommendations:")
        if success_rate > 80:
            logger.info(f"   ✅ Excellent success rate - ready for production")
        elif success_rate > 60:
            logger.info(f"   ⚠️  Good success rate - can proceed with monitoring")
        else:
            logger.info(f"   ❌ Low success rate - requires optimization")
        
        if block_rate > 30:
            logger.info(f"   ⚠️  High blocking rate - increase delays and improve headers")
        elif block_rate > 10:
            logger.info(f"   ⚠️  Moderate blocking - monitor and adjust as needed")
        else:
            logger.info(f"   ✅ Low blocking rate - current approach is working")
        
        if encoding_error_rate > 5:
            logger.info(f"   ⚠️  Encoding issues detected - may need charset detection")
        
        # Cost savings
        firecrawl_cost = total_requests * 0.02
        logger.info(f"\n💰 Cost Analysis:")
        logger.info(f"   Native Scraping: $0.00")
        logger.info(f"   Firecrawl API: ${firecrawl_cost:.2f}")
        logger.info(f"   Total Savings: ${firecrawl_cost:.2f} (100%)")
        
        # Save report
        report_data = {
            'session_info': {
                'retailer': self.config['name'],
                'retailer_code': self.config['code'],
                'start_time': self.stats['start_time'].isoformat(),
                'end_time': end_time.isoformat(),
                'duration': duration
            },
            'statistics': self.stats,
            'metrics': {
                'success_rate': success_rate,
                'block_rate': block_rate,
                'encoding_error_rate': encoding_error_rate,
                'avg_response_time': avg_response_time
            },
            'sample_results': self.results[:5]  # First 5 results
        }
        
        report_file = f"enhanced_report_{self.config['code']}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report_data, f, indent=2, ensure_ascii=False, default=str)
        
        logger.info(f"\n📄 Detailed report saved: {report_file}")
        logger.info(f"🎯 Enhanced scraping session completed!")
        
        if success_rate > 60:
            logger.info(f"🚀 System is ready for production scraping!")
        else:
            logger.info(f"⚠️  System needs optimization before production use")


async def main():
    """Main function"""
    parser = argparse.ArgumentParser(description='Enhanced Native Scraping System')
    parser.add_argument('--retailer', '-r', default='HP', 
                       choices=['HP', 'TWD'],
                       help='Retailer code (default: HP)')
    parser.add_argument('--mode', '-m', default='test',
                       choices=['test', 'explore'],
                       help='Scraping mode (default: test)')
    parser.add_argument('--limit', '-l', type=int, default=3,
                       help='Limit number of URLs to test (default: 3)')
    parser.add_argument('--verbose', '-v', action='store_true',
                       help='Verbose logging')
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    scraper = EnhancedNativeScraper(retailer_code=args.retailer)
    await scraper.run_enhanced_session(mode=args.mode, limit=args.limit)


if __name__ == "__main__":
    asyncio.run(main())