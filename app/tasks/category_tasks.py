"""
Celery tasks for category monitoring
"""
import asyncio
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from celery import shared_task
from celery.utils.log import get_task_logger

from app.services.category_monitor import CategoryMonitor
from app.services.supabase_service import SupabaseService
from app.models.schedule import ScheduleStatus

logger = get_task_logger(__name__)


@shared_task(bind=True, name='app.tasks.category_tasks.monitor_categories')
def monitor_categories(self, retailer_code: Optional[str] = None, force_full_scan: bool = False, **kwargs):
    """
    Monitor categories for changes
    
    Args:
        retailer_code: Optional specific retailer to monitor (None = all retailers)
        force_full_scan: Force a full scan instead of incremental
        **kwargs: Additional parameters from schedule configuration
    
    Returns:
        Dict with monitoring results
    """
    task_id = self.request.id
    schedule_id = kwargs.get('schedule_id')
    
    logger.info(f"Starting category monitoring task {task_id}")
    logger.info(f"Parameters: retailer_code={retailer_code}, force_full_scan={force_full_scan}")
    
    # Record task start in schedule history if schedule_id provided
    db = SupabaseService()
    history_id = None
    
    if schedule_id:
        try:
            history_data = {
                'schedule_id': schedule_id,
                'started_at': datetime.now().isoformat(),
                'status': ScheduleStatus.RUNNING
            }
            result = db.client.table('monitoring_schedule_history').insert(history_data).execute()
            if result.data:
                history_id = result.data[0]['id']
        except Exception as e:
            logger.error(f"Failed to record schedule history: {e}")
    
    # Run monitoring
    start_time = datetime.now()
    results = {
        'retailers_monitored': [],
        'total_categories_checked': 0,
        'changes_detected': 0,
        'errors': [],
        'alerts_created': 0
    }
    
    try:
        # Run async monitoring in sync context
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        monitor = CategoryMonitor()
        
        if retailer_code:
            # Monitor specific retailer
            logger.info(f"Monitoring retailer: {retailer_code}")
            try:
                monitoring_result = loop.run_until_complete(
                    monitor.monitor_retailer(retailer_code, force_full_scan=force_full_scan)
                )
                results['retailers_monitored'].append(retailer_code)
                results['total_categories_checked'] += monitoring_result.get('categories_checked', 0)
                results['changes_detected'] += monitoring_result.get('changes_found', 0)
                results['alerts_created'] += monitoring_result.get('alerts_created', 0)
                
            except Exception as e:
                logger.error(f"Error monitoring retailer {retailer_code}: {e}")
                results['errors'].append({
                    'retailer': retailer_code,
                    'error': str(e)
                })
        else:
            # Monitor all retailers
            retailers = ['HP', 'TWD', 'GH', 'DH', 'BT', 'MH']
            logger.info(f"Monitoring all retailers: {retailers}")
            
            for code in retailers:
                try:
                    monitoring_result = loop.run_until_complete(
                        monitor.monitor_retailer(code, force_full_scan=force_full_scan)
                    )
                    results['retailers_monitored'].append(code)
                    results['total_categories_checked'] += monitoring_result.get('categories_checked', 0)
                    results['changes_detected'] += monitoring_result.get('changes_found', 0)
                    results['alerts_created'] += monitoring_result.get('alerts_created', 0)
                    
                except Exception as e:
                    logger.error(f"Error monitoring retailer {code}: {e}")
                    results['errors'].append({
                        'retailer': code,
                        'error': str(e)
                    })
        
        loop.close()
        
        # Calculate duration
        duration = (datetime.now() - start_time).total_seconds()
        results['duration_seconds'] = int(duration)
        results['success'] = len(results['errors']) == 0
        
        # Update schedule status
        if schedule_id:
            try:
                # Update schedule last run info
                schedule_update = {
                    'last_run': datetime.now().isoformat(),
                    'last_status': ScheduleStatus.SUCCESS if results['success'] else ScheduleStatus.FAILURE,
                    'last_error': results['errors'][0]['error'] if results['errors'] else None
                }
                db.client.table('monitoring_schedules').update(schedule_update).eq('id', schedule_id).execute()
                
                # Update history record
                if history_id:
                    history_update = {
                        'completed_at': datetime.now().isoformat(),
                        'status': ScheduleStatus.SUCCESS if results['success'] else ScheduleStatus.FAILURE,
                        'result': results,
                        'duration_seconds': results['duration_seconds'],
                        'items_processed': results['total_categories_checked'],
                        'items_failed': len(results['errors'])
                    }
                    db.client.table('monitoring_schedule_history').update(history_update).eq('id', history_id).execute()
                    
            except Exception as e:
                logger.error(f"Failed to update schedule status: {e}")
        
        logger.info(f"Category monitoring completed: {results}")
        return results
        
    except Exception as e:
        logger.error(f"Category monitoring task failed: {e}")
        
        # Update failure status
        if schedule_id and history_id:
            try:
                db.client.table('monitoring_schedule_history').update({
                    'completed_at': datetime.now().isoformat(),
                    'status': ScheduleStatus.FAILURE,
                    'error_message': str(e),
                    'duration_seconds': int((datetime.now() - start_time).total_seconds())
                }).eq('id', history_id).execute()
                
                db.client.table('monitoring_schedules').update({
                    'last_run': datetime.now().isoformat(),
                    'last_status': ScheduleStatus.FAILURE,
                    'last_error': str(e)
                }).eq('id', schedule_id).execute()
                
            except Exception as update_e:
                logger.error(f"Failed to update failure status: {update_e}")
        
        raise


