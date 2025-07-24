#!/usr/bin/env python3
"""
Demo script for native scraping of HomePro website
Shows how to use the existing native scraping infrastructure
"""
import asyncio
import logging
import sys
from pathlib import Path
from typing import List, Dict, Any
import json
from datetime import datetime

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from config.retailers import retailer_manager, RetailerType
from scrapers.strategies.native_strategy import NativeStrategy
from scrapers.strategies.hybrid_strategy import HybridStrategy
from scrapers.strategy_factory import StrategyFactory

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class HomeProNativeScraper:
    """Demo class for native scraping of HomePro website"""
    
    def __init__(self):
        retailer_config_obj = retailer_manager.get_retailer_by_code('HP')
        # Convert to dictionary format expected by strategies
        self.retailer_config = {
            'name': retailer_config_obj.name,
            'code': retailer_config_obj.code,
            'base_url': retailer_config_obj.base_url,
            'category_urls': retailer_config_obj.category_urls,
            'product_url_patterns': retailer_config_obj.product_url_patterns,
            'estimated_products': retailer_config_obj.estimated_products,
            'rate_limit_delay': retailer_config_obj.rate_limit_delay,
            'max_concurrent': retailer_config_obj.max_concurrent,
            'timeout': retailer_config_obj.timeout,
            'primary_strategy': retailer_config_obj.primary_strategy,
            'fallback_strategy': retailer_config_obj.fallback_strategy,
            'success_rate_threshold': retailer_config_obj.success_rate_threshold,
            'response_time_threshold': retailer_config_obj.response_time_threshold
        }
        self.strategy = None
        self.results = []
    
    async def initialize(self):
        """Initialize the scraping strategy"""
        logger.info("Initializing HomePro native scraper...")
        
        # Force native strategy for this demo
        self.strategy = NativeStrategy(self.retailer_config)
        
        # Test connection
        connection_ok = await self.strategy.test_connection()
        if connection_ok:
            logger.info("✅ Native scraping connection test passed")
        else:
            logger.warning("⚠️  Native scraping connection test failed")
        
        return connection_ok
    
    async def scrape_sample_products(self) -> List[Dict[str, Any]]:
        """Scrape sample HomePro products"""
        logger.info("Starting HomePro native scraping demo...")
        
        # Sample HomePro product URLs for testing
        sample_urls = [
            "https://www.homepro.co.th/p/hammer-drill-set-10mm-500w-black-decker-hd500k2-a50-1/1000000000026",
            "https://www.homepro.co.th/p/electric-drill-10mm-450w-black-decker-kr454re-a50-1/1000000000027",
            "https://www.homepro.co.th/p/circular-saw-7-1/4-1200w-black-decker-cs1214-a50-1/1000000000028"
        ]
        
        results = []
        
        for i, url in enumerate(sample_urls, 1):
            logger.info(f"Scraping product {i}/{len(sample_urls)}: {url}")
            
            try:
                # Scrape product using native strategy
                result = await self.strategy.scrape_product(url)
                
                if result.success:
                    logger.info(f"✅ Successfully scraped product {i}")
                    logger.info(f"   Strategy: {result.strategy_used}")
                    logger.info(f"   Response time: {result.response_time:.2f}s")
                    
                    # Extract key information
                    product_data = result.data
                    if product_data:
                        logger.info(f"   Product name: {product_data.get('name', 'N/A')}")
                        logger.info(f"   Price: {product_data.get('price', 'N/A')}")
                        logger.info(f"   Brand: {product_data.get('brand', 'N/A')}")
                        logger.info(f"   Availability: {product_data.get('availability', 'N/A')}")
                else:
                    logger.error(f"❌ Failed to scrape product {i}: {result.error}")
                
                results.append({
                    'url': url,
                    'success': result.success,
                    'data': result.data,
                    'error': result.error,
                    'response_time': result.response_time,
                    'strategy_used': result.strategy_used
                })
                
                # Small delay between requests
                await asyncio.sleep(2)
                
            except Exception as e:
                logger.error(f"❌ Exception scraping product {i}: {str(e)}")
                results.append({
                    'url': url,
                    'success': False,
                    'error': str(e),
                    'response_time': 0,
                    'strategy_used': 'native'
                })
        
        return results
    
    async def scrape_category_sample(self) -> Dict[str, Any]:
        """Scrape a sample HomePro category"""
        logger.info("Scraping sample HomePro category...")
        
        # Sample category URL
        category_url = "https://www.homepro.co.th/c/power-tools"
        
        try:
            result = await self.strategy.scrape_category(category_url, max_pages=2)
            
            if result.success:
                logger.info("✅ Successfully scraped category")
                logger.info(f"   Strategy: {result.strategy_used}")
                logger.info(f"   Response time: {result.response_time:.2f}s")
                
                category_data = result.data
                if category_data:
                    product_urls = category_data.get('product_urls', [])
                    logger.info(f"   Found {len(product_urls)} product URLs")
                    
                    # Show first few URLs
                    for i, url in enumerate(product_urls[:5], 1):
                        logger.info(f"   Product {i}: {url}")
                    
                    if len(product_urls) > 5:
                        logger.info(f"   ... and {len(product_urls) - 5} more")
            else:
                logger.error(f"❌ Failed to scrape category: {result.error}")
            
            return {
                'url': category_url,
                'success': result.success,
                'data': result.data,
                'error': result.error,
                'response_time': result.response_time,
                'strategy_used': result.strategy_used
            }
            
        except Exception as e:
            logger.error(f"❌ Exception scraping category: {str(e)}")
            return {
                'url': category_url,
                'success': False,
                'error': str(e),
                'response_time': 0,
                'strategy_used': 'native'
            }
    
    async def test_search_functionality(self) -> Dict[str, Any]:
        """Test search functionality"""
        logger.info("Testing HomePro search functionality...")
        
        search_query = "hammer drill"
        
        try:
            result = await self.strategy.scrape_search(search_query, max_pages=1)
            
            if result.success:
                logger.info("✅ Successfully performed search")
                logger.info(f"   Strategy: {result.strategy_used}")
                logger.info(f"   Response time: {result.response_time:.2f}s")
                
                search_data = result.data
                if search_data:
                    product_urls = search_data.get('product_urls', [])
                    logger.info(f"   Found {len(product_urls)} search results")
            else:
                logger.error(f"❌ Failed to perform search: {result.error}")
            
            return {
                'query': search_query,
                'success': result.success,
                'data': result.data,
                'error': result.error,
                'response_time': result.response_time,
                'strategy_used': result.strategy_used
            }
            
        except Exception as e:
            logger.error(f"❌ Exception during search: {str(e)}")
            return {
                'query': search_query,
                'success': False,
                'error': str(e),
                'response_time': 0,
                'strategy_used': 'native'
            }
    
    async def compare_with_hybrid_strategy(self) -> Dict[str, Any]:
        """Compare native vs hybrid strategy performance"""
        logger.info("Comparing native vs hybrid strategy performance...")
        
        # Sample product URL
        test_url = "https://www.homepro.co.th/p/hammer-drill-set-10mm-500w-black-decker-hd500k2-a50-1/1000000000026"
        
        results = {}
        
        # Test native strategy
        try:
            native_result = await self.strategy.scrape_product(test_url)
            results['native'] = {
                'success': native_result.success,
                'response_time': native_result.response_time,
                'strategy_used': native_result.strategy_used,
                'data_extracted': bool(native_result.data.get('name')) if native_result.data else False
            }
            logger.info(f"Native strategy: {native_result.response_time:.2f}s, Success: {native_result.success}")
        except Exception as e:
            results['native'] = {'error': str(e), 'success': False}
            logger.error(f"Native strategy failed: {str(e)}")
        
        # Test hybrid strategy
        try:
            hybrid_strategy = HybridStrategy(self.retailer_config)
            hybrid_result = await hybrid_strategy.scrape_product(test_url)
            results['hybrid'] = {
                'success': hybrid_result.success,
                'response_time': hybrid_result.response_time,
                'strategy_used': hybrid_result.strategy_used,
                'data_extracted': bool(hybrid_result.data.get('name')) if hybrid_result.data else False,
                'fallback_used': hybrid_result.metadata.get('fallback_used', False)
            }
            logger.info(f"Hybrid strategy: {hybrid_result.response_time:.2f}s, Success: {hybrid_result.success}")
            
            await hybrid_strategy.close()
            
        except Exception as e:
            results['hybrid'] = {'error': str(e), 'success': False}
            logger.error(f"Hybrid strategy failed: {str(e)}")
        
        return results
    
    async def generate_report(self, results: Dict[str, Any]) -> str:
        """Generate a comprehensive scraping report"""
        report = {
            'timestamp': datetime.now().isoformat(),
            'retailer': 'HomePro',
            'strategy': 'Native Scraping',
            'results': results,
            'summary': {
                'total_attempts': 0,
                'successful_attempts': 0,
                'failed_attempts': 0,
                'average_response_time': 0,
                'success_rate': 0
            }
        }
        
        # Calculate summary statistics
        all_results = []
        if 'products' in results:
            all_results.extend(results['products'])
        if 'category' in results:
            all_results.append(results['category'])
        if 'search' in results:
            all_results.append(results['search'])
        
        if all_results:
            report['summary']['total_attempts'] = len(all_results)
            report['summary']['successful_attempts'] = sum(1 for r in all_results if r.get('success'))
            report['summary']['failed_attempts'] = report['summary']['total_attempts'] - report['summary']['successful_attempts']
            
            response_times = [r.get('response_time', 0) for r in all_results if r.get('response_time')]
            if response_times:
                report['summary']['average_response_time'] = sum(response_times) / len(response_times)
            
            report['summary']['success_rate'] = (report['summary']['successful_attempts'] / report['summary']['total_attempts']) * 100
        
        # Save report
        report_path = Path(__file__).parent / 'reports' / f'homepro_native_scraping_report_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
        report_path.parent.mkdir(exist_ok=True)
        
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        logger.info(f"📊 Report saved to: {report_path}")
        return str(report_path)
    
    async def close(self):
        """Close the scraper and clean up resources"""
        if self.strategy:
            await self.strategy.close()
        logger.info("HomePro native scraper closed")


