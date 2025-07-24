"""
Improved Thai Watsadu scraper with better error handling for category scraping
"""
import asyncio
import logging
from typing import List, Optional, Dict, Any
from decimal import Decimal
from datetime import datetime
import re
from urllib.parse import urljoin, urlparse

from src.models.product import Product
from src.services.firecrawl_client import FirecrawlClient
from src.config.retailers import retailer_manager, RetailerType
from src.utils.text_cleaner import clean_text, extract_number_from_string
from src.utils.url_validator import is_valid_product_url

logger = logging.getLogger(__name__)


class ImprovedThaiWatsaduScraper:
    """Improved scraper for Thai Watsadu products with better error handling"""
    
    def __init__(self):
        self.firecrawl = FirecrawlClient()
        self.retailer_config = retailer_manager.get_retailer(RetailerType.TWD)
        self.base_url = self.retailer_config.base_url
        
    async def scrape_category(self, category_url: str, max_pages: int = 5, max_concurrent: int = 5) -> Dict[str, Any]:
        """
        Scrape all products from a category with improved error handling
        
        Key improvements:
        1. Continue processing even if individual products fail
        2. Detailed error tracking
        3. Batch saving to reduce database calls
        4. Better progress reporting
        """
        logger.info(f"Scraping Thai Watsadu category: {category_url}")
        
        print(f"\n🏪 Thai Watsadu Category Scraping (Improved)")
        print(f"📂 Category URL: {category_url}")
        print(f"📄 Max pages to scan: {max_pages}")
        print(f"\n{'='*60}\n")
        
        # Initialize result dictionary with more detailed tracking
        result = {
            'category_url': category_url,
            'discovered': 0,
            'success': 0,
            'failed': 0,
            'errors': [],
            'successful_products': [],
            'failed_urls': []
        }
        
        try:
            # Phase 1: Discover product URLs
            print("🔍 Phase 1: Discovering product URLs...")
            product_urls = await self._discover_product_urls_improved(category_url, max_pages)
            result['discovered'] = len(product_urls)
            
            print(f"✅ Discovery complete! Found {len(product_urls)} products")
            logger.info(f"Found {len(product_urls)} product URLs")
            
            if not product_urls:
                print("⚠️  No product URLs discovered")
                logger.warning("No product URLs discovered")
                return result
            
            # Phase 2: Scrape products with better error handling
            print(f"\n📦 Phase 2: Scraping {len(product_urls)} products...")
            print(f"{'─'*60}\n")
            
            from src.services.supabase_service import SupabaseService
            supabase = SupabaseService()
            
            # Process in batches to avoid overwhelming the system
            batch_size = 10
            products_to_save = []
            
            for i, url in enumerate(product_urls, 1):
                print(f"\n[{i}/{len(product_urls)}] Processing: {url}")
                
                # Extra delay every batch_size products
                if i > 1 and (i-1) % batch_size == 0:
                    print(f"\n⏸️  Batch pause after {batch_size} products")
                    
                    # Save accumulated products
                    if products_to_save:
                        saved_count = await self._save_products_batch(supabase, products_to_save)
                        result['success'] += saved_count
                        result['failed'] += len(products_to_save) - saved_count
                        products_to_save = []
                    
                    await asyncio.sleep(self.retailer_config.rate_limit_delay * 2)
                
                try:
                    print(f"   🔍 Fetching product data...")
                    product = await self._scrape_product_with_retry(url)
                    
                    if product:
                        print(f"   ✅ Product extracted: {product.name[:50]}...")
                        print(f"      SKU: {product.sku}")
                        if product.current_price:
                            print(f"      Price: ฿{product.current_price:,.2f}")
                        
                        products_to_save.append(product)
                        result['successful_products'].append({
                            'sku': product.sku,
                            'name': product.name,
                            'url': url
                        })
                    else:
                        print(f"   ⚠️  No product data extracted")
                        result['failed_urls'].append(url)
                        result['errors'].append({
                            'url': url,
                            'error': 'No product data extracted'
                        })
                        
                except Exception as e:
                    error_msg = f"Error scraping product: {str(e)}"
                    logger.error(f"{error_msg} - URL: {url}")
                    print(f"   ❌ {error_msg}")
                    
                    result['failed_urls'].append(url)
                    result['errors'].append({
                        'url': url,
                        'error': str(e)
                    })
                
                # Progress update
                total_processed = result['success'] + result['failed'] + len(products_to_save)
                success_rate = (result['success'] / total_processed * 100) if total_processed > 0 else 0
                print(f"\n   Progress: {result['success']} saved, {len(products_to_save)} pending, {result['failed']} failed ({success_rate:.1f}% success rate)")
                
                # Rate limiting
                if i < len(product_urls):
                    await asyncio.sleep(self.retailer_config.rate_limit_delay)
            
            # Save any remaining products
            if products_to_save:
                saved_count = await self._save_products_batch(supabase, products_to_save)
                result['success'] += saved_count
                result['failed'] += len(products_to_save) - saved_count
            
            # Final summary
            print(f"\n{'='*60}")
            print(f"✅ Category scraping completed!")
            print(f"   Total discovered: {result['discovered']}")
            print(f"   Successfully scraped: {result['success']}")
            print(f"   Failed: {result['failed']}")
            print(f"   Success rate: {(result['success']/result['discovered']*100):.1f}%" if result['discovered'] > 0 else "N/A")
            
            if result['errors']:
                print(f"\n⚠️  Errors encountered:")
                error_types = {}
                for error in result['errors']:
                    error_type = error['error'].split(':')[0]
                    error_types[error_type] = error_types.get(error_type, 0) + 1
                
                for error_type, count in error_types.items():
                    print(f"   - {error_type}: {count} occurrences")
            
            print(f"{'='*60}\n")
            
            logger.info(f"Successfully scraped {result['success']} products from {category_url}")
            
        except Exception as e:
            logger.error(f"Fatal error during category scraping: {str(e)}")
            result['error'] = str(e)
            print(f"\n❌ Fatal error during category scraping: {str(e)}")
        
        return result
    
    async def _scrape_product_with_retry(self, url: str, max_retries: int = 2) -> Optional[Product]:
        """Scrape a product with retry logic"""
        for attempt in range(max_retries):
            try:
                if attempt > 0:
                    print(f"   🔄 Retry attempt {attempt + 1}/{max_retries}")
                    await asyncio.sleep(2)  # Wait before retry
                
                # Import the original scraper to use its scrape_product method
                from src.scrapers.thaiwatsadu_scraper import ThaiWatsaduScraper
                original_scraper = ThaiWatsaduScraper()
                product = await original_scraper.scrape_product(url)
                
                if product:
                    return product
                    
            except Exception as e:
                if attempt == max_retries - 1:
                    raise  # Re-raise on final attempt
                logger.warning(f"Retry {attempt + 1} failed for {url}: {str(e)}")
        
        return None
    
    async def _save_products_batch(self, supabase: Any, products: List[Product]) -> int:
        """Save a batch of products and return count of successful saves"""
        saved_count = 0
        
        print(f"\n💾 Saving batch of {len(products)} products...")
        
        for product in products:
            try:
                saved = await supabase.upsert_product(product)
                if saved:
                    saved_count += 1
            except Exception as e:
                logger.error(f"Failed to save product {product.sku}: {str(e)}")
        
        print(f"   ✅ Saved {saved_count}/{len(products)} products")
        
        return saved_count
    
    async def _discover_product_urls_improved(self, category_url: str, max_pages: int) -> List[str]:
        """Discover product URLs with better error handling"""
        product_urls = set()
        
        print(f"\n🔍 Discovering products from category pages...")
        print(f"   Max pages to scan: {max_pages}")
        
        consecutive_empty_pages = 0
        max_consecutive_empty = 2  # Stop after 2 consecutive empty pages
        
        for page in range(1, max_pages + 1):
            try:
                # Build page URL
                page_url = f"{category_url}?page={page}" if page > 1 else category_url
                
                print(f"\n   📄 Page {page}/{max_pages}: {page_url}")
                print(f"   🌐 Fetching page content...")
                
                result = await self.firecrawl.scrape(page_url)
                
                if not result:
                    print(f"   ❌ Failed to scrape page {page}")
                    consecutive_empty_pages += 1
                    
                    if consecutive_empty_pages >= max_consecutive_empty:
                        print(f"   ⚠️  {consecutive_empty_pages} consecutive empty pages, stopping discovery")
                        break
                    continue
                
                # Extract product links
                links = result.get('linksOnPage', result.get('links', []))
                page_products = 0
                
                for link in links:
                    if isinstance(link, dict):
                        url = link.get('url', link.get('href', ''))
                    else:
                        url = str(link)
                    
                    # Thai Watsadu product URL patterns
                    if '/th/product/' in url or '/product/' in url or '/en/product/' in url:
                        if not url.startswith('http'):
                            url = urljoin(self.base_url, url)
                        
                        # Validate URL format
                        if self._is_valid_product_url(url):
                            product_urls.add(url)
                            page_products += 1
                
                print(f"   ✅ Found {page_products} products on this page")
                print(f"   📊 Total products discovered so far: {len(product_urls)}")
                
                if page_products > 0:
                    consecutive_empty_pages = 0  # Reset counter
                else:
                    consecutive_empty_pages += 1
                    print(f"   ⚠️  Empty page ({consecutive_empty_pages} consecutive)")
                
                # Stop if we've hit too many empty pages
                if consecutive_empty_pages >= max_consecutive_empty:
                    print(f"   ⚠️  {consecutive_empty_pages} consecutive empty pages, stopping discovery")
                    break
                
                # Rate limiting between pages
                if page < max_pages:
                    await asyncio.sleep(self.retailer_config.rate_limit_delay)
                
            except Exception as e:
                print(f"   ❌ Error on page {page}: {str(e)}")
                logger.error(f"Error discovering products on page {page}: {str(e)}")
                consecutive_empty_pages += 1
                
                if consecutive_empty_pages >= max_consecutive_empty:
                    break
        
        print(f"\n✅ Discovery complete! Total unique products found: {len(product_urls)}")
        return list(product_urls)
    
    def _is_valid_product_url(self, url: str) -> bool:
        """Validate if URL is a valid product URL"""
        # Check basic URL structure
        if not url or not url.startswith('http'):
            return False
        
        # Must contain product indicator
        if not any(pattern in url for pattern in ['/product/', '/th/product/', '/en/product/']):
            return False
        
        # Should not be a category or listing page
        invalid_patterns = ['/category/', '/search', '/filter', '#', 'javascript:']
        if any(pattern in url.lower() for pattern in invalid_patterns):
            return False
        
        return True


# Quick test function
async def test_improved_scraper():
    """Test the improved scraper"""
    category_url = "https://www.thaiwatsadu.com/en/category/เครื่องปรับอากาศติดผนัง-630201"
    
    scraper = ImprovedThaiWatsaduScraper()
    result = await scraper.scrape_category(category_url, max_pages=1)
    
    print("\nTest Results:")
    print(f"Discovered: {result['discovered']}")
    print(f"Success: {result['success']}")
    print(f"Failed: {result['failed']}")
    
    if result.get('errors'):
        print(f"\nErrors: {len(result['errors'])}")
        for i, error in enumerate(result['errors'][:5], 1):
            print(f"  {i}. {error['url']}: {error['error']}")


if __name__ == "__main__":
    asyncio.run(test_improved_scraper())