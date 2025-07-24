#!/usr/bin/env python3
"""
Production Native Scraping System
Start native scraping for HomePro and other Thai retailers with advanced anti-detection
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

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('production_scraping.log')
    ]
)
logger = logging.getLogger(__name__)

class ProductionNativeScraper:
    """Production-ready native scraper with advanced anti-detection"""
    
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
            'total_response_time': 0,
            'data_extracted': 0
        }
        
        # Advanced anti-detection measures
        self.user_agents = [
            # Real browser User-Agents from different regions
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:120.0) Gecko/20100101 Firefox/120.0",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:120.0) Gecko/20100101 Firefox/120.0",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0",
            # Thai-specific User-Agents
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 (compatible; Thailand)",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 (compatible; Bangkok)"
        ]
        
        self.accept_languages = [
            'th-TH,th;q=0.9,en;q=0.8',
            'th-TH,th;q=0.9,en-US;q=0.8,en;q=0.7',
            'th,en-US;q=0.9,en;q=0.8',
            'th-TH,th;q=0.9,en-GB;q=0.8,en;q=0.7'
        ]
        
        # Request delay randomization
        self.base_delay = self.config.get('rate_limit_delay', 2.0)
        self.delay_variance = 0.5  # ±0.5 seconds
        
    def get_retailer_config(self) -> Dict[str, Any]:
        """Get retailer configuration with production settings"""
        configs = {
            'HP': {
                'name': 'HomePro',
                'code': 'HP',
                'base_url': 'https://www.homepro.co.th',
                'rate_limit_delay': 2.0,  # Conservative for production
                'max_concurrent': 2,      # Very conservative
                'timeout': 30,
                'retry_attempts': 3,
                'success_rate_threshold': 0.7,
                'test_urls': [
                    'https://www.homepro.co.th',  # Start with homepage
                    'https://www.homepro.co.th/sitemap'  # Then try sitemap
                ],
                'selectors': {
                    'product_name': [
                        'h1.product-title',
                        '.product-name h1',
                        'h1[data-testid="product-title"]',
                        '.pdp-product-title h1',
                        'h1'
                    ],
                    'price': [
                        '.price-current .price-value',
                        '.product-price .current-price',
                        '.price-display .final-price',
                        '[data-testid="price-current"]',
                        '.price'
                    ],
                    'product_links': [
                        '.product-item a',
                        '.product-card a',
                        '.item-link',
                        '.product-tile a',
                        'a[href*="/p/"]'
                    ]
                }
            },
            'TWD': {
                'name': 'Thai Watsadu',
                'code': 'TWD',
                'base_url': 'https://www.thaiwatsadu.com',
                'rate_limit_delay': 2.5,
                'max_concurrent': 1,
                'timeout': 35,
                'retry_attempts': 3,
                'test_urls': [
                    'https://www.thaiwatsadu.com',
                    'https://www.thaiwatsadu.com/th'
                ]
            }
        }
        return configs.get(self.retailer_code, configs['HP'])
    
    def get_random_headers(self) -> Dict[str, str]:
        """Generate randomized headers for each request"""
        return {
            'User-Agent': random.choice(self.user_agents),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
            'Accept-Language': random.choice(self.accept_languages),
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-User': '?1',
            'Cache-Control': 'max-age=0',
            'DNT': '1',
            'Sec-GPC': '1'
        }
    
    async def create_session(self):
        """Create HTTP session with advanced settings"""
        connector = aiohttp.TCPConnector(
            limit=self.config['max_concurrent'],
            limit_per_host=self.config['max_concurrent'],
            ttl_dns_cache=300,
            use_dns_cache=True,
            keepalive_timeout=60,
            enable_cleanup_closed=True,
            ssl=False  # For sites with SSL issues
        )
        
        timeout = aiohttp.ClientTimeout(
            total=self.config['timeout'],
            connect=15,
            sock_read=20
        )
        
        self.session = aiohttp.ClientSession(
            connector=connector,
            timeout=timeout,
            headers=self.get_random_headers(),
            cookie_jar=aiohttp.CookieJar(unsafe=True),
            trust_env=True
        )
        
        logger.info(f"🔧 Created session for {self.config['name']}")
    
    async def random_delay(self):
        """Add randomized delay between requests"""
        delay = self.base_delay + random.uniform(-self.delay_variance, self.delay_variance)
        delay = max(0.5, delay)  # Minimum 0.5 seconds
        await asyncio.sleep(delay)
    
    async def scrape_url(self, url: str) -> Dict[str, Any]:
        """Scrape a single URL with advanced error handling"""
        if not self.session:
            await self.create_session()
        
        self.stats['total_requests'] += 1
        start_time = time.time()
        
        for attempt in range(self.config.get('retry_attempts', 3)):
            try:
                # Rotate User-Agent for each attempt
                self.session.headers.update(self.get_random_headers())
                
                async with self.session.get(url) as response:
                    response_time = time.time() - start_time
                    self.stats['total_response_time'] += response_time
                    
                    logger.info(f"📡 {url} - Status: {response.status} - Time: {response_time:.2f}s")
                    
                    if response.status == 200:
                        content = await response.text()
                        
                        # Check for common blocking indicators
                        if self.is_blocked(content, response):
                            logger.warning(f"🚫 Detected blocking/captcha for {url}")
                            self.stats['blocked_requests'] += 1
                            
                            # Wait longer before retry
                            await asyncio.sleep(random.uniform(10, 20))
                            continue
                        
                        # Parse content
                        data = await self.parse_content(content, url)
                        
                        if data:
                            self.stats['successful_requests'] += 1
                            self.stats['data_extracted'] += 1
                            
                            return {
                                'success': True,
                                'data': data,
                                'response_time': response_time,
                                'attempt': attempt + 1
                            }
                    
                    elif response.status in [403, 429, 503]:
                        logger.warning(f"⚠️ Rate limited/blocked: {response.status} for {url}")
                        self.stats['blocked_requests'] += 1
                        
                        # Exponential backoff
                        wait_time = (2 ** attempt) * random.uniform(5, 15)
                        logger.info(f"⏰ Waiting {wait_time:.1f}s before retry...")
                        await asyncio.sleep(wait_time)
                        continue
                    
                    else:
                        logger.error(f"❌ HTTP {response.status} for {url}")
                        
            except asyncio.TimeoutError:
                logger.error(f"⏱️ Timeout for {url} (attempt {attempt + 1})")
                await asyncio.sleep(random.uniform(5, 10))
                continue
                
            except Exception as e:
                logger.error(f"❌ Error scraping {url}: {str(e)}")
                await asyncio.sleep(random.uniform(2, 5))
                continue
        
        # All attempts failed
        response_time = time.time() - start_time
        self.stats['failed_requests'] += 1
        
        return {
            'success': False,
            'error': 'All retry attempts failed',
            'response_time': response_time,
            'attempts': self.config.get('retry_attempts', 3)
        }
    
    def is_blocked(self, content: str, response) -> bool:
        """Detect if request was blocked or captcha'd"""
        content_lower = content.lower()
        
        # Common blocking indicators
        blocking_indicators = [
            'captcha',
            'cloudflare',
            'access denied',
            'forbidden',
            'blocked',
            'security check',
            'bot detection',
            'rate limit',
            'unusual traffic',
            'verify you are human'
        ]
        
        for indicator in blocking_indicators:
            if indicator in content_lower:
                return True
        
        # Check for suspicious redirects
        if len(content) < 1000 and ('redirect' in content_lower or 'loading' in content_lower):
            return True
        
        # Check for minimal content (likely error page)
        if len(content) < 500:
            return True
        
        return False
    
    async def parse_content(self, content: str, url: str) -> Optional[Dict[str, Any]]:
        """Parse content and extract data"""
        try:
            soup = BeautifulSoup(content, 'html.parser')
            
            data = {
                'url': url,
                'scraped_at': datetime.now().isoformat(),
                'content_length': len(content),
                'strategy': 'production_native'
            }
            
            # Extract title
            title = soup.find('title')
            if title:
                data['title'] = title.get_text(strip=True)
            
            # Extract meta description
            meta_desc = soup.find('meta', {'name': 'description'})
            if meta_desc:
                data['meta_description'] = meta_desc.get('content', '')
            
            # Try to determine page type
            if '/p/' in url or '/product/' in url:
                data['page_type'] = 'product'
                product_data = self.extract_product_data(soup)
                data.update(product_data)
            elif '/c/' in url or '/category/' in url:
                data['page_type'] = 'category'
                category_data = self.extract_category_data(soup, url)
                data.update(category_data)
            else:
                data['page_type'] = 'other'
                # Extract basic info
                data['links_found'] = len(soup.find_all('a', href=True))
                data['images_found'] = len(soup.find_all('img'))
            
            return data
            
        except Exception as e:
            logger.error(f"Error parsing content from {url}: {str(e)}")
            return None
    
    def extract_product_data(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """Extract product-specific data"""
        data = {}
        
        # Extract product name
        for selector in self.config['selectors']['product_name']:
            element = soup.select_one(selector)
            if element:
                data['product_name'] = element.get_text(strip=True)
                break
        
        # Extract price
        for selector in self.config['selectors']['price']:
            element = soup.select_one(selector)
            if element:
                price_text = element.get_text(strip=True)
                # Extract Thai price
                price_match = re.search(r'฿\s*([0-9,]+(?:\.[0-9]+)?)', price_text)
                if price_match:
                    try:
                        data['price'] = float(price_match.group(1).replace(',', ''))
                    except ValueError:
                        pass
                break
        
        # Extract brand
        brand_selectors = ['.brand-name', '.product-brand', '[data-brand]']
        for selector in brand_selectors:
            element = soup.select_one(selector)
            if element:
                data['brand'] = element.get_text(strip=True)
                break
        
        # Extract availability
        availability_text = soup.get_text().lower()
        if 'มีสินค้า' in availability_text or 'in stock' in availability_text:
            data['availability'] = 'in_stock'
        elif 'หมดสินค้า' in availability_text or 'out of stock' in availability_text:
            data['availability'] = 'out_of_stock'
        
        return data
    
    def extract_category_data(self, soup: BeautifulSoup, url: str) -> Dict[str, Any]:
        """Extract category-specific data"""
        data = {}
        
        # Extract product links
        product_links = []
        for selector in self.config['selectors']['product_links']:
            elements = soup.select(selector)
            for element in elements:
                href = element.get('href')
                if href:
                    if href.startswith('/'):
                        href = self.config['base_url'] + href
                    if '/p/' in href and href not in product_links:
                        product_links.append(href)
        
        data['product_links'] = product_links[:50]  # Limit to first 50
        data['products_found'] = len(product_links)
        
        # Extract category name
        h1 = soup.find('h1')
        if h1:
            data['category_name'] = h1.get_text(strip=True)
        
        return data
    
    async def test_connectivity(self) -> bool:
        """Test connectivity to the retailer website"""
        logger.info(f"🔍 Testing connectivity to {self.config['name']}...")
        
        for test_url in self.config.get('test_urls', [self.config['base_url']]):
            logger.info(f"🌐 Testing: {test_url}")
            
            result = await self.scrape_url(test_url)
            
            if result['success']:
                logger.info(f"✅ Successfully connected to {test_url}")
                logger.info(f"   Title: {result['data'].get('title', 'N/A')}")
                logger.info(f"   Page type: {result['data'].get('page_type', 'N/A')}")
                logger.info(f"   Content length: {result['data'].get('content_length', 0):,} chars")
                return True
            else:
                logger.error(f"❌ Failed to connect to {test_url}: {result.get('error', 'Unknown error')}")
        
        return False
    
    async def run_production_session(self, mode: str = 'test', limit: int = 5):
        """Run production scraping session"""
        logger.info(f"🚀 Starting Production Native Scraping Session")
        logger.info(f"Retailer: {self.config['name']} ({self.config['code']})")
        logger.info(f"Mode: {mode}, Limit: {limit}")
        logger.info("=" * 80)
        
        try:
            # Test connectivity first
            if not await self.test_connectivity():
                logger.error("❌ Connectivity test failed. Aborting session.")
                return
            
            logger.info("✅ Connectivity test passed. Starting scraping...")
            
            # Add delay before starting actual scraping
            await asyncio.sleep(random.uniform(2, 5))
            
            if mode == 'test':
                await self.run_test_mode(limit)
            elif mode == 'category':
                await self.run_category_mode(limit)
            elif mode == 'product':
                await self.run_product_mode(limit)
            else:
                logger.error(f"Unknown mode: {mode}")
                return
            
            # Generate report
            await self.generate_production_report()
            
        except Exception as e:
            logger.error(f"❌ Production session failed: {str(e)}")
            import traceback
            traceback.print_exc()
        
        finally:
            if self.session:
                await self.session.close()
                logger.info("🔐 Session closed")
    
    async def run_test_mode(self, limit: int):
        """Run test mode with safe URLs"""
        logger.info("🧪 Running test mode...")
        
        test_urls = [
            self.config['base_url'],
            f"{self.config['base_url']}/about",
            f"{self.config['base_url']}/contact",
            f"{self.config['base_url']}/sitemap"
        ]
        
        for i, url in enumerate(test_urls[:limit], 1):
            logger.info(f"🔍 Test {i}/{min(limit, len(test_urls))}: {url}")
            
            result = await self.scrape_url(url)
            self.results.append(result)
            
            if result['success']:
                logger.info(f"✅ Success: {result['data'].get('title', 'N/A')}")
            else:
                logger.error(f"❌ Failed: {result.get('error', 'Unknown error')}")
            
            # Random delay between requests
            await self.random_delay()
    
    async def run_category_mode(self, limit: int):
        """Run category scraping mode"""
        logger.info("📂 Running category mode...")
        logger.info("⚠️  This mode may trigger anti-bot measures")
        
        # This would require actual category URLs
        # For now, just test the base category structure
        potential_categories = [
            f"{self.config['base_url']}/c/tools",
            f"{self.config['base_url']}/c/power-tools",
            f"{self.config['base_url']}/c/electrical",
            f"{self.config['base_url']}/c/plumbing",
            f"{self.config['base_url']}/c/paint"
        ]
        
        for i, url in enumerate(potential_categories[:limit], 1):
            logger.info(f"📂 Category {i}/{min(limit, len(potential_categories))}: {url}")
            
            result = await self.scrape_url(url)
            self.results.append(result)
            
            if result['success']:
                data = result['data']
                logger.info(f"✅ Success: {data.get('title', 'N/A')}")
                logger.info(f"   Products found: {data.get('products_found', 0)}")
            else:
                logger.error(f"❌ Failed: {result.get('error', 'Unknown error')}")
            
            # Longer delay for category pages
            await asyncio.sleep(random.uniform(3, 8))
    
    async def run_product_mode(self, limit: int):
        """Run product scraping mode"""
        logger.info("🛍️  Running product mode...")
        logger.info("⚠️  This mode requires valid product URLs")
        
        # This would require actual product URLs
        # For demo purposes, we'll just test the concept
        logger.info("📝 Product mode requires specific product URLs")
        logger.info("   Use category mode first to discover product URLs")
    
    async def generate_production_report(self):
        """Generate comprehensive production report"""
        logger.info("\n📊 PRODUCTION SCRAPING REPORT")
        logger.info("=" * 80)
        
        end_time = datetime.now()
        duration = (end_time - self.stats['start_time']).total_seconds()
        
        # Calculate metrics
        total_requests = self.stats['total_requests']
        success_rate = (self.stats['successful_requests'] / total_requests) * 100 if total_requests > 0 else 0
        block_rate = (self.stats['blocked_requests'] / total_requests) * 100 if total_requests > 0 else 0
        avg_response_time = self.stats['total_response_time'] / total_requests if total_requests > 0 else 0
        
        logger.info(f"📈 Performance Metrics:")
        logger.info(f"   Retailer: {self.config['name']}")
        logger.info(f"   Duration: {duration:.1f} seconds")
        logger.info(f"   Total Requests: {total_requests}")
        logger.info(f"   Successful: {self.stats['successful_requests']}")
        logger.info(f"   Failed: {self.stats['failed_requests']}")
        logger.info(f"   Blocked: {self.stats['blocked_requests']}")
        logger.info(f"   Success Rate: {success_rate:.1f}%")
        logger.info(f"   Block Rate: {block_rate:.1f}%")
        logger.info(f"   Avg Response Time: {avg_response_time:.2f}s")
        logger.info(f"   Data Extracted: {self.stats['data_extracted']}")
        
        # Anti-detection assessment
        logger.info(f"\n🛡️  Anti-Detection Assessment:")
        if block_rate == 0:
            logger.info(f"   ✅ No blocking detected")
        elif block_rate < 20:
            logger.info(f"   ⚠️  Low blocking rate ({block_rate:.1f}%)")
        else:
            logger.info(f"   ❌ High blocking rate ({block_rate:.1f}%)")
        
        # Recommendations
        logger.info(f"\n💡 Recommendations:")
        if success_rate > 80:
            logger.info(f"   ✅ Good success rate - can proceed with production")
        elif success_rate > 60:
            logger.info(f"   ⚠️  Moderate success rate - adjust delays and headers")
        else:
            logger.info(f"   ❌ Low success rate - significant anti-bot measures detected")
        
        if avg_response_time > 5:
            logger.info(f"   ⚠️  High response times - website may be slow or throttling")
        
        # Cost analysis
        firecrawl_cost = total_requests * 0.02
        native_cost = 0.00
        
        logger.info(f"\n💰 Cost Analysis:")
        logger.info(f"   Native Scraping: ${native_cost:.2f}")
        logger.info(f"   Firecrawl API: ${firecrawl_cost:.2f}")
        logger.info(f"   Total Savings: ${firecrawl_cost:.2f} (100%)")
        
        # Save detailed report
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
                'avg_response_time': avg_response_time
            },
            'results': self.results[:10]  # First 10 results only
        }
        
        report_file = f"production_report_{self.config['code']}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report_data, f, indent=2, ensure_ascii=False)
        
        logger.info(f"\n📄 Detailed report saved: {report_file}")
        logger.info(f"🎯 Production scraping session completed!")


async def main():
    """Main function with command line arguments"""
    parser = argparse.ArgumentParser(description='Production Native Scraping System')
    parser.add_argument('--retailer', '-r', default='HP', 
                       choices=['HP', 'TWD', 'GH', 'DH', 'BT', 'MH'],
                       help='Retailer code (default: HP)')
    parser.add_argument('--mode', '-m', default='test',
                       choices=['test', 'category', 'product'],
                       help='Scraping mode (default: test)')
    parser.add_argument('--limit', '-l', type=int, default=3,
                       help='Limit number of URLs to test (default: 3)')
    parser.add_argument('--verbose', '-v', action='store_true',
                       help='Verbose logging')
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Create and run scraper
    scraper = ProductionNativeScraper(retailer_code=args.retailer)
    await scraper.run_production_session(mode=args.mode, limit=args.limit)


if __name__ == "__main__":
    asyncio.run(main())