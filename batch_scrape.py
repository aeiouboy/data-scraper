#!/usr/bin/env python3
"""Batch scrape products from URL file"""
import asyncio
import sys
from app.core.scraper import HomeProScraper

async def batch_scrape(urls_file: str, limit: int = None):
    """Batch scrape products from a file of URLs"""
    
    # Read URLs from file
    with open(urls_file, 'r') as f:
        urls = [line.strip() for line in f if line.strip()]
    
    if limit:
        urls = urls[:limit]
    
    print(f"📦 Batch scraping {len(urls)} products...")
    
    scraper = HomeProScraper()
    results = await scraper.scrape_batch(urls)
    
    print(f"\n✅ Successfully scraped: {results['success']}")
    print(f"❌ Failed: {results['failed']}")
    
    success_rate = (results['success'] / results['total'] * 100) if results['total'] > 0 else 0
    print(f"📈 Success rate: {success_rate:.1f}%")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python batch_scrape.py <urls_file> [limit]")
        sys.exit(1)
    
    urls_file = sys.argv[1]
    limit = int(sys.argv[2]) if len(sys.argv) > 2 else None
    
    asyncio.run(batch_scrape(urls_file, limit))