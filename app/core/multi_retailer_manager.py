"""
Multi-retailer scraping manager
"""
import asyncio
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime

from app.config.retailers import retailer_manager, RetailerType
from app.scrapers import get_scraper
from app.services.supabase_service import SupabaseService
from app.models.product import Product

logger = logging.getLogger(__name__)


class MultiRetailerManager:
    """Manages scraping across multiple retailers"""
    
    def __init__(self):
        self.supabase = SupabaseService()
        self.retailer_manager = retailer_manager
        
    async def scrape_all_retailers(
        self,
        retailers: Optional[List[str]] = None,
        max_products_per_retailer: int = 100
    ) -> Dict[str, Any]:
        """
        Scrape products from multiple retailers
        
        Args:
            retailers: List of retailer codes to scrape (None = all active)
            max_products_per_retailer: Maximum products to scrape per retailer
            
        Returns:
            Summary of scraping results
        """
        # Get retailers to scrape
        if retailers:
            retailer_configs = [
                self.retailer_manager.get_retailer(RetailerType(code.lower()))
                for code in retailers
            ]
        else:
            retailer_configs = self.retailer_manager.get_all_retailers()
        
        results = {
            'start_time': datetime.now(),
            'retailers': {},
            'total_products': 0,
            'total_saved': 0,
            'total_errors': 0
        }
        
        # Scrape each retailer
        for config in retailer_configs:
            logger.info(f"Starting scrape for {config.name} ({config.code})")
            
            retailer_result = await self._scrape_retailer(
                config.code,
                config.category_urls[:3],  # Limit categories for testing
                max_products_per_retailer
            )
            
            results['retailers'][config.code] = retailer_result
            results['total_products'] += retailer_result['products_found']
            results['total_saved'] += retailer_result['products_saved']
            results['total_errors'] += retailer_result['errors']
            
            # Delay between retailers
            await asyncio.sleep(5)
        
        results['end_time'] = datetime.now()
        results['duration'] = (results['end_time'] - results['start_time']).total_seconds()
        
        return results
    
    async def _scrape_retailer(
        self,
        retailer_code: str,
        category_urls: List[str],
        max_products: int
    ) -> Dict[str, Any]:
        """Scrape products from a single retailer"""
        result = {
            'retailer_code': retailer_code,
            'start_time': datetime.now(),
            'categories_scraped': 0,
            'products_found': 0,
            'products_saved': 0,
            'errors': 0,
            'error_messages': []
        }
        
        try:
            # Get scraper for this retailer
            scraper = get_scraper(retailer_code)
            
            products_scraped = 0
            
            # Scrape each category
            for category_url in category_urls:
                if products_scraped >= max_products:
                    break
                
                try:
                    logger.info(f"Scraping category: {category_url}")
                    
                    # Calculate remaining products to scrape
                    remaining = max_products - products_scraped
                    max_pages = min(5, (remaining // 20) + 1)  # Assume ~20 products per page
                    
                    # Scrape category
                    products = await scraper.scrape_category(category_url, max_pages=max_pages)
                    
                    result['categories_scraped'] += 1
                    result['products_found'] += len(products)
                    
                    # Save products
                    for product in products[:remaining]:
                        saved = await self.supabase.upsert_product(product)
                        if saved:
                            result['products_saved'] += 1
                            products_scraped += 1
                        else:
                            result['errors'] += 1
                    
                    # Rate limiting between categories
                    await asyncio.sleep(3)
                    
                except Exception as e:
                    logger.error(f"Error scraping category {category_url}: {str(e)}")
                    result['errors'] += 1
                    result['error_messages'].append(f"Category error: {str(e)}")
        
        except Exception as e:
            logger.error(f"Error with retailer {retailer_code}: {str(e)}")
            result['errors'] += 1
            result['error_messages'].append(f"Retailer error: {str(e)}")
        
        result['end_time'] = datetime.now()
        result['duration'] = (result['end_time'] - result['start_time']).total_seconds()
        
        return result
    
    async def update_retailer_stats(self):
        """Update retailer statistics in database"""
        for config in self.retailer_manager.get_all_retailers():
            try:
                # Get product count for this retailer
                products = await self.supabase.search_products(
                    filters={'retailer_code': config.code},
                    limit=1
                )
                
                total_products = products.get('total', 0)
                
                logger.info(f"{config.name}: {total_products} products in database")
                
            except Exception as e:
                logger.error(f"Error updating stats for {config.code}: {str(e)}")
    
    async def find_duplicate_products(self, retailer_code: str) -> List[Dict[str, Any]]:
        """Find potential duplicate products within a retailer"""
        duplicates = []
        
        try:
            # Get all products for retailer
            all_products = []
            page = 1
            
            while True:
                result = await self.supabase.search_products(
                    filters={'retailer_code': retailer_code},
                    page=page,
                    limit=100
                )
                
                products = result.get('products', [])
                if not products:
                    break
                
                all_products.extend(products)
                page += 1
                
                if len(all_products) >= result.get('total', 0):
                    break
            
            # Find duplicates by normalized name
            seen_names = {}
            
            for product in all_products:
                # Normalize name for comparison
                normalized = product['name'].lower().strip()
                normalized = ''.join(c for c in normalized if c.isalnum() or c.isspace())
                
                if normalized in seen_names:
                    duplicates.append({
                        'product1': seen_names[normalized],
                        'product2': product,
                        'similarity': 'exact_name'
                    })
                else:
                    seen_names[normalized] = product
            
            logger.info(f"Found {len(duplicates)} potential duplicates for {retailer_code}")
            
        except Exception as e:
            logger.error(f"Error finding duplicates: {str(e)}")
        
        return duplicates
    
    async def scrape_single_product(
        self,
        retailer_code: str,
        product_url: str
    ) -> List[Product]:
        """
        Scrape a single product by URL
        
        Args:
            retailer_code: The retailer code (e.g., 'HP', 'TWD')
            product_url: The product URL to scrape
            
        Returns:
            List of scraped products (usually just one)
        """
        try:
            # Get scraper for this retailer
            scraper = get_scraper(retailer_code)
            
            logger.info(f"Scraping single product from {retailer_code}: {product_url}")
            
            # Scrape the product
            product = await scraper.scrape_product(product_url)
            
            if product:
                # Save to database
                saved = await self.supabase.upsert_product(product)
                if saved:
                    logger.info(f"Successfully scraped and saved product: {product.sku}")
                    return [product]
                else:
                    logger.error(f"Failed to save product: {product.sku}")
                    return []
            else:
                logger.warning(f"No product data returned from scraper for URL: {product_url}")
                return []
                
        except Exception as e:
            logger.error(f"Error scraping single product from {retailer_code}: {str(e)}")
            raise


async def test_multi_retailer():
    """Test multi-retailer scraping"""
    manager = MultiRetailerManager()
    
    # Test with HomePro and Thai Watsadu
    results = await manager.scrape_all_retailers(
        retailers=['HP', 'TWD'],
        max_products_per_retailer=10  # Small test
    )
    
    print("\nMulti-Retailer Scraping Results")
    print("=" * 60)
    print(f"Total duration: {results['duration']:.2f} seconds")
    print(f"Total products found: {results['total_products']}")
    print(f"Total products saved: {results['total_saved']}")
    print(f"Total errors: {results['total_errors']}")
    
    print("\nPer-retailer results:")
    for code, result in results['retailers'].items():
        print(f"\n{code}:")
        print(f"  Categories scraped: {result['categories_scraped']}")
        print(f"  Products found: {result['products_found']}")
        print(f"  Products saved: {result['products_saved']}")
        print(f"  Errors: {result['errors']}")
        if result['error_messages']:
            print(f"  Error messages: {result['error_messages'][:3]}")


if __name__ == "__main__":
    asyncio.run(test_multi_retailer())