#!/usr/bin/env python3
"""
Production Native Scraping Runner
Start native scraping for HomePro and other Thai retailers
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

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('native_scraping.log')
    ]
)
logger = logging.getLogger(__name__)

class NativeScrapingRunner:
    """Production native scraping runner"""
    
    def __init__(self, retailer_code: str = 'HP'):
        self.retailer_code = retailer_code
        self.results = []
        self.stats = {
            'start_time': datetime.now(),
            'total_scraped': 0,
            'successful': 0,
            'failed': 0,
            'total_cost': 0.0,
            'avg_response_time': 0.0
        }
        
    def get_retailer_config(self) -> Dict[str, Any]:
        """Get retailer configuration"""
        configs = {
            'HP': {
                'name': 'HomePro',
                'code': 'HP',
                'base_url': 'https://www.homepro.co.th',
                'rate_limit_delay': 1.0,
                'max_concurrent': 3,  # Conservative for production
                'timeout': 30,
                'primary_strategy': 'native',
                'fallback_strategy': 'firecrawl',
                'success_rate_threshold': 0.8,
                'response_time_threshold': 10.0,
                'sample_urls': [
                    'https://www.homepro.co.th/c/power-tools',
                    'https://www.homepro.co.th/c/hand-tools',
                    'https://www.homepro.co.th/c/electrical',
                    'https://www.homepro.co.th/c/plumbing',
                    'https://www.homepro.co.th/c/paint'
                ]
            },
            'TWD': {
                'name': 'Thai Watsadu',
                'code': 'TWD',
                'base_url': 'https://www.thaiwatsadu.com',
                'rate_limit_delay': 1.0,
                'max_concurrent': 2,
                'timeout': 30,
                'primary_strategy': 'native',
                'fallback_strategy': 'firecrawl',
                'success_rate_threshold': 0.8,
                'response_time_threshold': 10.0,
                'sample_urls': [
                    'https://www.thaiwatsadu.com/th/c/tools',
                    'https://www.thaiwatsadu.com/th/c/electrical',
                    'https://www.thaiwatsadu.com/th/c/plumbing'
                ]
            }
        }
        return configs.get(self.retailer_code, configs['HP'])
    
    async def create_simple_scraper(self, config: Dict[str, Any]):
        """Create a simple scraper without complex imports"""
        import aiohttp
        from bs4 import BeautifulSoup
        import random
        import time
        
        class SimpleNativeScraper:
            def __init__(self, config):
                self.config = config
                self.session = None
                self.user_agents = [
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:120.0) Gecko/20100101 Firefox/120.0"
                ]
                
            async def create_session(self):
                headers = {
                    'User-Agent': random.choice(self.user_agents),
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                    'Accept-Language': 'th-TH,th;q=0.9,en;q=0.8',
                    'Accept-Encoding': 'gzip, deflate',
                    'Connection': 'keep-alive',
                    'Upgrade-Insecure-Requests': '1'
                }
                
                timeout = aiohttp.ClientTimeout(total=self.config['timeout'])
                connector = aiohttp.TCPConnector(limit=self.config['max_concurrent'])
                
                self.session = aiohttp.ClientSession(
                    headers=headers,
                    timeout=timeout,
                    connector=connector
                )
                
            async def scrape_url(self, url: str) -> Dict[str, Any]:
                if not self.session:
                    await self.create_session()
                
                start_time = time.time()
                
                try:
                    async with self.session.get(url) as response:
                        response_time = time.time() - start_time
                        
                        if response.status == 200:
                            content = await response.text()
                            
                            # Parse with BeautifulSoup
                            soup = BeautifulSoup(content, 'html.parser')
                            
                            # Extract basic data
                            data = {
                                'url': url,
                                'status': response.status,
                                'response_time': response_time,
                                'content_length': len(content),
                                'title': soup.title.string if soup.title else None,
                                'scraped_at': datetime.now().isoformat(),
                                'strategy': 'native',
                                'retailer': self.config['code']
                            }
                            
                            # Try to extract product links if it's a category page
                            if '/c/' in url:
                                product_links = []
                                for link in soup.find_all('a', href=True):
                                    href = link['href']
                                    if '/p/' in href and href not in product_links:
                                        if href.startswith('/'):
                                            href = self.config['base_url'] + href
                                        product_links.append(href)
                                
                                data['product_links'] = product_links[:20]  # Limit to first 20
                                data['total_products_found'] = len(product_links)
                            
                            # Try to extract product data if it's a product page
                            elif '/p/' in url:
                                # Extract product name
                                for selector in ['h1', '.product-title', '.product-name']:
                                    element = soup.select_one(selector)
                                    if element:
                                        data['product_name'] = element.get_text(strip=True)
                                        break
                                
                                # Extract price
                                price_text = soup.get_text()
                                import re
                                price_match = re.search(r'฿\s*([0-9,]+(?:\.[0-9]{1,2})?)', price_text)
                                if price_match:
                                    try:
                                        data['price'] = float(price_match.group(1).replace(',', ''))
                                    except ValueError:
                                        pass
                            
                            return {
                                'success': True,
                                'data': data,
                                'error': None
                            }
                        else:
                            return {
                                'success': False,
                                'data': {
                                    'url': url,
                                    'status': response.status,
                                    'response_time': response_time
                                },
                                'error': f'HTTP {response.status}'
                            }
                            
                except Exception as e:
                    response_time = time.time() - start_time
                    return {
                        'success': False,
                        'data': {
                            'url': url,
                            'response_time': response_time
                        },
                        'error': str(e)
                    }
                    
            async def close(self):
                if self.session:
                    await self.session.close()
        
        return SimpleNativeScraper(config)
    
    async def run_category_scraping(self, scraper, urls: List[str]) -> List[Dict[str, Any]]:
        """Run category scraping"""
        logger.info(f"🔍 Starting category scraping for {len(urls)} URLs")
        results = []
        
        for i, url in enumerate(urls, 1):
            logger.info(f"📂 Scraping category {i}/{len(urls)}: {url}")
            
            result = await scraper.scrape_url(url)
            results.append(result)
            
            if result['success']:
                data = result['data']
                logger.info(f"✅ Success: {data.get('title', 'Unknown')}")
                logger.info(f"   Response time: {data['response_time']:.2f}s")
                logger.info(f"   Products found: {data.get('total_products_found', 0)}")
                self.stats['successful'] += 1
            else:
                logger.error(f"❌ Failed: {result['error']}")
                self.stats['failed'] += 1
            
            self.stats['total_scraped'] += 1
            
            # Rate limiting
            await asyncio.sleep(scraper.config['rate_limit_delay'])
        
        return results
    
    async def run_product_scraping(self, scraper, product_urls: List[str]) -> List[Dict[str, Any]]:
        """Run product scraping"""
        logger.info(f"🛍️ Starting product scraping for {len(product_urls)} URLs")
        results = []
        
        for i, url in enumerate(product_urls, 1):
            logger.info(f"📦 Scraping product {i}/{len(product_urls)}: {url}")
            
            result = await scraper.scrape_url(url)
            results.append(result)
            
            if result['success']:
                data = result['data']
                logger.info(f"✅ Success: {data.get('product_name', 'Unknown Product')}")
                logger.info(f"   Response time: {data['response_time']:.2f}s")
                if data.get('price'):
                    logger.info(f"   Price: ฿{data['price']:,.2f}")
                self.stats['successful'] += 1
            else:
                logger.error(f"❌ Failed: {result['error']}")
                self.stats['failed'] += 1
            
            self.stats['total_scraped'] += 1
            
            # Rate limiting
            await asyncio.sleep(scraper.config['rate_limit_delay'])
        
        return results
    
    async def run_scraping_session(self, mode: str = 'category', limit: int = 5):
        """Run a complete scraping session"""
        logger.info(f"🚀 Starting {self.retailer_code} Native Scraping Session")
        logger.info(f"Mode: {mode}, Limit: {limit}")
        logger.info("=" * 60)
        
        # Get configuration
        config = self.get_retailer_config()
        logger.info(f"📋 Retailer: {config['name']} ({config['code']})")
        logger.info(f"🌐 Base URL: {config['base_url']}")
        logger.info(f"⏱️ Rate Limit: {config['rate_limit_delay']}s")
        logger.info(f"🔄 Max Concurrent: {config['max_concurrent']}")
        
        # Create scraper
        scraper = await self.create_simple_scraper(config)
        
        try:
            if mode == 'category':
                # Scrape categories
                urls = config['sample_urls'][:limit]
                category_results = await self.run_category_scraping(scraper, urls)
                
                # Collect product URLs from successful categories
                all_product_urls = []
                for result in category_results:
                    if result['success'] and result['data'].get('product_links'):
                        all_product_urls.extend(result['data']['product_links'][:5])  # 5 products per category
                
                # Scrape sample products
                if all_product_urls:
                    product_urls = all_product_urls[:limit]  # Limit total products
                    product_results = await self.run_product_scraping(scraper, product_urls)
                    self.results.extend(category_results + product_results)
                else:
                    logger.warning("No product URLs found in categories")
                    self.results.extend(category_results)
                    
            elif mode == 'product':
                # Direct product scraping (you'll need to provide product URLs)
                logger.info("Direct product scraping mode - implement with specific URLs")
                
            else:
                logger.error(f"Unknown mode: {mode}")
                return
            
            # Generate final report
            await self.generate_report()
            
        except Exception as e:
            logger.error(f"❌ Scraping session failed: {str(e)}")
            import traceback
            traceback.print_exc()
            
        finally:
            await scraper.close()
            logger.info("Session closed")
    
    async def generate_report(self):
        """Generate comprehensive scraping report"""
        logger.info("\n📊 SCRAPING SESSION REPORT")
        logger.info("=" * 60)
        
        # Calculate statistics
        end_time = datetime.now()
        duration = (end_time - self.stats['start_time']).total_seconds()
        
        success_rate = (self.stats['successful'] / self.stats['total_scraped']) * 100 if self.stats['total_scraped'] > 0 else 0
        
        # Calculate average response time
        total_response_time = sum(
            r['data']['response_time'] for r in self.results 
            if r['success'] and 'response_time' in r['data']
        )
        avg_response_time = total_response_time / len([r for r in self.results if r['success']]) if self.results else 0
        
        # Log statistics
        logger.info(f"📈 Session Statistics:")
        logger.info(f"   Duration: {duration:.1f} seconds")
        logger.info(f"   Total URLs: {self.stats['total_scraped']}")
        logger.info(f"   Successful: {self.stats['successful']}")
        logger.info(f"   Failed: {self.stats['failed']}")
        logger.info(f"   Success Rate: {success_rate:.1f}%")
        logger.info(f"   Avg Response Time: {avg_response_time:.2f}s")
        logger.info(f"   Requests/Second: {self.stats['total_scraped']/duration:.2f}")
        
        # Cost analysis
        firecrawl_cost = self.stats['total_scraped'] * 0.02  # Estimated $0.02 per request
        native_cost = 0.00
        savings = firecrawl_cost - native_cost
        
        logger.info(f"\n💰 Cost Analysis:")
        logger.info(f"   Native Scraping: ${native_cost:.2f}")
        logger.info(f"   Firecrawl API: ${firecrawl_cost:.2f}")
        logger.info(f"   Savings: ${savings:.2f} ({100:.0f}%)")
        
        # Save detailed report
        report_data = {
            'session_info': {
                'retailer': self.retailer_code,
                'start_time': self.stats['start_time'].isoformat(),
                'end_time': end_time.isoformat(),
                'duration_seconds': duration
            },
            'statistics': {
                'total_scraped': self.stats['total_scraped'],
                'successful': self.stats['successful'],
                'failed': self.stats['failed'],
                'success_rate': success_rate,
                'avg_response_time': avg_response_time,
                'requests_per_second': self.stats['total_scraped']/duration
            },
            'cost_analysis': {
                'native_cost': native_cost,
                'firecrawl_cost': firecrawl_cost,
                'savings': savings
            },
            'results': self.results
        }
        
        # Save to file
        report_file = f"scraping_report_{self.retailer_code}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report_data, f, indent=2, ensure_ascii=False)
        
        logger.info(f"\n📄 Detailed report saved to: {report_file}")
        logger.info("\n🎉 Native scraping session completed successfully!")


async def main():
    """Main function with command line arguments"""
    parser = argparse.ArgumentParser(description='Native Scraping Runner')
    parser.add_argument('--retailer', '-r', default='HP', 
                       choices=['HP', 'TWD', 'GH', 'DH', 'BT', 'MH'],
                       help='Retailer code (default: HP)')
    parser.add_argument('--mode', '-m', default='category',
                       choices=['category', 'product'],
                       help='Scraping mode (default: category)')
    parser.add_argument('--limit', '-l', type=int, default=5,
                       help='Limit number of URLs to scrape (default: 5)')
    parser.add_argument('--verbose', '-v', action='store_true',
                       help='Verbose logging')
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Create and run scraper
    runner = NativeScrapingRunner(retailer_code=args.retailer)
    await runner.run_scraping_session(mode=args.mode, limit=args.limit)


if __name__ == "__main__":
    asyncio.run(main())