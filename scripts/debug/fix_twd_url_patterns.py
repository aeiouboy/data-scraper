#!/usr/bin/env python3
"""
Fix Thai Watsadu URL pattern matching to include English URLs
"""
import asyncio
from src.scrapers.thaiwatsadu_scraper import ThaiWatsaduScraper
from src.services.supabase_service import SupabaseService

class FixedThaiWatsaduScraper(ThaiWatsaduScraper):
    """Fixed version that handles both Thai and English URLs"""
    
    async def _discover_product_urls(self, category_url: str, max_pages: int) -> List[str]:
        """Discover product URLs from category pages - Fixed version"""
        product_urls = set()
        
        print(f"\n🔍 Discovering products from category pages...")
        print(f"   Max pages to scan: {max_pages}")
        
        for page in range(1, max_pages + 1):
            try:
                # Build page URL (Thai Watsadu uses query params)
                page_url = f"{category_url}?page={page}" if page > 1 else category_url
                
                print(f"\n   📄 Page {page}/{max_pages}: {page_url}")
                print(f"   🌐 Fetching page content...")
                
                result = await self.firecrawl.scrape(page_url)
                
                if not result:
                    print(f"   ❌ Failed to scrape page {page}")
                    break
                
                # Extract product links
                links = result.get('linksOnPage', result.get('links', []))
                page_products = 0
                
                print(f"   📊 Found {len(links)} total links on page")
                
                for link in links:
                    if isinstance(link, dict):
                        url = link.get('url', link.get('href', ''))
                    else:
                        url = str(link)
                    
                    # Fixed: Check for both Thai and English product URLs
                    if any(pattern in url for pattern in ['/th/product/', '/product/', '/en/product/']):
                        if not url.startswith('http'):
                            url = urljoin(self.base_url, url)
                        product_urls.add(url)
                        page_products += 1
                
                print(f"   ✅ Found {page_products} products on this page")
                print(f"   📊 Total products discovered so far: {len(product_urls)}")
                
                # Stop if no products found
                if page_products == 0:
                    print(f"   ⚠️  No products found on page {page}, stopping discovery")
                    break
                
                # Rate limiting between pages
                if page < max_pages:
                    print(f"   ⏳ Rate limit delay: {self.retailer_config.rate_limit_delay}s")
                    await asyncio.sleep(self.retailer_config.rate_limit_delay)
                
            except Exception as e:
                print(f"   ❌ Error on page {page}: {str(e)}")
                break
        
        print(f"\n✅ Discovery complete! Total unique products found: {len(product_urls)}")
        return list(product_urls)


async def test_fixed_scraper():
    """Test the fixed scraper"""
    
    print("\n=== Testing Fixed Thai Watsadu Scraper ===\n")
    
    # Test with the air conditioner category
    category_url = "https://www.thaiwatsadu.com/en/category/เครื่องปรับอากาศติดผนัง-630201"
    
    scraper = FixedThaiWatsaduScraper()
    
    # Only scrape 1 page for testing
    result = await scraper.scrape_category(category_url, max_pages=1)
    
    print("\n📊 Final Results:")
    print(f"   Discovered: {result.get('discovered', 0)} URLs")
    print(f"   Successfully scraped: {result.get('success', 0)}")
    print(f"   Failed: {result.get('failed', 0)}")
    
    # Check database
    supabase = SupabaseService()
    count_response = supabase.client.table('products').select('id', count='exact').eq('retailer_code', 'TWD').execute()
    print(f"\n   Total TWD products in database: {count_response.count}")
    
    return result


# Import required for fixed scraper
from typing import List
from urllib.parse import urljoin

if __name__ == "__main__":
    asyncio.run(test_fixed_scraper())