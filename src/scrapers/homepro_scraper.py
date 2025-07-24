"""
Main scraper orchestrator with hybrid native/Firecrawl strategy
"""
import asyncio
from typing import List, Optional, Dict, Any
from datetime import datetime
import logging
from src.services.supabase_service import SupabaseService
from src.core.data_processor import DataProcessor
from src.scrapers.strategies.hybrid_strategy import HybridStrategy

logger = logging.getLogger(__name__)


class HomeProScraper:
    """Scraper implementation for HomePro products with hybrid strategy"""
    
    def __init__(self, use_native: bool = True):
        self.supabase = SupabaseService()
        self.processor = DataProcessor()
        
        # Add retailer config
        from src.config.retailers import retailer_manager, RetailerType
        self.retailer_config = retailer_manager.get_retailer(RetailerType.HOMEPRO)
        self.base_url = self.retailer_config.base_url
        
        # Initialize scraping strategy
        if use_native:
            # Convert retailer config to format expected by strategy
            strategy_config = {
                'name': self.retailer_config.name,
                'code': self.retailer_config.code,  
                'base_url': self.retailer_config.base_url,
                'rate_limit_delay': 2.0,
                'max_concurrent': 3,
                'timeout': 30,
                'retry_attempts': 2
            }
            self.strategy = HybridStrategy(strategy_config)
            logger.info("HomePro scraper initialized with hybrid strategy (native + Firecrawl fallback)")
        else:
            # Fallback to pure Firecrawl (backward compatibility)
            from src.scrapers.strategies.firecrawl_strategy import FirecrawlStrategy
            self.strategy = FirecrawlStrategy()
            logger.info("HomePro scraper initialized with Firecrawl-only strategy")
    
    async def scrape_single_product(self, url: str) -> Optional[Dict[str, Any]]:
        """
        Scrape and save a single product using hybrid strategy
        
        Args:
            url: Product URL to scrape
            
        Returns:
            Saved product data or None
        """
        try:
            # Use hybrid strategy to scrape
            result = await self.strategy.scrape_url(url)
            
            if not result.success:
                logger.warning(f"Failed to scrape {url}: {result.error}")
                return None
            
            if not result.data:
                logger.warning(f"No data scraped from {url}")
                return None
            
            # Process data - handle both native and Firecrawl formats
            if result.strategy_used.startswith('hybrid_native'):
                # Native strategy data format
                product = self._process_native_data(result.data, url)
            else:
                # Firecrawl strategy data format  
                product = self.processor.process_product_data(result.data, url)
            
            if not product:
                logger.warning(f"Failed to process data from {url}")
                return None
            
            # Validate product - create Product object from dict if needed
            if isinstance(product, dict):
                from src.models.product import Product
                try:
                    product_obj = Product(**product)
                    if not self.processor.validate_product(product_obj):
                        logger.warning(f"Invalid product data from {url}")
                        return None
                except Exception as e:
                    logger.warning(f"Failed to create Product object from {url}: {str(e)}")
                    return None
            else:
                if not self.processor.validate_product(product):
                    logger.warning(f"Invalid product data from {url}")
                    return None
            
            # Add strategy metadata to product dict
            if isinstance(product, dict):
                product['scrape_strategy'] = result.strategy_used
                product['response_time'] = result.response_time
                
                # Convert back to Product object for database save
                from src.models.product import Product
                product_obj = Product(**product)
                saved = await self.supabase.upsert_product(product_obj)
            else:
                # Product is already a Product object, add metadata differently
                product_dict = product.dict()
                product_dict['scrape_strategy'] = result.strategy_used
                product_dict['response_time'] = result.response_time
                
                # Create new Product object with metadata
                from src.models.product import Product
                product_obj = Product(**product_dict)
                saved = await self.supabase.upsert_product(product_obj)
            
            logger.info(f"Successfully scraped and saved product from {url} using {result.strategy_used}")
            return saved
            
        except Exception as e:
            logger.error(f"Error scraping {url}: {str(e)}")
            return None
    
    def _process_native_data(self, data: Dict[str, Any], url: str) -> Optional[Dict[str, Any]]:
        """Process data from native scraping strategy"""
        try:
            # Create a mock Firecrawl-style response for the data processor
            # This allows us to reuse the existing processor logic
            mock_firecrawl_data = {
                'content': data.get('html', ''),
                'markdown': f"# {data.get('name', data.get('title', ''))}\n\nPrice: {data.get('price', 'N/A')}\nBrand: {data.get('brand', 'N/A')}",
                'metadata': {
                    'title': data.get('name') or data.get('title', ''),
                    'description': data.get('meta_description', ''),
                    'url': url
                }
            }
            
            # Use the existing data processor
            product = self.processor.process_product_data(mock_firecrawl_data, url)
            
            if product:
                # Convert Product object to dictionary for modification
                product_dict = product.dict()
                
                # Override with native-extracted data where available
                if data.get('name'):
                    product_dict['name'] = data['name']
                if data.get('current_price') or data.get('price'):
                    product_dict['current_price'] = self.processor.extract_price(data.get('current_price') or data.get('price'))
                if data.get('original_price'):
                    product_dict['original_price'] = self.processor.extract_price(data['original_price'])
                if data.get('discount_percentage'):
                    product_dict['discount_percentage'] = data['discount_percentage']
                if data.get('brand'):
                    product_dict['brand'] = data['brand']
                if data.get('category'):
                    product_dict['category'] = data['category']
                if data.get('availability'):
                    product_dict['availability'] = data['availability']
                
                # Add native strategy metadata
                product_dict['content_length'] = data.get('content_length', 0)
                product_dict['page_type'] = data.get('page_type', 'product')
                product_dict['scraped_at'] = datetime.now().isoformat()
                
                # Generate a SKU if not present (required by validator)
                if not product_dict.get('sku'):
                    # Extract SKU from URL (e.g., /p/1290589 -> 1290589)
                    import re
                    sku_match = re.search(r'/p/([^/?]+)', url)
                    if sku_match:
                        product_dict['sku'] = sku_match.group(1)
                    else:
                        # Fallback: use URL hash
                        product_dict['sku'] = f"native_{hash(url) % 1000000}"
                
                return product_dict
            
            return None
            
        except Exception as e:
            logger.error(f"Error processing native data for {url}: {str(e)}")
            return None
    
    async def discover_product_urls(
        self, 
        start_url: str, 
        max_pages: int = 50
    ) -> List[str]:
        """
        Discover product URLs from category or search pages using hybrid strategy
        
        Args:
            start_url: Starting URL for discovery
            max_pages: Maximum pages to crawl
            
        Returns:
            List of discovered product URLs
        """
        try:
            # Use hybrid strategy for URL discovery
            product_urls = await self.strategy.discover_urls(start_url, max_pages)
            logger.info(f"Discovered {len(product_urls)} product URLs using hybrid strategy")
            return product_urls
            
        except Exception as e:
            logger.error(f"Error discovering URLs: {str(e)}")
            return []
    
    async def scrape_batch(
        self, 
        urls: List[str], 
        max_concurrent: int = 5
    ) -> Dict[str, Any]:
        """
        Scrape multiple products in batch using hybrid strategy
        
        Args:
            urls: List of product URLs
            max_concurrent: Maximum concurrent scrapes
            
        Returns:
            Results summary
        """
        # Create scrape job
        job = await self.supabase.create_scrape_job(
            job_type='product',
            target_url=f"Batch of {len(urls)} products"
        )
        
        if not job:
            logger.error("Failed to create scrape job")
            return {"success": 0, "failed": len(urls)}
        
        job_id = job['id']
        
        # Update job status
        await self.supabase.update_scrape_job(job_id, {
            'status': 'running',
            'total_items': len(urls)
        })
        
        # Process in batches
        success_count = 0
        failed_count = 0
        processed = 0
        
        try:
            # Use hybrid strategy for batch scraping
            results = await self.strategy.scrape_batch(urls, max_concurrent)
            
            # Process results and save to database
            for result in results:
                processed += 1
                
                if result.success and result.data:
                    try:
                        # Process data based on strategy used
                        if result.strategy_used.startswith('hybrid_native'):
                            product = self._process_native_data(result.data, result.url)
                        else:
                            product = self.processor.process_product_data(result.data, result.url)
                        
                        # Validate product - create Product object from dict if needed
                        product_is_valid = False
                        if product:
                            if isinstance(product, dict):
                                from src.models.product import Product
                                try:
                                    product_obj = Product(**product)
                                    product_is_valid = self.processor.validate_product(product_obj)
                                except Exception:
                                    product_is_valid = False
                            else:
                                product_is_valid = self.processor.validate_product(product)
                        
                        if product_is_valid:
                            # Add strategy metadata and convert to Product object for save
                            if isinstance(product, dict):
                                product['scrape_strategy'] = result.strategy_used
                                product['response_time'] = result.response_time
                                
                                # Convert back to Product object for database save
                                from src.models.product import Product
                                product_obj = Product(**product)
                                saved = await self.supabase.upsert_product(product_obj)
                            else:
                                # Product is already a Product object, add metadata differently
                                product_dict = product.dict()
                                product_dict['scrape_strategy'] = result.strategy_used
                                product_dict['response_time'] = result.response_time
                                
                                # Create new Product object with metadata
                                from src.models.product import Product
                                product_obj = Product(**product_dict)
                                saved = await self.supabase.upsert_product(product_obj)
                            if saved:
                                success_count += 1
                                logger.debug(f"Saved product from {result.url} using {result.strategy_used}")
                            else:
                                failed_count += 1
                                logger.warning(f"Failed to save product from {result.url}")
                        else:
                            failed_count += 1
                            logger.warning(f"Invalid product data from {result.url}")
                    
                    except Exception as e:
                        failed_count += 1
                        logger.error(f"Error processing result from {result.url}: {str(e)}")
                else:
                    failed_count += 1
                    logger.warning(f"Failed to scrape {result.url}: {result.error}")
                
                # Update progress periodically
                if processed % 10 == 0:
                    await self.supabase.update_scrape_job(job_id, {
                        'processed_items': processed,
                        'success_items': success_count,
                        'failed_items': failed_count
                    })
                    logger.info(f"Progress: {processed}/{len(urls)} - Success: {success_count}, Failed: {failed_count}")
            
            # Complete job
            await self.supabase.update_scrape_job(job_id, {
                'status': 'completed',
                'processed_items': processed,
                'success_items': success_count,
                'failed_items': failed_count
            })
            
            # Log strategy statistics
            if hasattr(self.strategy, 'get_strategy_stats'):
                stats = self.strategy.get_strategy_stats()
                logger.info(f"Batch scraping completed. Strategy stats: {stats}")
            
        except Exception as e:
            logger.error(f"Batch scrape error: {str(e)}")
            await self.supabase.update_scrape_job(job_id, {
                'status': 'failed',
                'error_message': str(e),
                'processed_items': processed,
                'success_items': success_count,
                'failed_items': failed_count
            })
        
        return {
            'job_id': job_id,
            'total': len(urls),
            'success': success_count,
            'failed': failed_count,
            'success_rate': (success_count / len(urls) * 100) if urls else 0
        }
    
    async def scrape_category(
        self,
        category_url: str,
        max_pages: int = 50,
        max_concurrent: int = 5
    ) -> Dict[str, Any]:
        """
        Scrape all products from a category
        
        Args:
            category_url: Category page URL
            max_pages: Maximum pages to discover
            max_concurrent: Maximum concurrent scrapes
            
        Returns:
            Results summary
        """
        logger.info(f"Starting category scrape: {category_url}")
        
        # Discover product URLs
        product_urls = await self.discover_product_urls(category_url, max_pages)
        
        if not product_urls:
            logger.warning("No product URLs discovered")
            return {
                'category_url': category_url,
                'discovered': 0,
                'success': 0,
                'failed': 0
            }
        
        logger.info(f"Found {len(product_urls)} products to scrape")
        
        # Scrape products
        results = await self.scrape_batch(product_urls, max_concurrent)
        results['category_url'] = category_url
        results['discovered'] = len(product_urls)
        
        return results
    
    async def get_scraping_stats(self) -> Dict[str, Any]:
        """Get current scraping statistics including strategy performance"""
        stats = await self.supabase.get_product_stats()
        recent_jobs = await self.supabase.get_daily_scrape_stats(7)
        
        # Get strategy statistics if available
        strategy_stats = {}
        if hasattr(self.strategy, 'get_strategy_stats'):
            strategy_stats = self.strategy.get_strategy_stats()
        elif hasattr(self.strategy, 'get_stats'):
            strategy_stats = self.strategy.get_stats()
        
        return {
            'products': stats,
            'recent_activity': recent_jobs,
            'strategy_stats': strategy_stats
        }
    
    async def close(self):
        """Close the scraper and cleanup resources"""
        try:
            if hasattr(self.strategy, 'close'):
                await self.strategy.close()
            logger.info("HomePro scraper closed successfully")
        except Exception as e:
            logger.error(f"Error closing HomePro scraper: {str(e)}")
    
    async def __aenter__(self):
        """Async context manager entry"""
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        await self.close()