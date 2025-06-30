"""
Main scraper orchestrator
"""
import asyncio
from typing import List, Optional, Dict, Any
from datetime import datetime
import logging
from app.services.firecrawl_client import FirecrawlClient
from app.services.supabase_service import SupabaseService
from app.core.data_processor import DataProcessor

logger = logging.getLogger(__name__)


class HomeProScraper:
    """Scraper implementation for HomePro products"""
    
    def __init__(self):
        self.supabase = SupabaseService()
        self.processor = DataProcessor()
        # Add retailer config
        from app.config.retailers import retailer_manager, RetailerType
        self.retailer_config = retailer_manager.get_retailer(RetailerType.HOMEPRO)
        self.base_url = self.retailer_config.base_url
    
    async def scrape_single_product(self, url: str) -> Optional[Dict[str, Any]]:
        """
        Scrape and save a single product
        
        Args:
            url: Product URL to scrape
            
        Returns:
            Saved product data or None
        """
        try:
            # Scrape product data
            async with FirecrawlClient() as client:
                raw_data = await client.scrape(url)
            
            if not raw_data:
                logger.warning(f"No data scraped from {url}")
                return None
            
            # Process data
            product = self.processor.process_product_data(raw_data, url)
            if not product:
                logger.warning(f"Failed to process data from {url}")
                return None
            
            # Validate product
            if not self.processor.validate_product(product):
                logger.warning(f"Invalid product data from {url}")
                return None
            
            # Save to database
            saved = await self.supabase.upsert_product(product)
            return saved
            
        except Exception as e:
            logger.error(f"Error scraping {url}: {str(e)}")
            return None
    
    async def discover_product_urls(
        self, 
        start_url: str, 
        max_pages: int = 50
    ) -> List[str]:
        """
        Discover product URLs from category or search pages
        
        Args:
            start_url: Starting URL for discovery
            max_pages: Maximum pages to crawl
            
        Returns:
            List of discovered product URLs
        """
        try:
            from app.core.url_discovery import URLDiscovery
            
            discovery = URLDiscovery()
            try:
                product_urls = await discovery.discover_from_category(start_url, max_pages)
                logger.info(f"Discovered {len(product_urls)} product URLs")
                return product_urls
            finally:
                await discovery.close()
            
        except Exception as e:
            logger.error(f"Error discovering URLs: {str(e)}")
            return []
    
    async def scrape_batch(
        self, 
        urls: List[str], 
        max_concurrent: int = 5
    ) -> Dict[str, Any]:
        """
        Scrape multiple products in batch
        
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
            async with FirecrawlClient() as client:
                # Process URLs in chunks
                for i in range(0, len(urls), max_concurrent):
                    chunk = urls[i:i + max_concurrent]
                    
                    # Scrape chunk
                    raw_results = await client.batch_scrape(chunk, max_concurrent)
                    
                    # Process each result
                    for j, raw_data in enumerate(raw_results):
                        url = chunk[j] if j < len(chunk) else None
                        
                        if raw_data and url:
                            product = self.processor.process_product_data(raw_data, url)
                            
                            if product and self.processor.validate_product(product):
                                saved = await self.supabase.upsert_product(product)
                                if saved:
                                    success_count += 1
                                else:
                                    failed_count += 1
                            else:
                                failed_count += 1
                        else:
                            failed_count += 1
                    
                    processed += len(chunk)
                    
                    # Update job progress
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
        """Get current scraping statistics"""
        stats = await self.supabase.get_product_stats()
        recent_jobs = await self.supabase.get_daily_scrape_stats(7)
        
        return {
            'products': stats,
            'recent_activity': recent_jobs
        }