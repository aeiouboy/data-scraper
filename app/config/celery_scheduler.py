"""
Custom Celery Beat Scheduler that loads schedules from database
"""
from celery.beat import ScheduleEntry, Scheduler
from datetime import datetime
import json
import logging

logger = logging.getLogger(__name__)


class DatabaseScheduler(Scheduler):
    """
    Custom scheduler that loads schedules from Supabase database
    and supports dynamic updates without restart
    """
    
    def __init__(self, *args, **kwargs):
        self._schedule = {}
        self._last_sync = None
        self.sync_interval = 60  # Sync with database every 60 seconds
        super().__init__(*args, **kwargs)
    
    def setup_schedule(self):
        """Initial schedule setup"""
        self.sync_schedules()
    
    def sync_schedules(self):
        """Sync schedules from database"""
        from app.services.supabase_service import SupabaseService
        from app.models.schedule import MonitoringSchedule
        
        try:
            logger.info("Syncing schedules from database")
            
            db = SupabaseService()
            
            # Get all enabled schedules
            result = db.client.table('monitoring_schedules').select('*').eq('enabled', True).execute()
            
            if result.data:
                new_schedule = {}
                
                for schedule_data in result.data:
                    try:
                        schedule = MonitoringSchedule(**schedule_data)
                        beat_entry = schedule.to_celery_beat_schedule()
                        
                        # Add schedule_id to kwargs for tracking
                        beat_entry['kwargs']['schedule_id'] = str(schedule.id)
                        
                        # Create schedule entry
                        entry = ScheduleEntry(
                            name=schedule.task_name,
                            task=beat_entry['task'],
                            schedule=beat_entry['schedule'],
                            args=beat_entry.get('args', []),
                            kwargs=beat_entry.get('kwargs', {}),
                            options=beat_entry.get('options', {}),
                            app=self.app
                        )
                        
                        new_schedule[schedule.task_name] = entry
                        logger.info(f"Loaded schedule: {schedule.task_name}")
                        
                    except Exception as e:
                        logger.error(f"Error loading schedule {schedule_data.get('task_name')}: {e}")
                
                # Update schedule
                self._schedule = new_schedule
                self._last_sync = datetime.now()
                
                # Update next run times in database
                self.update_next_run_times()
                
                logger.info(f"Synced {len(new_schedule)} schedules from database")
            else:
                logger.warning("No enabled schedules found in database")
                self._schedule = {}
                
        except Exception as e:
            logger.error(f"Error syncing schedules from database: {e}")
            # Keep existing schedule on error
    
    def update_next_run_times(self):
        """Update next run times in database"""
        from app.services.supabase_service import SupabaseService
        
        try:
            db = SupabaseService()
            
            for name, entry in self._schedule.items():
                next_run = entry.schedule.remaining_estimate(entry.last_run_at)
                if next_run:
                    next_run_time = datetime.now() + next_run
                    
                    # Update in database
                    db.client.table('monitoring_schedules').update({
                        'next_run': next_run_time.isoformat()
                    }).eq('task_name', name).execute()
                    
        except Exception as e:
            logger.error(f"Error updating next run times: {e}")
    
    @property
    def schedule(self):
        """
        Get current schedule, syncing with database if needed
        """
        # Check if we need to sync
        if self._last_sync is None or \
           (datetime.now() - self._last_sync).total_seconds() > self.sync_interval:
            self.sync_schedules()
        
        return self._schedule
    
    @schedule.setter
    def schedule(self, value):
        """Set schedule"""
        self._schedule = value
    
    def tick(self):
        """
        Run one tick of the scheduler
        This is called by Celery Beat
        """
        # Update next run times periodically
        if hasattr(self, '_tick_count'):
            self._tick_count += 1
            if self._tick_count % 60 == 0:  # Every 60 ticks
                self.update_next_run_times()
        else:
            self._tick_count = 0
        
        return super().tick()
    
    def close(self):
        """Cleanup on scheduler close"""
        logger.info("Closing database scheduler")
        super().close()


class DatabaseScheduleEntry(ScheduleEntry):
    """
    Custom schedule entry that updates database on execution
    """
    
    def __next__(self):
        """Get next execution time and update database"""
        next_time = super().__next__()
        
        # Update last run time in database
        try:
            from app.services.supabase_service import SupabaseService
            
            db = SupabaseService()
            db.client.table('monitoring_schedules').update({
                'last_run': datetime.now().isoformat(),
                'next_run': next_time.isoformat() if next_time else None
            }).eq('task_name', self.name).execute()
            
        except Exception as e:
            logger.error(f"Error updating schedule {self.name} in database: {e}")
        
        return next_time