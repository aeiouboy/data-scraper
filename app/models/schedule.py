"""
Schedule models for monitoring automation
"""
from datetime import datetime
from typing import Optional, Dict, Any, Literal
from uuid import UUID
from pydantic import BaseModel, Field, validator
from enum import Enum
import json


class ScheduleType(str, Enum):
    """Schedule type enumeration"""
    INTERVAL = "interval"
    CRON = "cron"


class TaskType(str, Enum):
    """Task type enumeration"""
    CATEGORY_MONITOR = "category_monitor"
    PRODUCT_SCRAPE = "product_scrape"
    PRICE_UPDATE = "price_update"
    INVENTORY_CHECK = "inventory_check"


class ScheduleStatus(str, Enum):
    """Schedule execution status"""
    SUCCESS = "success"
    FAILURE = "failure"
    RUNNING = "running"


class IntervalSchedule(BaseModel):
    """Interval-based schedule configuration"""
    days: Optional[int] = 0
    hours: Optional[int] = 0
    minutes: Optional[int] = 0
    seconds: Optional[int] = 0
    
    @validator('*', pre=True)
    def validate_positive(cls, v):
        if v is not None and v < 0:
            raise ValueError("Interval values must be positive")
        return v
    
    def to_celery_schedule(self):
        """Convert to Celery schedule format"""
        from datetime import timedelta
        return timedelta(
            days=self.days or 0,
            hours=self.hours or 0,
            minutes=self.minutes or 0,
            seconds=self.seconds or 0
        )


class CronSchedule(BaseModel):
    """Cron-based schedule configuration"""
    minute: str = "*"
    hour: str = "*"
    day_of_week: str = "*"
    day_of_month: str = "*"
    month_of_year: str = "*"
    
    def to_celery_schedule(self):
        """Convert to Celery crontab format"""
        from celery.schedules import crontab
        return crontab(
            minute=self.minute,
            hour=self.hour,
            day_of_week=self.day_of_week,
            day_of_month=self.day_of_month,
            month_of_year=self.month_of_year
        )


class MonitoringSchedule(BaseModel):
    """Monitoring schedule model"""
    id: Optional[UUID] = None
    task_name: str = Field(..., max_length=100)
    task_type: TaskType = TaskType.CATEGORY_MONITOR
    description: Optional[str] = None
    
    # Schedule configuration
    schedule_type: ScheduleType
    schedule_value: Dict[str, Any]
    
    # Task parameters
    task_params: Dict[str, Any] = Field(default_factory=dict)
    
    # Status fields
    enabled: bool = True
    last_run: Optional[datetime] = None
    next_run: Optional[datetime] = None
    last_status: Optional[ScheduleStatus] = None
    last_error: Optional[str] = None
    
    # Metadata
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    created_by: Optional[str] = None
    updated_by: Optional[str] = None
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None,
            UUID: lambda v: str(v) if v else None
        }
    
    def get_schedule_object(self):
        """Get the appropriate schedule object based on schedule_type"""
        schedule_type_value = self.schedule_type.value if hasattr(self.schedule_type, 'value') else self.schedule_type
        if schedule_type_value == ScheduleType.INTERVAL.value:
            return IntervalSchedule(**self.schedule_value)
        elif schedule_type_value == ScheduleType.CRON.value:
            return CronSchedule(**self.schedule_value)
        else:
            raise ValueError(f"Unknown schedule type: {self.schedule_type}")
    
    def to_celery_beat_schedule(self):
        """Convert to Celery Beat schedule entry"""
        schedule_obj = self.get_schedule_object()
        
        # Map task types to actual Celery tasks
        task_mapping = {
            TaskType.CATEGORY_MONITOR.value: "app.tasks.category_tasks.monitor_categories",
            TaskType.PRODUCT_SCRAPE.value: "app.tasks.scraping_tasks.scrape_products",
            TaskType.PRICE_UPDATE.value: "app.tasks.scraping_tasks.update_prices",
            TaskType.INVENTORY_CHECK.value: "app.tasks.scraping_tasks.check_inventory"
        }
        
        return {
            "task": task_mapping.get(self.task_type.value if hasattr(self.task_type, 'value') else self.task_type, "app.tasks.category_tasks.monitor_categories"),
            "schedule": schedule_obj.to_celery_schedule(),
            "args": [],
            "kwargs": self.task_params,
            "options": {
                "expires": 3600,  # Task expires after 1 hour if not executed
                "retry": True,
                "retry_policy": {
                    "max_retries": 3,
                    "interval_start": 60,
                    "interval_step": 120,
                    "interval_max": 600
                }
            }
        }


class ScheduleHistory(BaseModel):
    """Schedule execution history"""
    id: Optional[UUID] = None
    schedule_id: UUID
    started_at: datetime = Field(default_factory=datetime.now)
    completed_at: Optional[datetime] = None
    status: ScheduleStatus
    result: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    
    # Performance metrics
    duration_seconds: Optional[int] = None
    items_processed: Optional[int] = None
    items_failed: Optional[int] = None
    
    created_at: Optional[datetime] = None
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None,
            UUID: lambda v: str(v) if v else None
        }


# Request/Response models for API
class ScheduleCreate(BaseModel):
    """Create schedule request"""
    task_name: str = Field(..., max_length=100)
    task_type: TaskType = TaskType.CATEGORY_MONITOR
    description: Optional[str] = None
    schedule_type: ScheduleType
    schedule_value: Dict[str, Any]
    task_params: Dict[str, Any] = Field(default_factory=dict)
    enabled: bool = True


class ScheduleUpdate(BaseModel):
    """Update schedule request"""
    description: Optional[str] = None
    schedule_type: Optional[ScheduleType] = None
    schedule_value: Optional[Dict[str, Any]] = None
    task_params: Optional[Dict[str, Any]] = None
    enabled: Optional[bool] = None


class ScheduleResponse(MonitoringSchedule):
    """Schedule response with computed fields"""
    is_overdue: bool = False
    run_count: int = 0
    success_rate: float = 0.0
    
    @classmethod
    def from_db(cls, schedule_dict: Dict[str, Any], history_stats: Optional[Dict[str, Any]] = None):
        """Create response from database record with computed fields"""
        schedule = cls(**schedule_dict)
        
        if history_stats:
            schedule.run_count = history_stats.get('total_runs', 0)
            if schedule.run_count > 0:
                schedule.success_rate = history_stats.get('successful_runs', 0) / schedule.run_count * 100
        
        # Check if schedule is overdue
        if schedule.enabled and schedule.next_run:
            schedule.is_overdue = datetime.now() > schedule.next_run
        
        return schedule