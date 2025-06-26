"""
Supabase database service for CRUD operations
"""
from typing import List, Optional, Dict, Any
from datetime import datetime
from decimal import Decimal
import logging
from supabase import create_client, Client
from config import get_settings
from app.models.product import Product, PriceHistory, ScrapeJob

logger = logging.getLogger(__name__)


class SupabaseService:
    """Service for Supabase database operations"""
    
    def __init__(self):
        settings = get_settings()
        self.client: Client = create_client(
            settings.supabase_url,
            settings.supabase_service_role_key  # Use service role for write operations
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
                on_conflict='sku'
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
        target_url: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """Create new scrape job"""
        try:
            job = ScrapeJob(
                job_type=job_type,
                target_url=target_url,
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
        brand: Optional[str] = None,
        category: Optional[str] = None,
        min_price: Optional[float] = None,
        max_price: Optional[float] = None,
        on_sale_only: bool = False,
        limit: int = 20,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """Search products with filters"""
        try:
            query_builder = self.client.table('products').select('*')
            
            # Apply filters
            if query:
                query_builder = query_builder.or_(
                    f"name.ilike.%{query}%,description.ilike.%{query}%,sku.ilike.%{query}%"
                )
            
            if brand:
                query_builder = query_builder.eq('brand', brand)
            
            if category:
                query_builder = query_builder.eq('category', category)
            
            if min_price is not None:
                query_builder = query_builder.gte('current_price', min_price)
            
            if max_price is not None:
                query_builder = query_builder.lte('current_price', max_price)
            
            if on_sale_only:
                query_builder = query_builder.gt('discount_percentage', 0)
            
            # Apply pagination and execute
            result = query_builder\
                .order('updated_at', desc=True)\
                .range(offset, offset + limit - 1)\
                .execute()
            
            return result.data
            
        except Exception as e:
            logger.error(f"Error searching products: {str(e)}")
            return []
    
    async def get_brands(self) -> List[str]:
        """Get all unique brands"""
        try:
            result = self.client.table('products')\
                .select('brand')\
                .not_('brand', 'is', None)\
                .execute()
            
            brands = list(set(item['brand'] for item in result.data if item['brand']))
            return sorted(brands)
            
        except Exception as e:
            logger.error(f"Error fetching brands: {str(e)}")
            return []
    
    async def get_categories(self) -> List[str]:
        """Get all unique categories"""
        try:
            result = self.client.table('products')\
                .select('category')\
                .not_('category', 'is', None)\
                .execute()
            
            categories = list(set(item['category'] for item in result.data if item['category']))
            return sorted(categories)
            
        except Exception as e:
            logger.error(f"Error fetching categories: {str(e)}")
            return []