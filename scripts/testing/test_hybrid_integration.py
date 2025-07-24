#!/usr/bin/env python3
"""
Test script for hybrid native/Firecrawl scraping integration
"""
import asyncio
import logging
from src.scrapers.homepro_scraper import HomeProScraper

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def test_hybrid_scraping():
    """Test the hybrid scraping integration"""
    
    print("🚀 Testing Hybrid Native/Firecrawl Scraping Integration")
    print("=" * 60)
    
    try:
        # Initialize scraper with hybrid strategy
        async with HomeProScraper(use_native=True) as scraper:
            print("✅ HomePro scraper initialized with hybrid strategy")
            
            # Test URL discovery
            print("\n📂 Testing URL discovery...")
            test_category_url = "https://www.homepro.co.th/c/APP"
            
            discovered_urls = await scraper.discover_product_urls(test_category_url, max_pages=1)
            print(f"🔍 Discovered {len(discovered_urls)} product URLs")
            
            if discovered_urls:
                # Test single product scraping
                print("\n📦 Testing single product scraping...")
                test_url = discovered_urls[0]
                print(f"🔗 Testing URL: {test_url}")
                
                result = await scraper.scrape_single_product(test_url)
                
                if result:
                    print("✅ Single product scraping successful!")
                    print(f"   Product: {result.get('title', 'N/A')}")
                    print(f"   Strategy: {result.get('scrape_strategy', 'N/A')}")
                    print(f"   Response time: {result.get('response_time', 'N/A'):.2f}s" if result.get('response_time') else "   Response time: N/A")
                else:
                    print("❌ Single product scraping failed")
                
                # Test batch scraping (small batch)
                if len(discovered_urls) > 1:
                    print("\n📦📦 Testing batch scraping...")
                    batch_urls = discovered_urls[:3]  # Test with 3 URLs
                    print(f"🔗 Testing {len(batch_urls)} URLs")
                    
                    batch_result = await scraper.scrape_batch(batch_urls, max_concurrent=2)
                    
                    print("✅ Batch scraping completed!")
                    print(f"   Total: {batch_result['total']}")
                    print(f"   Success: {batch_result['success']}")
                    print(f"   Failed: {batch_result['failed']}")
                    print(f"   Success rate: {batch_result['success_rate']:.1f}%")
            
            # Get scraping statistics
            print("\n📊 Getting scraping statistics...")
            stats = await scraper.get_scraping_stats()
            
            if 'strategy_stats' in stats and stats['strategy_stats']:
                print("📈 Strategy Statistics:")
                strategy_stats = stats['strategy_stats']
                
                # Show overall hybrid stats
                if 'overall_stats' in strategy_stats:
                    overall = strategy_stats['overall_stats']
                    print(f"   Overall Success Rate: {overall.get('success_rate', 0):.1f}%")
                    print(f"   Total Requests: {overall.get('total_requests', 0)}")
                    print(f"   Avg Response Time: {overall.get('avg_response_time', 0):.2f}s")
                
                # Show native vs Firecrawl breakdown
                if 'hybrid_session' in strategy_stats:
                    session = strategy_stats['hybrid_session']
                    print(f"   Native Attempts: {session.get('native_attempts', 0)}")
                    print(f"   Native Successes: {session.get('native_successes', 0)}")
                    print(f"   Firecrawl Attempts: {session.get('firecrawl_attempts', 0)}")
                    print(f"   Firecrawl Successes: {session.get('firecrawl_successes', 0)}")
                    print(f"   Fallback Triggers: {session.get('fallback_triggers', 0)}")
            
            print("\n🎉 Integration test completed successfully!")
            
    except Exception as e:
        print(f"❌ Integration test failed: {str(e)}")
        import traceback
        traceback.print_exc()

async def test_pure_firecrawl():
    """Test pure Firecrawl mode for comparison"""
    
    print("\n🔄 Testing Pure Firecrawl Mode (for comparison)")
    print("=" * 60)
    
    try:
        # Initialize scraper with Firecrawl-only strategy
        async with HomeProScraper(use_native=False) as scraper:
            print("✅ HomePro scraper initialized with Firecrawl-only strategy")
            
            # Test single product scraping
            test_url = "https://www.homepro.co.th/p/49014803"
            print(f"🔗 Testing URL: {test_url}")
            
            result = await scraper.scrape_single_product(test_url)
            
            if result:
                print("✅ Firecrawl-only scraping successful!")
                print(f"   Product: {result.get('title', 'N/A')}")
                print(f"   Strategy: {result.get('scrape_strategy', 'N/A')}")
            else:
                print("❌ Firecrawl-only scraping failed")
                
    except Exception as e:
        print(f"❌ Firecrawl test failed: {str(e)}")

if __name__ == "__main__":
    asyncio.run(test_hybrid_scraping())
    asyncio.run(test_pure_firecrawl())