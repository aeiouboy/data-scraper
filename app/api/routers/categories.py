"""
Category Discovery and Management API endpoints
"""
from fastapi import APIRouter, HTTPException, Query, BackgroundTasks
from typing import List, Optional, Dict, Any
from datetime import datetime
import logging

from app.core.category_explorer import CategoryExplorer
from app.services.category_monitor import CategoryMonitor
from app.core.scraper_config_manager import ScraperConfigManager
from app.services.supabase_service import SupabaseService
from app.config.retailers import retailer_manager

logger = logging.getLogger(__name__)

router = APIRouter(
    tags=["categories"]
)


@router.get("/discover")
async def trigger_category_discovery(
    retailer_code: str = Query(..., description="Retailer code (e.g., HP, TWD)"),
    max_depth: int = Query(3, ge=1, le=5, description="Maximum depth to explore"),
    max_categories: int = Query(500, ge=10, le=1000, description="Maximum categories to discover"),
    background_tasks: BackgroundTasks = BackgroundTasks()
):
    """
    Trigger category discovery for a retailer
    
    This endpoint starts a background task to discover categories.
    """
    try:
        # Validate retailer
        retailer = retailer_manager.get_retailer_by_code(retailer_code)
        if not retailer:
            raise HTTPException(status_code=404, detail=f"Retailer {retailer_code} not found")
        
        # Create job record
        db = SupabaseService()
        job = await db.create_scrape_job(
            job_type='category_discovery',
            target_url=retailer.base_url
        )
        
        # Start discovery in background
        background_tasks.add_task(
            run_category_discovery,
            retailer_code,
            max_depth,
            max_categories,
            job['id'] if job else None
        )
        
        return {
            "message": "Category discovery started",
            "retailer": retailer.name,
            "job_id": job['id'] if job else None,
            "max_depth": max_depth,
            "max_categories": max_categories
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error triggering category discovery: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to start category discovery")


async def run_category_discovery(
    retailer_code: str,
    max_depth: int,
    max_categories: int,
    job_id: Optional[str] = None
):
    """Background task to run category discovery"""
    explorer = CategoryExplorer()
    db = SupabaseService()
    
    try:
        # Update job status
        if job_id:
            await db.update_scrape_job(job_id, {
                'status': 'running',
                'retailer_code': retailer_code
            })
        
        # Run discovery
        result = await explorer.discover_all_categories(
            retailer_code=retailer_code,
            max_depth=max_depth,
            max_categories=max_categories
        )
        
        # Update job with results
        if job_id:
            await db.update_scrape_job(job_id, {
                'status': 'completed',
                'processed_items': result['discovered_count'],
                'success_items': result['saved_count'],
                'duration_seconds': result['duration_seconds']
            })
            
    except Exception as e:
        logger.error(f"Category discovery failed: {str(e)}")
        if job_id:
            await db.update_scrape_job(job_id, {
                'status': 'failed',
                'error_message': str(e)
            })


@router.get("/tree/{retailer_code}")
async def get_category_tree(
    retailer_code: str,
    include_inactive: bool = Query(False, description="Include inactive categories")
):
    """Get hierarchical category tree for a retailer"""
    try:
        db = SupabaseService()
        
        # Build query
        query = db.client.table('retailer_categories')\
            .select('*')\
            .eq('retailer_code', retailer_code)\
            .order('level', desc=False)\
            .order('position', desc=False)
            
        if not include_inactive:
            query = query.eq('is_active', True)
            
        result = query.execute()
        categories = result.data if result.data else []
        
        # Build tree structure
        tree = build_category_tree(categories)
        
        return {
            "retailer_code": retailer_code,
            "total_categories": len(categories),
            "tree": tree
        }
        
    except Exception as e:
        logger.error(f"Error fetching category tree: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to fetch category tree")


def build_category_tree(categories: List[Dict]) -> List[Dict]:
    """Build hierarchical tree from flat category list"""
    # Create lookup by ID
    by_id = {cat['id']: cat for cat in categories}
    
    # Initialize children lists
    for cat in categories:
        cat['children'] = []
    
    # Build tree
    roots = []
    for cat in categories:
        if cat['parent_category_id']:
            parent = by_id.get(cat['parent_category_id'])
            if parent:
                parent['children'].append(cat)
        else:
            roots.append(cat)
    
    return roots


@router.get("/changes")
async def get_category_changes(
    retailer_code: Optional[str] = Query(None, description="Filter by retailer"),
    days: int = Query(7, ge=1, le=30, description="Number of days to look back"),
    change_type: Optional[str] = Query(None, description="Filter by change type")
):
    """Get recent category changes"""
    try:
        monitor = CategoryMonitor()
        changes = await monitor.get_recent_changes(retailer_code, days)
        
        # Filter by change type if specified
        if change_type:
            changes = [c for c in changes if c['change_type'] == change_type]
        
        return {
            "total_changes": len(changes),
            "period_days": days,
            "changes": changes
        }
        
    except Exception as e:
        logger.error(f"Error fetching category changes: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to fetch category changes")


@router.post("/monitor")
async def trigger_category_monitoring(
    retailer_code: Optional[str] = Query(None, description="Monitor specific retailer or all"),
    background_tasks: BackgroundTasks = BackgroundTasks()
):
    """Trigger category monitoring"""
    try:
        # Start monitoring in background
        background_tasks.add_task(
            run_category_monitoring,
            retailer_code
        )
        
        return {
            "message": "Category monitoring started",
            "retailer": retailer_code or "all retailers"
        }
        
    except Exception as e:
        logger.error(f"Error triggering monitoring: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to start monitoring")


async def run_category_monitoring(retailer_code: Optional[str] = None):
    """Background task to run category monitoring"""
    monitor = CategoryMonitor()
    
    try:
        if retailer_code:
            await monitor.monitor_retailer(retailer_code)
        else:
            await monitor.monitor_all_retailers()
            
    except Exception as e:
        logger.error(f"Category monitoring failed: {str(e)}")


@router.get("/health/{retailer_code}")
async def get_category_health(retailer_code: str):
    """Get category health metrics for a retailer"""
    try:
        monitor = CategoryMonitor()
        health = await monitor.get_category_health(retailer_code)
        
        return health
        
    except Exception as e:
        logger.error(f"Error fetching category health: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to fetch category health")


@router.post("/verify/{category_id}")
async def verify_category(category_id: str):
    """Verify a single category is still valid"""
    try:
        db = SupabaseService()
        
        # Get category
        result = db.client.table('retailer_categories')\
            .select('*')\
            .eq('id', category_id)\
            .single()\
            .execute()
            
        if not result.data:
            raise HTTPException(status_code=404, detail="Category not found")
            
        category = result.data
        
        # Use explorer to verify
        explorer = CategoryExplorer()
        verification = await explorer.discover_single_category(
            category['retailer_code'],
            category['category_url']
        )
        
        # Update verification timestamp
        db.client.table('retailer_categories')\
            .update({'last_verified': datetime.now().isoformat()})\
            .eq('id', category_id)\
            .execute()
            
        return {
            "category_id": category_id,
            "is_valid": verification is not None,
            "verification": verification
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error verifying category: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to verify category")


@router.put("/{category_id}/activate")
async def activate_category(category_id: str):
    """Activate a category"""
    return update_category_status(category_id, True)


@router.put("/{category_id}/deactivate") 
async def deactivate_category(category_id: str):
    """Deactivate a category"""
    return update_category_status(category_id, False)


def update_category_status(category_id: str, is_active: bool):
    """Update category active status"""
    try:
        db = SupabaseService()
        
        result = db.client.table('retailer_categories')\
            .update({
                'is_active': is_active,
                'updated_at': datetime.now().isoformat()
            })\
            .eq('id', category_id)\
            .execute()
            
        if not result.data:
            raise HTTPException(status_code=404, detail="Category not found")
            
        return {
            "category_id": category_id,
            "is_active": is_active,
            "message": f"Category {'activated' if is_active else 'deactivated'}"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating category status: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to update category")


@router.get("/stats")
async def get_category_statistics(
    retailer_code: Optional[str] = Query(None, description="Filter by retailer")
):
    """Get category statistics across retailers"""
    try:
        db = SupabaseService()
        
        # Build query
        query = db.client.table('retailer_categories').select('*')
        
        if retailer_code:
            query = query.eq('retailer_code', retailer_code)
            
        result = query.execute()
        categories = result.data if result.data else []
        
        # Calculate statistics
        stats = {}
        for cat in categories:
            rc = cat['retailer_code']
            if rc not in stats:
                stats[rc] = {
                    'total': 0,
                    'active': 0,
                    'inactive': 0,
                    'auto_discovered': 0,
                    'by_level': {},
                    'total_products': 0
                }
            
            stats[rc]['total'] += 1
            if cat['is_active']:
                stats[rc]['active'] += 1
            else:
                stats[rc]['inactive'] += 1
                
            if cat['is_auto_discovered']:
                stats[rc]['auto_discovered'] += 1
                
            level = str(cat['level'])
            stats[rc]['by_level'][level] = stats[rc]['by_level'].get(level, 0) + 1
            
            stats[rc]['total_products'] += cat.get('product_count', 0)
        
        return {
            "retailer_stats": stats,
            "total_categories": len(categories),
            "total_active": sum(s['active'] for s in stats.values()),
            "total_products": sum(s['total_products'] for s in stats.values())
        }
        
    except Exception as e:
        logger.error(f"Error calculating category stats: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to calculate statistics")


@router.post("/import")
async def import_categories(
    retailer_code: str,
    categories: List[Dict[str, Any]]
):
    """Import category list for a retailer"""
    try:
        db = SupabaseService()
        imported_count = 0
        
        for cat_data in categories:
            try:
                # Prepare category data
                category = {
                    'retailer_code': retailer_code,
                    'category_code': cat_data['code'],
                    'category_name': cat_data['name'],
                    'category_url': cat_data['url'],
                    'level': cat_data.get('level', 0),
                    'is_active': True,
                    'is_auto_discovered': False,
                    'discovered_at': datetime.now().isoformat()
                }
                
                # Check if exists
                existing = db.client.table('retailer_categories')\
                    .select('id')\
                    .eq('retailer_code', retailer_code)\
                    .eq('category_code', cat_data['code'])\
                    .execute()
                    
                if existing.data:
                    # Update existing
                    db.client.table('retailer_categories')\
                        .update(category)\
                        .eq('id', existing.data[0]['id'])\
                        .execute()
                else:
                    # Insert new
                    db.client.table('retailer_categories')\
                        .insert(category)\
                        .execute()
                        
                imported_count += 1
                
            except Exception as e:
                logger.error(f"Error importing category {cat_data.get('code')}: {str(e)}")
        
        return {
            "message": "Categories imported",
            "retailer_code": retailer_code,
            "total_provided": len(categories),
            "imported_count": imported_count
        }
        
    except Exception as e:
        logger.error(f"Error importing categories: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to import categories")