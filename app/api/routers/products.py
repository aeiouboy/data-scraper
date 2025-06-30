"""
Products API endpoints
"""
from fastapi import APIRouter, Query, HTTPException, Depends
from typing import Optional, List
import logging

from app.api.models import (
    ProductSearchRequest, 
    ProductSearchResponse, 
    ProductResponse
)
from app.services.supabase_service import SupabaseService

logger = logging.getLogger(__name__)
router = APIRouter()


def get_supabase() -> SupabaseService:
    """Dependency to get Supabase service"""
    return SupabaseService()


@router.post("/search", response_model=ProductSearchResponse)
async def search_products(
    request: ProductSearchRequest,
    supabase: SupabaseService = Depends(get_supabase)
):
    """
    Search and filter products
    
    Supports:
    - Full-text search
    - Filter by brand, category, price range
    - Sort by name, price, discount, date
    - Pagination
    """
    try:
        # Build filters
        filters = {}
        if request.retailer_code:
            filters['retailer_code'] = request.retailer_code
        if request.brands:
            filters['brands'] = request.brands
        if request.categories:
            filters['categories'] = request.categories
        if request.min_price is not None:
            filters['min_price'] = request.min_price
        if request.max_price is not None:
            filters['max_price'] = request.max_price
        if request.on_sale_only:
            filters['on_sale'] = True
        if request.in_stock_only:
            filters['in_stock'] = True
            
        # Search products
        results = await supabase.search_products(
            query=request.query,
            filters=filters,
            sort_by=request.sort_by,
            sort_order=request.sort_order,
            page=request.page,
            limit=request.page_size
        )
        
        # Convert to response model
        products = [
            ProductResponse(
                id=p['id'],
                sku=p['sku'],
                name=p['name'],
                brand=p.get('brand'),
                category=p.get('category'),
                current_price=float(p['current_price']) if p.get('current_price') else None,
                original_price=float(p['original_price']) if p.get('original_price') else None,
                discount_percentage=p.get('discount_percentage'),
                description=p.get('description'),
                features=p.get('features', []),
                specifications=p.get('specifications', {}),
                availability=p.get('availability', 'unknown'),
                images=p.get('images', []),
                url=p['url'],
                last_scraped=p.get('scraped_at', p['created_at']),
                created_at=p['created_at'],
                updated_at=p.get('updated_at')
            )
            for p in results['products']
        ]
        
        total_pages = (results['total'] + request.page_size - 1) // request.page_size
        
        return ProductSearchResponse(
            products=products,
            total=results['total'],
            page=request.page,
            page_size=request.page_size,
            total_pages=total_pages
        )
        
    except Exception as e:
        logger.error(f"Product search error: {str(e)}")
        raise HTTPException(status_code=500, detail="Search failed")


@router.get("/{product_id}", response_model=ProductResponse)
async def get_product(
    product_id: str,
    supabase: SupabaseService = Depends(get_supabase)
):
    """Get product by ID"""
    try:
        product = await supabase.get_product_by_id(product_id)
        if not product:
            raise HTTPException(status_code=404, detail="Product not found")
            
        return ProductResponse(
            id=product['id'],
            sku=product['sku'],
            name=product['name'],
            brand=product.get('brand'),
            category=product.get('category'),
            current_price=float(product['current_price']) if product.get('current_price') else None,
            original_price=float(product['original_price']) if product.get('original_price') else None,
            discount_percentage=product.get('discount_percentage'),
            description=product.get('description'),
            features=product.get('features', []),
            specifications=product.get('specifications', {}),
            availability=product.get('availability', 'unknown'),
            images=product.get('images', []),
            url=product['url'],
            last_scraped=product.get('scraped_at', product['created_at']),
            created_at=product['created_at'],
            updated_at=product.get('updated_at')
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get product error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get product")


@router.get("/{product_id}/price-history")
async def get_price_history(
    product_id: str,
    days: int = Query(default=30, ge=1, le=365),
    supabase: SupabaseService = Depends(get_supabase)
):
    """Get product price history"""
    try:
        history = await supabase.get_price_history(product_id, limit=days)
        return {
            "product_id": product_id,
            "history": history,
            "days": days
        }
        
    except Exception as e:
        logger.error(f"Price history error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get price history")


@router.get("/filters/brands")
async def get_brands(
    retailer_code: Optional[str] = Query(None, description="Filter by retailer code"),
    supabase: SupabaseService = Depends(get_supabase)
):
    """Get all unique brands, optionally filtered by retailer"""
    try:
        brands = await supabase.get_all_brands(retailer_code=retailer_code)
        return {"brands": brands}
        
    except Exception as e:
        logger.error(f"Get brands error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get brands")


@router.get("/filters/categories")
async def get_categories(
    retailer_code: Optional[str] = Query(None, description="Filter by retailer code"),
    supabase: SupabaseService = Depends(get_supabase)
):
    """Get all categories, optionally filtered by retailer"""
    try:
        categories = await supabase.get_categories(retailer_code=retailer_code)
        return {"categories": categories}
        
    except Exception as e:
        logger.error(f"Get categories error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get categories")


@router.post("/{product_id}/rescrape")
async def rescrape_product(
    product_id: str,
    supabase: SupabaseService = Depends(get_supabase)
):
    """Trigger rescrape of a single product"""
    try:
        # Get product details
        product = await supabase.get_product_by_id(product_id)
        if not product:
            raise HTTPException(status_code=404, detail="Product not found")
        
        # Import multi-retailer manager
        from app.core.multi_retailer_manager import MultiRetailerManager
        from app.config.retailers import retailer_manager
        
        # Get the appropriate scraper for this retailer
        retailer_code = product.get('retailer_code')
        if not retailer_code:
            raise HTTPException(status_code=400, detail="Product missing retailer code")
            
        retailer_config = retailer_manager.get_retailer(retailer_code)
        if not retailer_config:
            raise HTTPException(status_code=400, detail=f"Unknown retailer: {retailer_code}")
        
        # Create scrape job
        job = await supabase.create_scrape_job(
            job_type='product_rescrape',
            target_url=product['url']
        )
        
        # Update job with retailer info
        await supabase.update_scrape_job(job['id'], {
            'retailer_code': retailer_code,
            'status': 'running'
        })
        
        # Initialize multi-retailer manager
        manager = MultiRetailerManager()
        
        # Scrape the single product
        try:
            scraped_products = await manager.scrape_single_product(
                retailer_code=retailer_code,
                product_url=product['url']
            )
            
            success = len(scraped_products) > 0
            
            # Update job status
            await supabase.update_scrape_job(job['id'], {
                'status': 'completed' if success else 'failed',
                'success_items': 1 if success else 0,
                'failed_items': 0 if success else 1,
                'processed_items': 1
            })
            
            return {
                "message": "Rescrape completed" if success else "Rescrape failed",
                "job_id": job['id'],
                "status": "completed" if success else "failed",
                "retailer": retailer_config.name
            }
            
        except Exception as scrape_error:
            logger.error(f"Scraping error for {retailer_code}: {str(scrape_error)}")
            
            # Update job as failed
            await supabase.update_scrape_job(job['id'], {
                'status': 'failed',
                'failed_items': 1,
                'processed_items': 1,
                'error_message': str(scrape_error)
            })
            
            return {
                "message": "Rescrape failed",
                "job_id": job['id'],
                "status": "failed",
                "error": str(scrape_error)
            }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Rescrape error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to trigger rescrape")