async def main():
    """Main demo function"""
    logger.info("🚀 Starting HomePro Native Scraping Demo")
    logger.info("="*50)
    
    scraper = HomeProNativeScraper()
    
    try:
        # Initialize scraper
        if not await scraper.initialize():
            logger.error("Failed to initialize scraper")
            return
        
        # Run all tests
        all_results = {}
        
        # Test 1: Scrape sample products
        logger.info("\n📦 Test 1: Scraping sample products")
        all_results['products'] = await scraper.scrape_sample_products()
        
        # Test 2: Scrape category
        logger.info("\n📂 Test 2: Scraping category")
        all_results['category'] = await scraper.scrape_category_sample()
        
        # Test 3: Test search
        logger.info("\n🔍 Test 3: Testing search functionality")
        all_results['search'] = await scraper.test_search_functionality()
        
        # Test 4: Compare strategies
        logger.info("\n⚔️  Test 4: Comparing native vs hybrid strategies")
        all_results['strategy_comparison'] = await scraper.compare_with_hybrid_strategy()
        
        # Generate report
        logger.info("\n📊 Generating comprehensive report")
        report_path = await scraper.generate_report(all_results)
        
        # Print summary
        logger.info("\n🎯 DEMO SUMMARY")
        logger.info("="*50)
        
        # Products summary
        products = all_results.get('products', [])
        if products:
            successful_products = sum(1 for p in products if p.get('success'))
            logger.info(f"Products scraped: {successful_products}/{len(products)}")
            
            avg_time = sum(p.get('response_time', 0) for p in products) / len(products)
            logger.info(f"Average response time: {avg_time:.2f}s")
        
        # Category summary
        category = all_results.get('category', {})
        if category.get('success'):
            product_count = len(category.get('data', {}).get('product_urls', []))
            logger.info(f"Category products found: {product_count}")
        
        # Search summary
        search = all_results.get('search', {})
        if search.get('success'):
            search_count = len(search.get('data', {}).get('product_urls', []))
            logger.info(f"Search results found: {search_count}")
        
        # Strategy comparison
        comparison = all_results.get('strategy_comparison', {})
        if comparison:
            logger.info(f"Strategy comparison:")
            for strategy, result in comparison.items():
                status = "✅" if result.get('success') else "❌"
                time_str = f"{result.get('response_time', 0):.2f}s" if result.get('response_time') else "N/A"
                logger.info(f"  {strategy}: {status} {time_str}")
        
        logger.info(f"\n📄 Full report available at: {report_path}")
        
        # Cost comparison
        logger.info("\n💰 COST COMPARISON")
        logger.info("="*50)
        logger.info("Native scraping: $0.00 (No API costs)")
        logger.info("Firecrawl API: ~$0.01-0.05 per request")
        logger.info("Potential savings: 100% API cost reduction")
        
        logger.info("\n✅ HomePro native scraping demo completed successfully!")
        
    except Exception as e:
        logger.error(f"❌ Demo failed: {str(e)}")
        import traceback
        traceback.print_exc()
        
    finally:
        await scraper.close()


if __name__ == "__main__":
    asyncio.run(main())