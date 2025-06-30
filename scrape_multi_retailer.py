#!/usr/bin/env python3
"""
Multi-Retailer Scraping System for Thai Home Improvement Market
Supports: HomePro, Thai Watsadu, Global House, DoHome, Boonthavorn, MegaHome
"""

import asyncio
import argparse
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
import hashlib
import re

from app.config.retailers import (
    RetailerType, RetailerConfig, retailer_manager,
    get_unified_category_mapping
)
from app.core.data_processor import DataProcessor
from app.models.product import Product, ProductMatch
from app.services.firecrawl_client import FirecrawlClient
from app.utils.database import SupabaseClient
from app.utils.logging_config import setup_logging

# Configure logging
logger = setup_logging(__name__)


class MultiRetailerScraper:
    """Comprehensive scraper for all 6 Thai home improvement retailers"""
    
    def __init__(self):
        self.firecrawl = FirecrawlClient()
        self.db = SupabaseClient()
        self.data_processor = DataProcessor()
        self.unified_categories = get_unified_category_mapping()
        
        # Initialize retailer-specific processors
        self.retailer_processors = {}
        for retailer_type in RetailerType:
            self.retailer_processors[retailer_type] = RetailerDataProcessor(
                retailer_manager.get_retailer(retailer_type)
            )
    
    async def scrape_retailer(
        self,
        retailer_type: RetailerType,
        max_products: Optional[int] = None,
        categories: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Scrape a specific retailer"""
        
        retailer_config = retailer_manager.get_retailer(retailer_type)
        processor = self.retailer_processors[retailer_type]
        
        logger.info(f"Starting scrape for {retailer_config.name}")
        logger.info(f"Estimated products: {retailer_config.estimated_products:,}")
        
        results = {
            "retailer": retailer_config.name,
            "total_discovered": 0,
            "total_scraped": 0,
            "success_rate": 0.0,
            "categories_processed": 0,
            "errors": []
        }
        
        try:
            # Step 1: Category Discovery
            category_urls = categories or retailer_config.category_urls
            results["categories_processed"] = len(category_urls)
            
            product_urls = []
            for category_url in category_urls:
                logger.info(f"Discovering products in: {category_url}")
                
                try:
                    urls = await self._discover_category_products(
                        category_url, retailer_config, max_per_category=max_products
                    )
                    product_urls.extend(urls)
                    logger.info(f"Found {len(urls)} products in category")
                    
                    # Apply rate limiting
                    await asyncio.sleep(retailer_config.rate_limit_delay)
                    
                except Exception as e:
                    error_msg = f"Category discovery failed for {category_url}: {str(e)}"
                    logger.error(error_msg)
                    results["errors"].append(error_msg)
            
            results["total_discovered"] = len(product_urls)
            logger.info(f"Total products discovered: {len(product_urls):,}")
            
            # Step 2: Product Scraping
            if product_urls:
                scraped_count = await self._scrape_products_batch(
                    product_urls, retailer_config, processor
                )
                results["total_scraped"] = scraped_count
                results["success_rate"] = (scraped_count / len(product_urls)) * 100
            
            logger.info(f"Completed {retailer_config.name}: {results['total_scraped']:,} products scraped")
            
        except Exception as e:
            error_msg = f"Retailer scraping failed for {retailer_config.name}: {str(e)}"
            logger.error(error_msg)
            results["errors"].append(error_msg)
        
        return results
    
    async def scrape_all_retailers(
        self,
        max_products_per_retailer: Optional[int] = None,
        selected_retailers: Optional[List[RetailerType]] = None
    ) -> Dict[str, Any]:
        """Scrape all retailers comprehensively"""
        
        retailers_to_scrape = selected_retailers or list(RetailerType)
        
        logger.info("=" * 80)
        logger.info("MULTI-RETAILER SCRAPING STARTED")
        logger.info(f"Retailers: {len(retailers_to_scrape)}")
        logger.info(f"Estimated total products: {retailer_manager.get_total_estimated_products():,}")
        logger.info("=" * 80)
        
        overall_results = {
            "start_time": datetime.now(),
            "retailers": {},
            "totals": {
                "discovered": 0,
                "scraped": 0,
                "success_rate": 0.0
            },
            "monitoring_distribution": retailer_manager.calculate_monitoring_distribution()
        }
        
        # Scrape each retailer
        for retailer_type in retailers_to_scrape:
            retailer_config = retailer_manager.get_retailer(retailer_type)
            
            logger.info(f"\n📍 Starting {retailer_config.name} ({retailer_config.code})")
            logger.info(f"   Market Position: {retailer_config.market_position}")
            logger.info(f"   Estimated Products: {retailer_config.estimated_products:,}")
            logger.info(f"   Focus: {', '.join(retailer_config.focus_categories)}")
            
            retailer_results = await self.scrape_retailer(
                retailer_type, max_products_per_retailer
            )
            
            overall_results["retailers"][retailer_config.code] = retailer_results
            overall_results["totals"]["discovered"] += retailer_results["total_discovered"]
            overall_results["totals"]["scraped"] += retailer_results["total_scraped"]
        
        # Calculate overall success rate
        if overall_results["totals"]["discovered"] > 0:
            overall_results["totals"]["success_rate"] = (
                overall_results["totals"]["scraped"] / overall_results["totals"]["discovered"]
            ) * 100
        
        overall_results["end_time"] = datetime.now()
        overall_results["duration"] = str(overall_results["end_time"] - overall_results["start_time"])
        
        # Log final summary
        self._log_final_summary(overall_results)
        
        return overall_results
    
    async def _discover_category_products(
        self,
        category_url: str,
        retailer_config: RetailerConfig,
        max_per_category: Optional[int] = None
    ) -> List[str]:
        """Discover product URLs from a category page"""
        
        try:
            # Use Firecrawl to get category page content
            result = await self.firecrawl.scrape_url(
                category_url,
                formats=["markdown", "links"],
                wait_for=2000
            )
            
            if not result.success:
                logger.error(f"Failed to scrape category: {category_url}")
                return []
            
            # Extract product URLs using retailer-specific patterns
            product_urls = []
            links = result.data.get("links", [])
            
            for link in links:
                url = link.get("url", "")
                
                # Apply retailer-specific URL filtering
                if self._is_product_url(url, retailer_config):
                    product_urls.append(url)
                
                # Limit products per category if specified
                if max_per_category and len(product_urls) >= max_per_category:
                    break
            
            return list(set(product_urls))  # Remove duplicates
            
        except Exception as e:
            logger.error(f"Category discovery error for {category_url}: {str(e)}")
            return []
    
    def _is_product_url(self, url: str, retailer_config: RetailerConfig) -> bool:
        """Check if URL is a product page based on retailer-specific patterns"""
        
        if not url or retailer_config.base_url not in url:
            return False
        
        # Common product URL patterns for Thai retailers
        product_patterns = [
            r'/p/',           # Common product path
            r'/product/',     # Alternative product path
            r'/products/',    # Products collection
            r'-p-\d+',        # Product ID patterns
            r'/[^/]+\.html',  # HTML product pages
        ]
        
        # Add retailer-specific patterns
        if retailer_config.type == RetailerType.HOMEPRO:
            product_patterns.extend([
                r'/p/\d+',
                r'/products/\d+',
            ])
        elif retailer_config.type == RetailerType.GLOBAL_HOUSE:
            product_patterns.extend([
                r'/product/[^/]+',
                r'/item/\d+',
            ])
        
        for pattern in product_patterns:
            if re.search(pattern, url, re.IGNORECASE):
                return True
        
        return False
    
    async def _scrape_products_batch(
        self,
        product_urls: List[str],
        retailer_config: RetailerConfig,
        processor: 'RetailerDataProcessor'
    ) -> int:
        """Scrape products in batches with rate limiting"""
        
        scraped_count = 0
        batch_size = retailer_config.max_concurrent
        
        for i in range(0, len(product_urls), batch_size):
            batch = product_urls[i:i + batch_size]
            
            logger.info(f"Processing batch {i//batch_size + 1}: {len(batch)} products")
            
            # Process batch with concurrency control
            tasks = [
                self._scrape_single_product(url, retailer_config, processor)
                for url in batch
            ]
            
            batch_results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Count successful scrapes
            for result in batch_results:
                if isinstance(result, Product):
                    scraped_count += 1
                elif isinstance(result, Exception):
                    logger.warning(f"Product scrape failed: {str(result)}")
            
            # Rate limiting between batches
            await asyncio.sleep(retailer_config.rate_limit_delay)
        
        return scraped_count
    
    async def _scrape_single_product(
        self,
        url: str,
        retailer_config: RetailerConfig,
        processor: 'RetailerDataProcessor'
    ) -> Optional[Product]:
        """Scrape a single product"""
        
        try:
            # Use Firecrawl to scrape product page
            result = await self.firecrawl.scrape_url(
                url,
                formats=["markdown", "extract"],
                extract_schema={
                    "name": "string",
                    "price": "number",
                    "original_price": "number",
                    "brand": "string",
                    "description": "string",
                    "availability": "string",
                    "images": "array"
                }
            )
            
            if not result.success:
                logger.warning(f"Failed to scrape product: {url}")
                return None
            
            # Process data using retailer-specific processor
            product = await processor.process_product_data(url, result.data)
            
            if product:
                # Save to database
                await self.db.insert_product(product)
                return product
            
        except Exception as e:
            logger.error(f"Product scraping error for {url}: {str(e)}")
        
        return None
    
    def _log_final_summary(self, results: Dict[str, Any]) -> None:
        """Log comprehensive final summary"""
        
        logger.info("\n" + "=" * 100)
        logger.info("🏆 MULTI-RETAILER SCRAPING COMPLETED")
        logger.info("=" * 100)
        
        logger.info(f"⏱️  Duration: {results['duration']}")
        logger.info(f"📊 Total Products Discovered: {results['totals']['discovered']:,}")
        logger.info(f"✅ Total Products Scraped: {results['totals']['scraped']:,}")
        logger.info(f"📈 Overall Success Rate: {results['totals']['success_rate']:.1f}%")
        
        logger.info("\n📍 RETAILER BREAKDOWN:")
        for retailer_code, retailer_results in results["retailers"].items():
            logger.info(f"   {retailer_code}: {retailer_results['total_scraped']:,} products")
            logger.info(f"      Success Rate: {retailer_results['success_rate']:.1f}%")
            if retailer_results['errors']:
                logger.info(f"      Errors: {len(retailer_results['errors'])}")
        
        logger.info("\n🎯 MONITORING DISTRIBUTION:")
        total_ultra_critical = 0
        total_high_value = 0
        total_standard = 0
        total_low_priority = 0
        
        for retailer_code, distribution in results["monitoring_distribution"].items():
            total_ultra_critical += distribution["ultra_critical"]
            total_high_value += distribution["high_value"]
            total_standard += distribution["standard"]
            total_low_priority += distribution["low_priority"]
        
        logger.info(f"   Ultra-Critical: {total_ultra_critical:,} products (daily monitoring)")
        logger.info(f"   High-Value: {total_high_value:,} products (3x/week)")
        logger.info(f"   Standard: {total_standard:,} products (weekly)")
        logger.info(f"   Low-Priority: {total_low_priority:,} products (bi-weekly)")
        
        total_products = total_ultra_critical + total_high_value + total_standard + total_low_priority
        logger.info(f"\n📈 TOTAL ADDRESSABLE MARKET: {total_products:,} products")
        
        logger.info("=" * 100)


class RetailerDataProcessor:
    """Retailer-specific data processing"""
    
    def __init__(self, retailer_config: RetailerConfig):
        self.config = retailer_config
        self.data_processor = DataProcessor()
        self.unified_categories = get_unified_category_mapping()
    
    async def process_product_data(self, url: str, raw_data: Dict[str, Any]) -> Optional[Product]:
        """Process scraped data into Product model"""
        
        try:
            # Extract basic product information
            extract_data = raw_data.get("extract", {})
            markdown_data = raw_data.get("markdown", "")
            
            # Create base product
            product = Product(
                sku=self._generate_sku(url, extract_data),
                name=extract_data.get("name", "").strip(),
                url=url,
                retailer_code=self.config.code,
                retailer_name=self.config.name,
            )
            
            # Extract retailer-specific data
            product.current_price = self._extract_price(extract_data.get("price"))
            product.original_price = self._extract_price(extract_data.get("original_price"))
            product.brand = self._extract_brand(extract_data, markdown_data)
            product.category = self._extract_category(url, markdown_data, extract_data)
            product.unified_category = self._map_to_unified_category(product.category)
            product.availability = self._extract_availability(extract_data, markdown_data)
            product.description = extract_data.get("description", "")
            product.images = extract_data.get("images", [])
            
            # Calculate monitoring tier
            price = float(product.current_price or product.original_price or 0)
            product.monitoring_tier = self.config.get_monitoring_tier(price, product.category or "")
            
            # Generate product hash for matching
            product.product_hash = self._generate_product_hash(product)
            
            # Calculate discount percentage
            if product.current_price and product.original_price and product.original_price > product.current_price:
                product.discount_percentage = float(
                    ((product.original_price - product.current_price) / product.original_price) * 100
                )
            
            return product
            
        except Exception as e:
            logger.error(f"Product data processing error: {str(e)}")
            return None
    
    def _generate_sku(self, url: str, extract_data: Dict[str, Any]) -> str:
        """Generate SKU from URL or extracted data"""
        
        # Try to extract SKU from URL patterns
        sku_patterns = [
            r'/p/(\d+)',
            r'/product/(\d+)',
            r'-p-(\d+)',
            r'/(\d{6,})',
        ]
        
        for pattern in sku_patterns:
            match = re.search(pattern, url)
            if match:
                return f"{self.config.code}-{match.group(1)}"
        
        # Fallback: use URL hash
        url_hash = hashlib.md5(url.encode()).hexdigest()[:8]
        return f"{self.config.code}-{url_hash.upper()}"
    
    def _extract_price(self, price_value: Any) -> Optional[float]:
        """Extract and validate price"""
        if not price_value:
            return None
        
        try:
            if isinstance(price_value, (int, float)):
                return float(price_value)
            
            # Clean price string
            price_str = str(price_value).replace(",", "").replace("฿", "").replace("$", "")
            price_match = re.search(r'[\d,]+\.?\d*', price_str)
            
            if price_match:
                return float(price_match.group().replace(",", ""))
        except:
            pass
        
        return None
    
    def _extract_brand(self, extract_data: Dict[str, Any], markdown: str) -> Optional[str]:
        """Extract brand using retailer-specific logic"""
        
        brand = extract_data.get("brand", "").strip()
        if brand:
            return brand
        
        # Try to extract from markdown using common patterns
        brand_patterns = [
            r'แบรนด์[:\s]+([^\n]+)',
            r'ยี่ห้อ[:\s]+([^\n]+)',
            r'Brand[:\s]+([^\n]+)',
        ]
        
        for pattern in brand_patterns:
            match = re.search(pattern, markdown, re.IGNORECASE)
            if match:
                return match.group(1).strip()
        
        return None
    
    def _extract_category(self, url: str, markdown: str, extract_data: Dict[str, Any]) -> Optional[str]:
        """Extract category using retailer-specific mapping"""
        
        # Use retailer-specific category mapping
        for code, category in self.config.category_mapping.items():
            if f'/{code}' in url or f'/c/{code}' in url:
                return category
        
        # Try to extract from content
        category_patterns = [
            r'หมวดหมู่[:\s]+([^\n]+)',
            r'Category[:\s]+([^\n]+)',
        ]
        
        for pattern in category_patterns:
            match = re.search(pattern, markdown, re.IGNORECASE)
            if match:
                return match.group(1).strip()
        
        return None
    
    def _map_to_unified_category(self, retailer_category: Optional[str]) -> Optional[str]:
        """Map retailer category to unified category"""
        
        if not retailer_category:
            return None
        
        # Direct mapping
        for unified_key, unified_value in self.unified_categories.items():
            if retailer_category == unified_value:
                return unified_key
        
        # Fuzzy matching based on keywords
        category_lower = retailer_category.lower()
        
        if any(keyword in category_lower for keyword in ['เฟอร์นิเจอร์', 'furniture']):
            return 'furniture'
        elif any(keyword in category_lower for keyword in ['ไฟฟ้า', 'electrical', 'appliance']):
            return 'appliances'
        elif any(keyword in category_lower for keyword in ['ห้องครัว', 'kitchen']):
            return 'kitchen'
        elif any(keyword in category_lower for keyword in ['ห้องน้ำ', 'bathroom']):
            return 'bathroom'
        elif any(keyword in category_lower for keyword in ['สี', 'paint']):
            return 'paint'
        elif any(keyword in category_lower for keyword in ['โคมไฟ', 'lighting', 'หลอดไฟ']):
            return 'lighting'
        
        return None
    
    def _extract_availability(self, extract_data: Dict[str, Any], markdown: str) -> str:
        """Extract availability status"""
        
        availability = extract_data.get("availability", "").lower()
        
        # Check extracted availability first
        if "in stock" in availability or "พร้อม" in availability:
            return "in_stock"
        elif "out of stock" in availability or "หมด" in availability:
            return "out_of_stock"
        elif "limited" in availability or "จำกัด" in availability:
            return "limited_stock"
        
        # Check markdown content
        content_lower = markdown.lower()
        if any(phrase in content_lower for phrase in ["พร้อมส่ง", "มีสินค้า", "in stock"]):
            return "in_stock"
        elif any(phrase in content_lower for phrase in ["สินค้าหมด", "out of stock", "ไม่มีสินค้า"]):
            return "out_of_stock"
        
        return "unknown"
    
    def _generate_product_hash(self, product: Product) -> str:
        """Generate hash for product matching across retailers"""
        
        # Normalize product attributes for matching
        normalized_name = re.sub(r'[^\w\s]', '', product.name.lower().strip())
        normalized_brand = re.sub(r'[^\w\s]', '', (product.brand or "").lower().strip())
        
        # Create hash from key attributes
        hash_input = f"{normalized_name}_{normalized_brand}_{product.unified_category or ''}"
        return hashlib.md5(hash_input.encode()).hexdigest()


async def main():
    """Main entry point for multi-retailer scraping"""
    
    parser = argparse.ArgumentParser(description="Multi-Retailer Thai Home Improvement Scraper")
    parser.add_argument("--retailers", nargs="+", choices=[r.value for r in RetailerType],
                       help="Specific retailers to scrape (default: all)")
    parser.add_argument("--max-products", type=int, help="Maximum products per retailer")
    parser.add_argument("--test-mode", action="store_true", help="Run in test mode with limited products")
    
    args = parser.parse_args()
    
    # Parse retailer selection
    selected_retailers = None
    if args.retailers:
        selected_retailers = [RetailerType(r) for r in args.retailers]
    
    # Adjust limits for test mode
    max_products = args.max_products
    if args.test_mode:
        max_products = max_products or 50
        logger.info("🧪 Running in TEST MODE - Limited product scraping")
    
    # Initialize and run scraper
    scraper = MultiRetailerScraper()
    
    try:
        results = await scraper.scrape_all_retailers(
            max_products_per_retailer=max_products,
            selected_retailers=selected_retailers
        )
        
        logger.info("✅ Multi-retailer scraping completed successfully")
        
        # Save results summary
        with open("multi_retailer_results.json", "w") as f:
            import json
            json.dump(results, f, indent=2, default=str)
        
    except Exception as e:
        logger.error(f"❌ Multi-retailer scraping failed: {str(e)}")
        raise


if __name__ == "__main__":
    asyncio.run(main())