#!/usr/bin/env python3
"""
CLI tool for HomePro scraper
"""
import asyncio
import argparse
import logging
import sys
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).parent))

from app.core.scraper import HomeProScraper
from app.services.supabase_service import SupabaseService


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def scrape_product(url: str):
    """Scrape a single product"""
    print(f"\n🔍 Scraping product: {url}")
    
    scraper = HomeProScraper()
    result = await scraper.scrape_single_product(url)
    
    if result:
        print(f"✅ Successfully scraped: {result['name']}")
        print(f"   SKU: {result['sku']}")
        print(f"   Price: ฿{result.get('current_price', 'N/A')}")
        print(f"   Brand: {result.get('brand', 'N/A')}")
    else:
        print("❌ Failed to scrape product")


async def scrape_category(url: str, max_pages: int = 10):
    """Scrape products from a category"""
    print(f"\n📂 Scraping category: {url}")
    print(f"   Max pages: {max_pages}")
    
    scraper = HomeProScraper()
    results = await scraper.scrape_category(url, max_pages=max_pages)
    
    print(f"\n📊 Results:")
    print(f"   Products discovered: {results['discovered']}")
    print(f"   Successfully scraped: {results['success']}")
    print(f"   Failed: {results['failed']}")
    print(f"   Success rate: {results['success_rate']:.1f}%")
    print(f"   Job ID: {results.get('job_id', 'N/A')}")


async def discover_urls(url: str, max_pages: int = 50):
    """Discover product URLs from a page"""
    print(f"\n🔎 Discovering URLs from: {url}")
    
    scraper = HomeProScraper()
    urls = await scraper.discover_product_urls(url, max_pages)
    
    print(f"\n📋 Found {len(urls)} product URLs:")
    for i, product_url in enumerate(urls[:10], 1):
        print(f"   {i}. {product_url}")
    
    if len(urls) > 10:
        print(f"   ... and {len(urls) - 10} more")
    
    # Save to file
    if urls:
        filename = "discovered_urls.txt"
        with open(filename, 'w') as f:
            f.write('\n'.join(urls))
        print(f"\n💾 Saved all URLs to: {filename}")


async def show_stats():
    """Show scraping statistics"""
    print("\n📊 Scraping Statistics")
    
    scraper = HomeProScraper()
    stats = await scraper.get_scraping_stats()
    
    if stats['products']:
        print("\n🏷️  Product Stats:")
        for key, value in stats['products'].items():
            if value is not None:
                if 'price' in key and isinstance(value, (int, float)):
                    print(f"   {key}: ฿{value:,.2f}")
                elif isinstance(value, float):
                    print(f"   {key}: {value:.2f}")
                else:
                    print(f"   {key}: {value}")
    
    if stats['recent_activity']:
        print("\n📈 Recent Activity:")
        for day in stats['recent_activity']:
            print(f"   {day['date']}: {day['jobs_run']} jobs, "
                  f"{day['total_success']} success, "
                  f"{day['avg_success_rate']:.1f}% success rate")


async def search_products(query: str, limit: int = 10):
    """Search for products"""
    print(f"\n🔍 Searching for: {query}")
    
    service = SupabaseService()
    products = await service.search_products(query=query, limit=limit)
    
    if products:
        print(f"\n📦 Found {len(products)} products:")
        for i, product in enumerate(products, 1):
            print(f"\n{i}. {product['name']}")
            print(f"   SKU: {product['sku']}")
            print(f"   Price: ฿{product.get('current_price', 'N/A')}")
            print(f"   Brand: {product.get('brand', 'N/A')}")
            print(f"   URL: {product['url']}")
    else:
        print("❌ No products found")


def main():
    """Main CLI function"""
    parser = argparse.ArgumentParser(
        description='HomePro Scraper CLI',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Scrape a single product
  python scrape.py product https://www.homepro.co.th/p/12345
  
  # Scrape a category
  python scrape.py category https://www.homepro.co.th/c/electrical --max-pages 5
  
  # Discover URLs
  python scrape.py discover https://www.homepro.co.th/c/tools
  
  # Show statistics
  python scrape.py stats
  
  # Search products
  python scrape.py search "drill" --limit 20
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Commands')
    
    # Product command
    product_parser = subparsers.add_parser('product', help='Scrape a single product')
    product_parser.add_argument('url', help='Product URL')
    
    # Category command
    category_parser = subparsers.add_parser('category', help='Scrape a category')
    category_parser.add_argument('url', help='Category URL')
    category_parser.add_argument('--max-pages', type=int, default=10, help='Max pages to crawl')
    
    # Discover command
    discover_parser = subparsers.add_parser('discover', help='Discover product URLs')
    discover_parser.add_argument('url', help='Page URL to discover from')
    discover_parser.add_argument('--max-pages', type=int, default=50, help='Max pages to crawl')
    
    # Stats command
    stats_parser = subparsers.add_parser('stats', help='Show scraping statistics')
    
    # Search command
    search_parser = subparsers.add_parser('search', help='Search products')
    search_parser.add_argument('query', help='Search query')
    search_parser.add_argument('--limit', type=int, default=10, help='Number of results')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    # Run async command
    try:
        if args.command == 'product':
            asyncio.run(scrape_product(args.url))
        elif args.command == 'category':
            asyncio.run(scrape_category(args.url, args.max_pages))
        elif args.command == 'discover':
            asyncio.run(discover_urls(args.url, args.max_pages))
        elif args.command == 'stats':
            asyncio.run(show_stats())
        elif args.command == 'search':
            asyncio.run(search_products(args.query, args.limit))
    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupted by user")
    except Exception as e:
        logger.error(f"Command failed: {str(e)}")
        print(f"\n❌ Error: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()