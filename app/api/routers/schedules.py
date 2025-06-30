"""
API endpoints for monitoring schedule management
"""
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from uuid import UUID
from fastapi import APIRouter, HTTPException, Depends, Query
from app.services.supabase_service import SupabaseService
from app.models.schedule import (
    MonitoringSchedule,
    ScheduleCreate,
    ScheduleUpdate,
    ScheduleResponse,
    ScheduleHistory,
    ScheduleType,
    TaskType
)
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/monitoring/schedules", tags=["Monitoring Schedules"])


def get_db() -> SupabaseService:
    """Get database service instance"""
    return SupabaseService()


@router.get("", response_model=List[ScheduleResponse])
async def get_schedules(
    task_type: Optional[TaskType] = None,
    enabled: Optional[bool] = None,
    db: SupabaseService = Depends(get_db)
):
    """
    Get all monitoring schedules
    
    Args:
        task_type: Filter by task type
        enabled: Filter by enabled status
    
    Returns:
        List of schedules with computed fields
    """
    try:
        query = db.client.table('monitoring_schedules').select('*')
        
        if task_type:
            query = query.eq('task_type', task_type)
        if enabled is not None:
            query = query.eq('enabled', enabled)
            
        result = query.order('created_at', desc=False).execute()
        
        schedules = []
        for schedule_data in result.data:
            # Get run statistics
            history_result = db.client.table('monitoring_schedule_history')\
                .select('status')\
                .eq('schedule_id', schedule_data['id'])\
                .execute()
            
            total_runs = len(history_result.data) if history_result.data else 0
            successful_runs = sum(1 for h in (history_result.data or []) if h['status'] == 'success')
            
            history_stats = {
                'total_runs': total_runs,
                'successful_runs': successful_runs
            }
            
            schedule = ScheduleResponse.from_db(schedule_data, history_stats)
            schedules.append(schedule)
        
        return schedules
        
    except Exception as e:
        logger.error(f"Error fetching schedules: {e}")
        raise HTTPException(status_code=500, detail=f"Error fetching schedules: {str(e)}")


