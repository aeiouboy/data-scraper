"""
Supabase database service for CRUD operations
"""
from typing import List, Optional, Dict, Any
from datetime import datetime
from decimal import Decimal
import logging
from supabase import create_client, Client
from config import get_settings
from src.models.product import Product, PriceHistory, ScrapeJob

logger = logging.getLogger(__name__)


class SupabaseService:
    """Service for Supabase database operations"""
    
    def __init__(self):
        settings = get_settings()
        self.client: Client = create_client(
            settings.supabase_url,
            settings.supabase_service_role_key
        )
    
    # Product operations
    async def get_product_by_sku(self, sku: str) -> Optional[Dict[str, Any]]:
        """Get product by SKU"""
        try:
            result = self.client.table('products').select('*').eq('sku', sku).execute()
            return result.data[0] if result.data else None
        except Exception as e:
            logger.error(f"Error fetching product {sku}: {str(e)}")
            return None
    
    async def upsert_product(self, product: Product) -> Optional[Dict[str, Any]]:
        """Insert or update product"""
        try:
            # Check if product exists
            existing = await self.get_product_by_sku(product.sku)
            
            # Prepare data
            product_data = product.to_supabase_dict()
            
            # Upsert product
            result = self.client.table('products').upsert(
                product_data,
                on_conflict='retailer_code,sku'
            ).execute()
            
            if not result.data:
                return None
            
            saved_product = result.data[0]
            
            # Record price history if price changed
            if existing and existing.get('current_price') != product_data.get('current_price'):
                await self.record_price_history(
                    product_id=saved_product['id'],
                    price=product.current_price,
                    original_price=product.original_price,
                    discount_percentage=product.discount_percentage
                )
            
            logger.info(f"Successfully upserted product: {product.sku}")
            return saved_product
            
        except Exception as e:
            logger.error(f"Error upserting product {product.sku}: {str(e)}")
            return None
    
    async def batch_upsert_products(self, products: List[Product]) -> int:
        """Batch insert/update products"""
        success_count = 0
        
        for product in products:
            result = await self.upsert_product(product)
            if result:
                success_count += 1
        
        return success_count
    
    # Price history operations
    async def record_price_history(
        self,
        product_id: str,
        price: Optional[Decimal],
        original_price: Optional[Decimal] = None,
        discount_percentage: Optional[float] = None
    ) -> bool:
        """Record price history entry"""
        try:
            history = PriceHistory(
                product_id=product_id,
                price=price,
                original_price=original_price,
                discount_percentage=discount_percentage
            )
            
            result = self.client.table('price_history').insert(
                history.to_supabase_dict()
            ).execute()
            
            return bool(result.data)
            
        except Exception as e:
            logger.error(f"Error recording price history: {str(e)}")
            return False
    
    async def get_price_history(
        self, 
        product_id: str, 
        limit: int = 30
    ) -> List[Dict[str, Any]]:
        """Get price history for a product"""
        try:
            result = self.client.table('price_history')\
                .select('*')\
                .eq('product_id', product_id)\
                .order('recorded_at', desc=True)\
                .limit(limit)\
                .execute()
            
            return result.data
            
        except Exception as e:
            logger.error(f"Error fetching price history: {str(e)}")
            return []
    
    # Scrape job operations
    async def create_scrape_job(
        self,
        job_type: str,
        target_url: Optional[str] = None,
        retailer_code: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """Create new scrape job"""
        try:
            job = ScrapeJob(
                job_type=job_type,
                target_url=target_url,
                retailer_code=retailer_code,
                status='pending'
            )
            
            result = self.client.table('scrape_jobs').insert(
                job.model_dump(exclude={'id', 'created_at'})
            ).execute()
            
            return result.data[0] if result.data else None
            
        except Exception as e:
            logger.error(f"Error creating scrape job: {str(e)}")
            return None
    
    async def update_scrape_job(
        self,
        job_id: str,
        updates: Dict[str, Any]
    ) -> bool:
        """Update scrape job status"""
        try:
            # Add timestamp updates
            if updates.get('status') == 'running' and 'started_at' not in updates:
                updates['started_at'] = datetime.now().isoformat()
            elif updates.get('status') in ['completed', 'failed'] and 'completed_at' not in updates:
                updates['completed_at'] = datetime.now().isoformat()
            
            result = self.client.table('scrape_jobs')\
                .update(updates)\
                .eq('id', job_id)\
                .execute()
            
            return bool(result.data)
            
        except Exception as e:
            logger.error(f"Error updating scrape job: {str(e)}")
            return False
    
    async def get_scrape_job(self, job_id: str) -> Optional[Dict[str, Any]]:
        """Get scrape job by ID"""
        try:
            result = self.client.table('scrape_jobs')\
                .select('*')\
                .eq('id', job_id)\
                .single()\
                .execute()
            
            return result.data
            
        except Exception as e:
            logger.error(f"Error fetching scrape job: {str(e)}")
            return None
    
    async def get_scrape_jobs(
        self, 
        status: Optional[str] = None,
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """Get scrape jobs with optional status filter"""
        try:
            query = self.client.table('scrape_jobs').select('*')
            
            if status:
                query = query.eq('status', status)
            
            result = query\
                .order('created_at', desc=True)\
                .limit(limit)\
                .execute()
            
            return result.data
            
        except Exception as e:
            logger.error(f"Error fetching scrape jobs: {str(e)}")
            return []
    
    # Analytics operations
    async def get_product_stats(self) -> Optional[Dict[str, Any]]:
        """Get product statistics"""
        try:
            result = self.client.table('product_stats').select('*').execute()
            return result.data[0] if result.data else None
        except Exception as e:
            logger.error(f"Error fetching product stats: {str(e)}")
            return None
    
    async def get_daily_scrape_stats(self, days: int = 7) -> List[Dict[str, Any]]:
        """Get daily scraping statistics"""
        try:
            result = self.client.table('daily_scrape_stats')\
                .select('*')\
                .limit(days)\
                .execute()
            
            return result.data
            
        except Exception as e:
            logger.error(f"Error fetching scrape stats: {str(e)}")
            return []
    
    # Search operations
    async def search_products(
        self,
        query: Optional[str] = None,
        filters: Optional[Dict[str, Any]] = None,
        sort_by: str = 'name',
        sort_order: str = 'asc',
        page: int = 1,
        limit: int = 20
    ) -> Dict[str, Any]:
        """Search products with filters and pagination"""
        try:
            query_builder = self.client.table('products').select('*', count='exact')
            
            # Apply text search
            if query:
                query_builder = query_builder.or_(
                    f"name.ilike.%{query}%,description.ilike.%{query}%,sku.ilike.%{query}%"
                )
            
            # Apply filters
            if filters:
                if filters.get('retailer_code'):
                    query_builder = query_builder.eq('retailer_code', filters['retailer_code'])
                
                if filters.get('brands'):
                    query_builder = query_builder.in_('brand', filters['brands'])
                
                if filters.get('categories'):
                    query_builder = query_builder.in_('category', filters['categories'])
                
                if filters.get('min_price') is not None:
                    query_builder = query_builder.gte('current_price', filters['min_price'])
                
                if filters.get('max_price') is not None:
                    query_builder = query_builder.lte('current_price', filters['max_price'])
                
                if filters.get('on_sale'):
                    query_builder = query_builder.gt('discount_percentage', 0)
                
                if filters.get('in_stock'):
                    query_builder = query_builder.eq('availability', 'in_stock')
            
            # Apply sorting
            desc = sort_order == 'desc'
            query_builder = query_builder.order(sort_by, desc=desc)
            
            # Apply pagination
            offset = (page - 1) * limit
            query_builder = query_builder.range(offset, offset + limit - 1)
            
            # Execute query
            result = query_builder.execute()
            
            return {
                'products': result.data,
                'total': result.count or 0
            }
            
        except Exception as e:
            logger.error(f"Error searching products: {str(e)}")
            return {'products': [], 'total': 0}
    
    async def get_product_by_id(self, product_id: str) -> Optional[Dict[str, Any]]:
        """Get product by ID"""
        try:
            result = self.client.table('products')\
                .select('*')\
                .eq('id', product_id)\
                .single()\
                .execute()
            
            return result.data
            
        except Exception as e:
            logger.error(f"Error fetching product by ID: {str(e)}")
            return None
    
    async def get_all_brands(self, retailer_code: Optional[str] = None) -> List[str]:
        """Get all unique brands, optionally filtered by retailer"""
        try:
            # Build query
            if retailer_code:
                result = self.client.table('products')\
                    .select('brand')\
                    .eq('retailer_code', retailer_code)\
                    .not_.is_('brand', 'null')\
                    .execute()
            else:
                result = self.client.table('products')\
                    .select('brand')\
                    .not_.is_('brand', 'null')\
                    .execute()
            
            # Extract unique brands
            brands = list(set(item['brand'] for item in result.data if item['brand']))
            return sorted(brands)
            
        except Exception as e:
            logger.error(f"Error fetching brands: {str(e)}")
            return []
    
    async def get_categories(self, retailer_code: Optional[str] = None) -> List[str]:
        """Get all unique categories, optionally filtered by retailer"""
        try:
            # Build query
            if retailer_code:
                result = self.client.table('products')\
                    .select('category')\
                    .eq('retailer_code', retailer_code)\
                    .not_.is_('category', 'null')\
                    .execute()
            else:
                result = self.client.table('products')\
                    .select('category')\
                    .not_.is_('category', 'null')\
                    .execute()
            
            # Extract unique categories
            categories = list(set(item['category'] for item in result.data if item['category']))
            return sorted(categories)
            
        except Exception as e:
            logger.error(f"Error fetching categories: {str(e)}")
            return []
    
    # Batch query operations to fix N+1 query problem
    async def get_products_batch(self, product_ids: List[str]) -> Dict[str, Dict[str, Any]]:
        """
        Fetch multiple products in one query
        
        Args:
            product_ids: List of product IDs to fetch
            
        Returns:
            Dictionary keyed by product ID for easy lookup
        """
        if not product_ids:
            return {}
            
        try:
            result = self.client.table('products')\
                .select('*')\
                .in_('id', product_ids)\
                .execute()
            
            # Convert to dictionary keyed by product ID
            products_dict = {
                product['id']: product 
                for product in result.data
            }
            
            logger.info(f"Fetched {len(products_dict)} products in batch")
            return products_dict
            
        except Exception as e:
            logger.error(f"Error fetching products batch: {str(e)}")
            return {}
    
    async def get_products_with_prices_batch(self, product_ids: List[str]) -> Dict[str, Dict[str, Any]]:
        """
        Get products with their current prices in batch
        
        Args:
            product_ids: List of product IDs to fetch
            
        Returns:
            Dictionary keyed by product ID with product data including current price info
        """
        if not product_ids:
            return {}
            
        try:
            # Fetch products with price information
            result = self.client.table('products')\
                .select('id, sku, name, brand, category, retailer_code, '
                       'current_price, original_price, discount_percentage, '
                       'availability, url, image_url, scraped_at')\
                .in_('id', product_ids)\
                .execute()
            
            # Convert to dictionary keyed by product ID
            products_dict = {
                product['id']: product 
                for product in result.data
            }
            
            logger.info(f"Fetched {len(products_dict)} products with prices in batch")
            return products_dict
            
        except Exception as e:
            logger.error(f"Error fetching products with prices batch: {str(e)}")
            return {}
    
    async def get_match_details_batch(self, match_ids: List[str]) -> Dict[str, Dict[str, Any]]:
        """
        Get match details in batch (assuming a matches or product_matches table exists)
        
        Args:
            match_ids: List of match IDs to fetch
            
        Returns:
            Dictionary keyed by match ID for easy lookup
        """
        if not match_ids:
            return {}
            
        try:
            # First, check if product_matches table exists
            # If not, this might need to be adjusted based on your actual schema
            result = self.client.table('product_matches')\
                .select('*')\
                .in_('id', match_ids)\
                .execute()
            
            # Convert to dictionary keyed by match ID
            matches_dict = {
                match['id']: match 
                for match in result.data
            }
            
            logger.info(f"Fetched {len(matches_dict)} matches in batch")
            return matches_dict
            
        except Exception as e:
            # If product_matches table doesn't exist, log and return empty
            logger.warning(f"Error fetching matches batch (table might not exist): {str(e)}")
            return {}
    
    async def get_products_by_skus_batch(
        self, 
        skus: List[str], 
        retailer_code: Optional[str] = None
    ) -> Dict[str, Dict[str, Any]]:
        """
        Fetch multiple products by SKUs in one query
        
        Args:
            skus: List of SKUs to fetch
            retailer_code: Optional retailer code to filter by
            
        Returns:
            Dictionary keyed by SKU for easy lookup
        """
        if not skus:
            return {}
            
        try:
            query = self.client.table('products').select('*').in_('sku', skus)
            
            if retailer_code:
                query = query.eq('retailer_code', retailer_code)
            
            result = query.execute()
            
            # Convert to dictionary keyed by SKU
            products_dict = {
                product['sku']: product 
                for product in result.data
            }
            
            logger.info(f"Fetched {len(products_dict)} products by SKU in batch")
            return products_dict
            
        except Exception as e:
            logger.error(f"Error fetching products by SKUs batch: {str(e)}")
            return {}
    
    async def get_price_history_batch(
        self, 
        product_ids: List[str], 
        limit_per_product: int = 10
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        Get price history for multiple products in one query
        
        Args:
            product_ids: List of product IDs
            limit_per_product: Maximum number of price history entries per product
            
        Returns:
            Dictionary keyed by product ID containing list of price history entries
        """
        if not product_ids:
            return {}
            
        try:
            # Fetch all price history for the given products
            result = self.client.table('price_history')\
                .select('*')\
                .in_('product_id', product_ids)\
                .order('recorded_at', desc=True)\
                .execute()
            
            # Group by product_id and limit entries per product
            price_history_dict: Dict[str, List[Dict[str, Any]]] = {}
            
            for entry in result.data:
                product_id = entry['product_id']
                if product_id not in price_history_dict:
                    price_history_dict[product_id] = []
                
                # Only add if under limit
                if len(price_history_dict[product_id]) < limit_per_product:
                    price_history_dict[product_id].append(entry)
            
            logger.info(f"Fetched price history for {len(price_history_dict)} products in batch")
            return price_history_dict
            
        except Exception as e:
            logger.error(f"Error fetching price history batch: {str(e)}")
            return {}