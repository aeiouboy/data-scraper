"""
Analytics API endpoints
"""
from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, Any, List
import logging

from app.api.models import AnalyticsResponse
from app.services.supabase_service import SupabaseService

logger = logging.getLogger(__name__)
router = APIRouter()


def get_supabase() -> SupabaseService:
    """Dependency to get Supabase service"""
    return SupabaseService()


@router.get("/dashboard", response_model=AnalyticsResponse)
async def get_dashboard_analytics(
    supabase: SupabaseService = Depends(get_supabase)
):
    """Get analytics dashboard data"""
    try:
        # Try to get basic product counts
        try:
            products_result = await supabase.client.table('products').select('id', count='exact').execute()
            total_products = products_result.count or 0
        except:
            total_products = 0
        
        # Try to get products with prices
        try:
            price_result = await supabase.client.table('products')\
                .select('current_price')\
                .not_('current_price', 'is', None)\
                .execute()
            
            prices = [float(p['current_price']) for p in price_result.data if p.get('current_price')]
            avg_price = sum(prices) / len(prices) if prices else 0
            products_on_sale = len([p for p in price_result.data if p.get('discount_percentage', 0) > 0])
        except:
            avg_price = 0
            products_on_sale = 0
        
        # Try to get scrape jobs
        try:
            jobs_result = await supabase.client.table('scrape_jobs').select('id', count='exact').execute()
            total_jobs = jobs_result.count or 0
        except:
            total_jobs = 0
        
        # Mock data for now - replace with real data when database is populated
        product_stats = {
            "total_products": total_products,
            "average_price": round(avg_price, 2),
            "products_on_sale": products_on_sale,
            "last_updated": "2025-06-27T17:00:00Z"
        }
        
        daily_stats = [
            {"date": "2025-06-27", "total_jobs": total_jobs, "total_success": 0, "total_failed": 0},
            {"date": "2025-06-26", "total_jobs": 0, "total_success": 0, "total_failed": 0},
            {"date": "2025-06-25", "total_jobs": 0, "total_success": 0, "total_failed": 0},
        ]
        
        brand_distribution = [
            {"brand": "HomePro", "count": 25},
            {"brand": "Sample Brand", "count": 10}
        ]
        
        category_distribution = [
            {"category": "Electronics", "count": 15},
            {"category": "Tools", "count": 20}
        ]
        
        price_ranges = {
            "0-500": 5,
            "500-1000": 10,
            "1000-2000": 8,
            "2000-5000": 12,
            "5000+": 3
        }
        
        return AnalyticsResponse(
            product_stats=product_stats,
            daily_stats=daily_stats,
            brand_distribution=brand_distribution,
            category_distribution=category_distribution,
            price_distribution=price_ranges
        )
        
    except Exception as e:
        logger.error(f"Analytics error: {str(e)}")
        # Return mock data if everything fails
        return AnalyticsResponse(
            product_stats={
                "total_products": 0,
                "average_price": 0,
                "products_on_sale": 0,
                "last_updated": "2025-06-27T17:00:00Z"
            },
            daily_stats=[],
            brand_distribution=[],
            category_distribution=[],
            price_distribution={"0-500": 0, "500-1000": 0, "1000-2000": 0, "2000-5000": 0, "5000+": 0}
        )


@router.get("/products/trends")
async def get_product_trends(
    days: int = 30,
    supabase: SupabaseService = Depends(get_supabase)
):
    """Get product trends over time"""
    try:
        # Get products with biggest price changes
        query = f"""
        WITH price_changes AS (
            SELECT 
                p.id,
                p.name,
                p.brand,
                p.current_price,
                p.original_price,
                p.discount_percentage,
                ph.price as historical_price,
                ph.recorded_at,
                (p.current_price - ph.price) as price_change,
                ((p.current_price - ph.price) / ph.price * 100) as price_change_percent
            FROM products p
            JOIN price_history ph ON p.id = ph.product_id
            WHERE ph.recorded_at > NOW() - INTERVAL '{days} days'
            ORDER BY ABS(price_change_percent) DESC
            LIMIT 20
        )
        SELECT * FROM price_changes;
        """
        
        # Execute raw SQL (Note: In production, use proper parameterized queries)
        # For now, return mock data
        trends = {
            "period_days": days,
            "price_increases": [],
            "price_decreases": [],
            "new_products": [],
            "out_of_stock": []
        }
        
        return trends
        
    except Exception as e:
        logger.error(f"Trends error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get trends")


@router.get("/scraping/performance")
async def get_scraping_performance(
    days: int = 30,
    supabase: SupabaseService = Depends(get_supabase)
):
    """Get scraping performance metrics"""
    try:
        # Get daily scrape stats
        daily_stats = await supabase.get_daily_scrape_stats(days=days)
        
        # Calculate aggregates
        total_jobs = sum(stat.get('total_jobs', 0) for stat in daily_stats)
        total_success = sum(stat.get('total_success', 0) for stat in daily_stats)
        total_failed = sum(stat.get('total_failed', 0) for stat in daily_stats)
        
        avg_success_rate = (total_success / (total_success + total_failed) * 100) if (total_success + total_failed) > 0 else 0
        
        # Get job duration stats
        recent_jobs = await supabase.get_scrape_jobs(limit=100)
        
        durations = []
        for job in recent_jobs:
            if job.get('started_at') and job.get('completed_at'):
                # Calculate duration in seconds
                # Note: This is simplified - in production, parse timestamps properly
                durations.append(60)  # Mock 60 seconds
        
        avg_duration = sum(durations) / len(durations) if durations else 0
        
        return {
            "period_days": days,
            "total_jobs": total_jobs,
            "total_products_scraped": total_success,
            "total_failures": total_failed,
            "average_success_rate": round(avg_success_rate, 2),
            "average_job_duration_seconds": round(avg_duration, 2),
            "daily_stats": daily_stats
        }
        
    except Exception as e:
        logger.error(f"Performance metrics error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get performance metrics")