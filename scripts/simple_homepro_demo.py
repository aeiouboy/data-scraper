#!/usr/bin/env python3
"""
Simple demonstration of HomePro native scraping
Shows basic functionality without complex imports
"""
import asyncio
import logging
import sys
import aiohttp
from pathlib import Path
from typing import Dict, Any, Optional
from bs4 import BeautifulSoup
import time
import random
from urllib.parse import urljoin
import re

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class SimpleHomeProScraper:
    """Simple HomePro native scraper demonstration"""
    
    def __init__(self):
        self.base_url = "https://www.homepro.co.th"
        self.session = None
        self.stats = {
            'requests_made': 0,
            'successful_requests': 0,
            'failed_requests': 0,
            'total_response_time': 0
        }
        
        # Simple user agents for rotation
        self.user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:120.0) Gecko/20100101 Firefox/120.0"
        ]
    
    async def create_session(self):
        """Create HTTP session with proper headers"""
        headers = {
            'User-Agent': random.choice(self.user_agents),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'th-TH,th;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        }
        
        timeout = aiohttp.ClientTimeout(total=30)
        connector = aiohttp.TCPConnector(limit=10)
        
        self.session = aiohttp.ClientSession(
            headers=headers,
            timeout=timeout,
            connector=connector
        )
        
        logger.info(f"Created session with User-Agent: {headers['User-Agent'][:50]}...")
    
    async def fetch_url(self, url: str) -> Optional[str]:
        """Fetch URL and return HTML content"""
        if not self.session:
            await self.create_session()
        
        start_time = time.time()
        self.stats['requests_made'] += 1
        
        try:
            async with self.session.get(url) as response:
                response_time = time.time() - start_time
                self.stats['total_response_time'] += response_time
                
                if response.status == 200:
                    content = await response.text()
                    self.stats['successful_requests'] += 1
                    logger.info(f"✅ Fetched {url} in {response_time:.2f}s")
                    return content
                else:
                    logger.warning(f"❌ HTTP {response.status} for {url}")
                    self.stats['failed_requests'] += 1
                    return None
                    
        except Exception as e:
            response_time = time.time() - start_time
            self.stats['total_response_time'] += response_time
            self.stats['failed_requests'] += 1
            logger.error(f"❌ Error fetching {url}: {str(e)}")
            return None
    
    def extract_product_data(self, html: str, url: str) -> Dict[str, Any]:
        """Extract product data from HTML"""
        soup = BeautifulSoup(html, 'html.parser')
        
        product_data = {
            'url': url,
            'scraped_at': time.time(),
            'retailer': 'HomePro',
            'scraping_method': 'native'
        }
        
        # Extract product name
        name_selectors = [
            'h1.product-title',
            '.product-name h1',
            'h1[data-testid="product-title"]',
            '.pdp-product-title h1',
            'h1'
        ]
        
        for selector in name_selectors:
            element = soup.select_one(selector)
            if element:
                product_data['name'] = element.get_text(strip=True)
                break
        
        # Extract price
        price_selectors = [
            '.price-current .price-value',
            '.product-price .current-price',
            '.price-display .final-price',
            '[data-testid="price-current"]'
        ]
        
        for selector in price_selectors:
            element = soup.select_one(selector)
            if element:
                price_text = element.get_text(strip=True)
                # Extract numeric price
                price_match = re.search(r'([0-9,]+(?:\.[0-9]{1,2})?)', price_text)
                if price_match:
                    try:
                        product_data['price'] = float(price_match.group(1).replace(',', ''))
                    except ValueError:
                        pass
                break
        
        # Extract brand
        brand_selectors = [
            '.product-brand',
            '.brand-name',
            '[data-testid="brand-name"]',
            '.pdp-brand-name'
        ]
        
        for selector in brand_selectors:
            element = soup.select_one(selector)
            if element:
                product_data['brand'] = element.get_text(strip=True)
                break
        
        # Extract availability
        availability_selectors = [
            '.stock-status',
            '.availability-status',
            '.product-availability',
            '[data-testid="stock-status"]'
        ]
        
        for selector in availability_selectors:
            element = soup.select_one(selector)
            if element:
                availability_text = element.get_text(strip=True).lower()
                if 'มีสินค้า' in availability_text or 'in stock' in availability_text:
                    product_data['availability'] = 'in_stock'
                elif 'หมดสินค้า' in availability_text or 'out of stock' in availability_text:
                    product_data['availability'] = 'out_of_stock'
                else:
                    product_data['availability'] = 'unknown'
                break
        
        # Extract images
        image_selectors = [
            '.product-gallery img',
            '.product-images img',
            '.image-gallery img',
            '.pdp-gallery img'
        ]
        
        images = []
        for selector in image_selectors:
            elements = soup.select(selector)
            for element in elements:
                src = element.get('src') or element.get('data-src')
                if src:
                    full_url = urljoin(url, src)
                    if full_url not in images:
                        images.append(full_url)
        
        product_data['images'] = images[:5]  # Limit to 5 images
        
        return product_data
    
    def extract_category_links(self, html: str, base_url: str) -> list:
        """Extract product links from category page"""
        soup = BeautifulSoup(html, 'html.parser')
        
        product_links = []
        
        # Common selectors for product links
        link_selectors = [
            '.product-item a',
            '.product-card a',
            '.item-link',
            '.product-tile a',
            'a[href*="/p/"]',
            'a[href*="/product/"]'
        ]
        
        for selector in link_selectors:
            elements = soup.select(selector)
            for element in elements:
                href = element.get('href')
                if href:
                    full_url = urljoin(base_url, href)
                    if '/p/' in full_url and full_url not in product_links:
                        product_links.append(full_url)
        
        return product_links
    
    async def scrape_product(self, url: str) -> Dict[str, Any]:
        """Scrape a single product"""
        logger.info(f"🔍 Scraping product: {url}")
        
        html = await self.fetch_url(url)
        if not html:
            return {
                'url': url,
                'success': False,
                'error': 'Failed to fetch HTML'
            }
        
        try:
            product_data = self.extract_product_data(html, url)
            
            # Check if we got meaningful data
            if product_data.get('name'):
                logger.info(f"✅ Product: {product_data['name']}")
                if product_data.get('price'):
                    logger.info(f"   Price: ฿{product_data['price']:,.2f}")
                if product_data.get('brand'):
                    logger.info(f"   Brand: {product_data['brand']}")
                if product_data.get('availability'):
                    logger.info(f"   Availability: {product_data['availability']}")
                
                return {
                    'url': url,
                    'success': True,
                    'data': product_data
                }
            else:
                logger.warning(f"⚠️  No product data extracted from {url}")
                return {
                    'url': url,
                    'success': False,
                    'error': 'No product data extracted'
                }
                
        except Exception as e:
            logger.error(f"❌ Error parsing product data: {str(e)}")
            return {
                'url': url,
                'success': False,
                'error': str(e)
            }
    
    async def scrape_category(self, url: str) -> Dict[str, Any]:
        """Scrape a category page"""
        logger.info(f"📂 Scraping category: {url}")
        
        html = await self.fetch_url(url)
        if not html:
            return {
                'url': url,
                'success': False,
                'error': 'Failed to fetch HTML'
            }
        
        try:
            product_links = self.extract_category_links(html, url)
            
            logger.info(f"✅ Found {len(product_links)} product links")
            
            # Show first few links
            for i, link in enumerate(product_links[:3], 1):
                logger.info(f"   {i}. {link}")
            
            if len(product_links) > 3:
                logger.info(f"   ... and {len(product_links) - 3} more")
            
            return {
                'url': url,
                'success': True,
                'data': {
                    'product_links': product_links,
                    'total_products': len(product_links)
                }
            }
            
        except Exception as e:
            logger.error(f"❌ Error parsing category data: {str(e)}")
            return {
                'url': url,
                'success': False,
                'error': str(e)
            }
    
    async def run_demo(self):
        """Run the complete demo"""
        logger.info("🚀 Starting HomePro Native Scraping Demo")
        logger.info("=" * 60)
        
        try:
            # Test 1: Scrape a category page
            logger.info("\n📂 Test 1: Scraping Power Tools Category")
            category_url = "https://www.homepro.co.th/c/power-tools"
            category_result = await self.scrape_category(category_url)
            
            # Small delay between requests
            await asyncio.sleep(2)
            
            # Test 2: Scrape sample products
            logger.info("\n📦 Test 2: Scraping Sample Products")
            
            # Get some product URLs from category or use hardcoded ones
            sample_urls = []
            if category_result['success']:
                sample_urls = category_result['data']['product_links'][:3]
            
            # Fallback to hardcoded URLs if needed
            if not sample_urls:
                sample_urls = [
                    "https://www.homepro.co.th/p/hammer-drill-set-10mm-500w-black-decker-hd500k2-a50-1",
                    "https://www.homepro.co.th/p/electric-drill-10mm-450w-black-decker-kr454re-a50-1",
                    "https://www.homepro.co.th/p/circular-saw-7-1-4-1200w-black-decker-cs1214-a50-1"
                ]
            
            product_results = []
            for i, url in enumerate(sample_urls, 1):
                result = await self.scrape_product(url)
                product_results.append(result)
                
                # Delay between requests
                await asyncio.sleep(2)
            
            # Generate summary
            logger.info("\n📊 DEMO SUMMARY")
            logger.info("=" * 60)
            
            # Category summary
            if category_result['success']:
                logger.info(f"Category scraping: ✅ SUCCESS")
                logger.info(f"  Products found: {category_result['data']['total_products']}")
            else:
                logger.info(f"Category scraping: ❌ FAILED")
                logger.info(f"  Error: {category_result['error']}")
            
            # Product summary
            successful_products = sum(1 for r in product_results if r['success'])
            logger.info(f"Product scraping: {successful_products}/{len(product_results)} successful")
            
            for i, result in enumerate(product_results, 1):
                if result['success']:
                    name = result['data'].get('name', 'Unknown')
                    price = result['data'].get('price', 0)
                    price_str = f"฿{price:,.2f}" if price else "N/A"
                    logger.info(f"  Product {i}: ✅ {name} - {price_str}")
                else:
                    logger.info(f"  Product {i}: ❌ {result['error']}")
            
            # Performance stats
            avg_response_time = self.stats['total_response_time'] / self.stats['requests_made'] if self.stats['requests_made'] > 0 else 0
            success_rate = (self.stats['successful_requests'] / self.stats['requests_made']) * 100 if self.stats['requests_made'] > 0 else 0
            
            logger.info(f"\n⚡ PERFORMANCE STATS")
            logger.info(f"Total requests: {self.stats['requests_made']}")
            logger.info(f"Successful requests: {self.stats['successful_requests']}")
            logger.info(f"Failed requests: {self.stats['failed_requests']}")
            logger.info(f"Average response time: {avg_response_time:.2f}s")
            logger.info(f"Success rate: {success_rate:.1f}%")
            
            # Cost comparison
            logger.info(f"\n💰 COST COMPARISON")
            logger.info(f"Native scraping cost: $0.00")
            logger.info(f"Firecrawl API cost (estimated): ${self.stats['requests_made'] * 0.02:.2f}")
            logger.info(f"Savings: 100% (${self.stats['requests_made'] * 0.02:.2f} saved)")
            
            logger.info("\n✅ Demo completed successfully!")
            
        except Exception as e:
            logger.error(f"❌ Demo failed: {str(e)}")
            import traceback
            traceback.print_exc()
        
        finally:
            await self.close()
    
    async def close(self):
        """Close the session"""
        if self.session:
            await self.session.close()
            logger.info("Session closed")


async def main():
    """Main demo function"""
    scraper = SimpleHomeProScraper()
    await scraper.run_demo()


if __name__ == "__main__":
    asyncio.run(main())