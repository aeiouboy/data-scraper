#!/usr/bin/env python3
"""Test GlobalHouse URL structure"""
import asyncio
from src.services.firecrawl_client import FirecrawlClient

async def check_globalhouse_structure():
    async with FirecrawlClient() as client:
        # Try a search URL instead
        result = await client.scrape('https://globalhouse.co.th/search?q=air%20conditioner')
        
        if result:
            links = result.get('linksOnPage', result.get('links', []))
            print(f'Total links found: {len(links)}')
            
            # Also check the content
            markdown = result.get('markdown', '')
            
            # Look for product-like patterns in content
            import re
            
            # Common product URL patterns
            url_patterns = [
                r'https?://[^\s]+/product/[^\s]+',
                r'https?://[^\s]+/p/[^\s]+',
                r'https?://[^\s]+/item/[^\s]+',
                r'href=["\']([^"\']+product[^"\']+)["\']',
                r'href=["\']([^"\']+/p/[^"\']+)["\']',
            ]
            
            print('\nSearching for product URLs in content...')
            found_urls = set()
            for pattern in url_patterns:
                matches = re.findall(pattern, markdown, re.IGNORECASE)
                for match in matches:
                    found_urls.add(match)
            
            if found_urls:
                print(f'Found {len(found_urls)} product URLs in content:')
                for url in list(found_urls)[:5]:
                    print(f'  - {url}')
            else:
                print('No product URLs found in content')
                
            # Show a snippet of the content
            print('\n\nContent snippet (first 500 chars):')
            print(markdown[:500])

if __name__ == "__main__":
    asyncio.run(check_globalhouse_structure())