@shared_task(name='app.tasks.category_tasks.verify_category')
def verify_category(category_id: str, retailer_code: str):
    """
    Verify a specific category
    
    Args:
        category_id: Category ID to verify
        retailer_code: Retailer code
    
    Returns:
        Dict with verification results
    """
    logger.info(f"Verifying category {category_id} for retailer {retailer_code}")
    
    try:
        # Run async verification in sync context
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        monitor = CategoryMonitor()
        result = loop.run_until_complete(
            monitor.verify_category(category_id, retailer_code)
        )
        
        loop.close()
        
        logger.info(f"Category verification completed: {result}")
        return result
        
    except Exception as e:
        logger.error(f"Category verification failed: {e}")
        raise


@shared_task(name='app.tasks.category_tasks.discover_categories')
def discover_categories(retailer_code: str, max_depth: int = 3):
    """
    Discover new categories for a retailer
    
    Args:
        retailer_code: Retailer code
        max_depth: Maximum depth to explore
    
    Returns:
        Dict with discovery results
    """
    logger.info(f"Discovering categories for retailer {retailer_code} with max_depth={max_depth}")
    
    try:
        # Run async discovery in sync context
        from app.core.category_explorer import CategoryExplorer
        
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        explorer = CategoryExplorer(retailer_code)
        
        # Get retailer config
        from app.config.retailers import RETAILER_CONFIGS
        retailer_config = RETAILER_CONFIGS.get(retailer_code)
        
        if not retailer_config:
            raise ValueError(f"Unknown retailer: {retailer_code}")
        
        categories = loop.run_until_complete(
            explorer.discover_categories(
                base_url=retailer_config['base_url'],
                max_depth=max_depth
            )
        )
        
        loop.close()
        
        result = {
            'retailer_code': retailer_code,
            'categories_discovered': len(categories),
            'categories': categories
        }
        
        logger.info(f"Category discovery completed: Found {len(categories)} categories")
        return result
        
    except Exception as e:
        logger.error(f"Category discovery failed: {e}")
        raise


@shared_task(name='app.tasks.category_tasks.cleanup_old_history')
def cleanup_old_history(days_to_keep: int = 30):
    """
    Clean up old schedule history records
    
    Args:
        days_to_keep: Number of days of history to keep
    
    Returns:
        Number of records deleted
    """
    logger.info(f"Cleaning up schedule history older than {days_to_keep} days")
    
    try:
        db = SupabaseService()
        cutoff_date = (datetime.now() - timedelta(days=days_to_keep)).isoformat()
        
        # Delete old history records
        result = db.client.table('monitoring_schedule_history').delete().lt('created_at', cutoff_date).execute()
        
        deleted_count = len(result.data) if result.data else 0
        logger.info(f"Deleted {deleted_count} old history records")
        
        return deleted_count
        
    except Exception as e:
        logger.error(f"History cleanup failed: {e}")
        raise