@router.get("/{schedule_id}", response_model=ScheduleResponse)
async def get_schedule(
    schedule_id: UUID,
    db: SupabaseService = Depends(get_db)
):
    """Get a specific schedule by ID"""
    try:
        result = db.client.table('monitoring_schedules').select('*').eq('id', str(schedule_id)).single().execute()
        
        if not result.data:
            raise HTTPException(status_code=404, detail="Schedule not found")
        
        # Get run statistics
        history_result = db.client.table('monitoring_schedule_history')\
            .select('status')\
            .eq('schedule_id', str(schedule_id))\
            .execute()
        
        total_runs = len(history_result.data) if history_result.data else 0
        successful_runs = sum(1 for h in (history_result.data or []) if h['status'] == 'success')
        
        history_stats = {
            'total_runs': total_runs,
            'successful_runs': successful_runs
        }
        
        return ScheduleResponse.from_db(result.data, history_stats)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching schedule {schedule_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Error fetching schedule: {str(e)}")


@router.post("", response_model=MonitoringSchedule)
async def create_schedule(
    schedule: ScheduleCreate,
    db: SupabaseService = Depends(get_db)
):
    """Create a new monitoring schedule"""
    try:
        # Validate schedule configuration
        schedule_obj = MonitoringSchedule(**schedule.dict())
        schedule_obj.get_schedule_object()  # Validate schedule_value format
        
        # Check if task_name already exists
        existing = db.client.table('monitoring_schedules').select('id').eq('task_name', schedule.task_name).execute()
        if existing.data:
            raise HTTPException(status_code=400, detail=f"Schedule with task_name '{schedule.task_name}' already exists")
        
        # Insert schedule
        schedule_data = schedule.dict()
        schedule_data['created_at'] = datetime.now().isoformat()
        schedule_data['updated_at'] = datetime.now().isoformat()
        
        result = db.client.table('monitoring_schedules').insert(schedule_data).execute()
        
        if not result.data:
            raise HTTPException(status_code=500, detail="Failed to create schedule")
        
        return MonitoringSchedule(**result.data[0])
        
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid schedule configuration: {str(e)}")
    except Exception as e:
        logger.error(f"Error creating schedule: {e}")
        raise HTTPException(status_code=500, detail=f"Error creating schedule: {str(e)}")


@router.put("/{schedule_id}", response_model=MonitoringSchedule)
async def update_schedule(
    schedule_id: UUID,
    update: ScheduleUpdate,
    db: SupabaseService = Depends(get_db)
):
    """Update an existing schedule"""
    try:
        # Get existing schedule
        existing_result = db.client.table('monitoring_schedules').select('*').eq('id', str(schedule_id)).single().execute()
        
        if not existing_result.data:
            raise HTTPException(status_code=404, detail="Schedule not found")
        
        # Prepare update data
        update_data = {k: v for k, v in update.dict().items() if v is not None}
        
        if not update_data:
            return MonitoringSchedule(**existing_result.data)
        
        # Validate schedule if schedule_type or schedule_value is being updated
        if 'schedule_type' in update_data or 'schedule_value' in update_data:
            test_schedule = MonitoringSchedule(**existing_result.data)
            if 'schedule_type' in update_data:
                test_schedule.schedule_type = update_data['schedule_type']
            if 'schedule_value' in update_data:
                test_schedule.schedule_value = update_data['schedule_value']
            test_schedule.get_schedule_object()  # Validate
        
        update_data['updated_at'] = datetime.now().isoformat()
        
        # Update schedule
        result = db.client.table('monitoring_schedules').update(update_data).eq('id', str(schedule_id)).execute()
        
        if not result.data:
            raise HTTPException(status_code=500, detail="Failed to update schedule")
        
        return MonitoringSchedule(**result.data[0])
        
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid schedule configuration: {str(e)}")
    except Exception as e:
        logger.error(f"Error updating schedule {schedule_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Error updating schedule: {str(e)}")


@router.post("/{schedule_id}/toggle", response_model=MonitoringSchedule)
async def toggle_schedule(
    schedule_id: UUID,
    enabled: bool = True,
    db: SupabaseService = Depends(get_db)
):
    """Enable or disable a schedule"""
    try:
        # Check if schedule exists
        existing = db.client.table('monitoring_schedules').select('id').eq('id', str(schedule_id)).single().execute()
        
        if not existing.data:
            raise HTTPException(status_code=404, detail="Schedule not found")
        
        # Update enabled status
        update_data = {
            'enabled': enabled,
            'updated_at': datetime.now().isoformat()
        }
        
        result = db.client.table('monitoring_schedules').update(update_data).eq('id', str(schedule_id)).execute()
        
        if not result.data:
            raise HTTPException(status_code=500, detail="Failed to update schedule")
        
        return MonitoringSchedule(**result.data[0])
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error toggling schedule {schedule_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Error toggling schedule: {str(e)}")


@router.delete("/{schedule_id}")
async def delete_schedule(
    schedule_id: UUID,
    db: SupabaseService = Depends(get_db)
):
    """Delete a schedule"""
    try:
        # Check if schedule exists
        existing = db.client.table('monitoring_schedules').select('id').eq('id', str(schedule_id)).single().execute()
        
        if not existing.data:
            raise HTTPException(status_code=404, detail="Schedule not found")
        
        # Delete schedule (history will be cascade deleted)
        db.client.table('monitoring_schedules').delete().eq('id', str(schedule_id)).execute()
        
        return {"message": "Schedule deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting schedule {schedule_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Error deleting schedule: {str(e)}")


@router.get("/{schedule_id}/history", response_model=List[ScheduleHistory])
async def get_schedule_history(
    schedule_id: UUID,
    limit: int = Query(default=50, ge=1, le=1000),
    offset: int = Query(default=0, ge=0),
    status: Optional[str] = None,
    db: SupabaseService = Depends(get_db)
):
    """Get execution history for a schedule"""
    try:
        query = db.client.table('monitoring_schedule_history').select('*').eq('schedule_id', str(schedule_id))
        
        if status:
            query = query.eq('status', status)
        
        query = query.order('started_at', desc=True).range(offset, offset + limit - 1)
        
        result = query.execute()
        
        return [ScheduleHistory(**h) for h in result.data]
        
    except Exception as e:
        logger.error(f"Error fetching schedule history: {e}")
        raise HTTPException(status_code=500, detail=f"Error fetching schedule history: {str(e)}")


@router.post("/{schedule_id}/run", response_model=Dict[str, Any])
async def run_schedule_now(
    schedule_id: UUID,
    db: SupabaseService = Depends(get_db)
):
    """Manually trigger a scheduled task"""
    try:
        # Get schedule
        result = db.client.table('monitoring_schedules').select('*').eq('id', str(schedule_id)).single().execute()
        
        if not result.data:
            raise HTTPException(status_code=404, detail="Schedule not found")
        
        schedule = MonitoringSchedule(**result.data)
        
        # Import task based on task type
        if schedule.task_type == TaskType.CATEGORY_MONITOR:
            from app.tasks.category_tasks import monitor_categories
            task = monitor_categories
        else:
            raise HTTPException(status_code=400, detail=f"Unsupported task type: {schedule.task_type}")
        
        # Run task asynchronously
        task_params = schedule.task_params.copy()
        task_params['schedule_id'] = str(schedule.id)
        
        result = task.apply_async(kwargs=task_params)
        
        return {
            "task_id": result.id,
            "status": "started",
            "message": f"Task {schedule.task_name} started successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error running schedule {schedule_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Error running schedule: {str(e)}")


@router.get("/stats/summary", response_model=Dict[str, Any])
async def get_schedule_stats(
    db: SupabaseService = Depends(get_db)
):
    """Get summary statistics for all schedules"""
    try:
        # Get all schedules
        schedules_result = db.client.table('monitoring_schedules').select('*').execute()
        schedules = schedules_result.data or []
        
        # Get recent history
        history_result = db.client.table('monitoring_schedule_history')\
            .select('*')\
            .gte('started_at', (datetime.now() - timedelta(days=7)).isoformat())\
            .execute()
        
        recent_history = history_result.data or []
        
        # Calculate stats
        stats = {
            "total_schedules": len(schedules),
            "enabled_schedules": sum(1 for s in schedules if s['enabled']),
            "disabled_schedules": sum(1 for s in schedules if not s['enabled']),
            "schedules_by_type": {},
            "recent_runs": {
                "total": len(recent_history),
                "successful": sum(1 for h in recent_history if h['status'] == 'success'),
                "failed": sum(1 for h in recent_history if h['status'] == 'failure'),
                "running": sum(1 for h in recent_history if h['status'] == 'running')
            },
            "average_duration_seconds": 0,
            "next_scheduled_runs": []
        }
        
        # Count by type
        for schedule in schedules:
            task_type = schedule['task_type']
            stats["schedules_by_type"][task_type] = stats["schedules_by_type"].get(task_type, 0) + 1
        
        # Calculate average duration
        completed_runs = [h for h in recent_history if h['status'] == 'success' and h.get('duration_seconds')]
        if completed_runs:
            stats["average_duration_seconds"] = sum(h['duration_seconds'] for h in completed_runs) / len(completed_runs)
        
        # Get next scheduled runs
        enabled_schedules = [s for s in schedules if s['enabled'] and s.get('next_run')]
        enabled_schedules.sort(key=lambda s: s['next_run'])
        stats["next_scheduled_runs"] = [
            {
                "task_name": s['task_name'],
                "task_type": s['task_type'],
                "next_run": s['next_run']
            }
            for s in enabled_schedules[:5]  # Next 5 runs
        ]
        
        return stats
        
    except Exception as e:
        logger.error(f"Error fetching schedule stats: {e}")
        raise HTTPException(status_code=500, detail=f"Error fetching schedule stats: {str(e)}")