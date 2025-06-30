"""
Celery configuration with dynamic schedule loading from database
"""
import os
from celery import Celery
from celery.schedules import crontab
from datetime import timedelta
from kombu import Exchange, Queue

# Redis configuration
REDIS_URL = os.getenv('REDIS_URL', 'redis://localhost:6379/0')

# Celery app configuration
celery_app = Celery('homepro_scraper')

celery_app.conf.update(
    broker_url=REDIS_URL,
    result_backend=REDIS_URL,
    
    # Task settings
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='Asia/Bangkok',
    enable_utc=True,
    
    # Task routing
    task_routes={
        'app.tasks.category_tasks.*': {'queue': 'monitoring'},
        'app.tasks.scraping_tasks.*': {'queue': 'scraping'},
    },
    
    # Queue configuration
    task_queues=(
        Queue('monitoring', Exchange('monitoring'), routing_key='monitoring'),
        Queue('scraping', Exchange('scraping'), routing_key='scraping'),
        Queue('default', Exchange('default'), routing_key='default'),
    ),
    
    # Worker settings
    worker_prefetch_multiplier=4,
    worker_max_tasks_per_child=1000,
    
    # Task execution settings
    task_soft_time_limit=1800,  # 30 minutes
    task_time_limit=3600,  # 1 hour
    
    # Result backend settings
    result_expires=86400,  # 24 hours
    
    # Beat settings for scheduled tasks
    beat_scheduler='app.config.celery_scheduler:DatabaseScheduler',
    beat_schedule={
        # Default schedules (will be overridden by database schedules)
        'cleanup-old-history': {
            'task': 'app.tasks.category_tasks.cleanup_old_history',
            'schedule': crontab(hour=0, minute=0),  # Daily at midnight
            'kwargs': {'days_to_keep': 30}
        },
    }
)

# Import tasks to register them
celery_app.autodiscover_tasks(['app.tasks'])


def setup_periodic_tasks(sender, **kwargs):
    """
    Setup periodic tasks from database
    This function is called when Celery Beat starts
    """
    from app.services.supabase_service import SupabaseService
    from app.models.schedule import MonitoringSchedule
    
    print("Loading schedules from database...")
    
    try:
        db = SupabaseService()
        
        # Get all enabled schedules
        result = db.client.table('monitoring_schedules').select('*').eq('enabled', True).execute()
        
        if result.data:
            for schedule_data in result.data:
                try:
                    schedule = MonitoringSchedule(**schedule_data)
                    
                    # Add to beat schedule
                    beat_entry = schedule.to_celery_beat_schedule()
                    
                    # Add schedule_id to kwargs for tracking
                    beat_entry['kwargs']['schedule_id'] = str(schedule.id)
                    
                    # Register with Celery Beat
                    sender.add_periodic_task(
                        beat_entry['schedule'],
                        beat_entry['task'],
                        name=schedule.task_name,
                        kwargs=beat_entry['kwargs'],
                        options=beat_entry['options']
                    )
                    
                    print(f"Loaded schedule: {schedule.task_name}")
                    
                except Exception as e:
                    print(f"Error loading schedule {schedule_data.get('task_name')}: {e}")
        
        print("Schedule loading completed")
        
    except Exception as e:
        print(f"Error loading schedules from database: {e}")


# Register the setup function
celery_app.on_after_configure.connect(setup_periodic_tasks)