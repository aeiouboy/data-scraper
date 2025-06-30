"""
Monitoring API endpoints for scraping health
"""
from fastapi import APIRouter, HTTPException
from datetime import datetime, timedelta
from typing import List, Dict, Any
import logging

from app.services.supabase_service import SupabaseService
from app.api.models import (
    HealthMetricsResponse,
    RetailerHealthResponse,
    JobMetricsResponse
)
from app.config.retailers import retailer_manager

logger = logging.getLogger(__name__)

router = APIRouter(
    tags=["monitoring"]
)


@router.get("/health", response_model=HealthMetricsResponse)
async def get_health_metrics():
    """Get overall system health metrics"""
    try:
        db = SupabaseService()
        now = datetime.utcnow()
        last_24h = (now - timedelta(hours=24)).isoformat()
        last_7d = (now - timedelta(days=7)).isoformat()
        
        # Get job statistics for last 24 hours
        jobs_24h = db.client.table('scrape_jobs').select('*').gte('created_at', last_24h).execute()
        jobs_24h_data = jobs_24h.data if jobs_24h.data else []
        
        # Calculate 24h metrics
        total_24h = len(jobs_24h_data)
        successful_24h = sum(1 for job in jobs_24h_data if job.get('status') == 'completed')
        failed_24h = sum(1 for job in jobs_24h_data if job.get('status') == 'failed')
        durations = [job.get('duration_seconds', 0) for job in jobs_24h_data if job.get('duration_seconds')]
        avg_duration = sum(durations) / len(durations) if durations else 0.0
        
        # Get job statistics for last 7 days
        jobs_7d = db.client.table('scrape_jobs').select('id,status').gte('created_at', last_7d).execute()
        jobs_7d_data = jobs_7d.data if jobs_7d.data else []
        
        total_7d = len(jobs_7d_data)
        successful_7d = sum(1 for job in jobs_7d_data if job.get('status') == 'completed')
        
        # Get active and queued jobs
        active_result = db.client.table('scrape_jobs').select('id').eq('status', 'in_progress').execute()
        queue_result = db.client.table('scrape_jobs').select('id').eq('status', 'pending').execute()
        
        active_jobs = len(active_result.data) if active_result.data else 0
        queue_size = len(queue_result.data) if queue_result.data else 0
        
        # Calculate success rates
        success_rate_24h = (successful_24h / total_24h * 100) if total_24h > 0 else 0.0
        success_rate_7d = (successful_7d / total_7d * 100) if total_7d > 0 else 0.0
        
        # Determine overall health
        if success_rate_24h >= 95 and avg_duration < 10:
            overall_health = "healthy"
        elif success_rate_24h >= 85 or avg_duration < 20:
            overall_health = "warning"
        else:
            overall_health = "critical"
        
        return HealthMetricsResponse(
            overall_health=overall_health,
            success_rate_24h=success_rate_24h,
            success_rate_7d=success_rate_7d,
            avg_response_time=avg_duration,
            total_jobs_24h=total_24h,
            failed_jobs_24h=failed_24h,
            active_jobs=active_jobs,
            queue_size=queue_size,
            last_updated=now.isoformat()
        )
        
    except Exception as e:
        logger.error(f"Error getting health metrics: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get health metrics")


@router.get("/retailers", response_model=List[RetailerHealthResponse])
async def get_retailer_health():
    """Get health status for each retailer"""
    try:
        db = SupabaseService()
        now = datetime.utcnow()
        last_24h = (now - timedelta(hours=24)).isoformat()
        
        retailer_health = []
        
        for retailer in retailer_manager.get_all_retailers():
            # Get job statistics for this retailer
            jobs = db.client.table('scrape_jobs').select('*').eq('retailer_code', retailer.code).gte('created_at', last_24h).execute()
            jobs_data = jobs.data if jobs.data else []
            
            total = len(jobs_data)
            successful = sum(1 for job in jobs_data if job.get('status') == 'completed')
            failed = sum(1 for job in jobs_data if job.get('status') == 'failed')
            durations = [job.get('duration_seconds', 0) for job in jobs_data if job.get('duration_seconds')]
            avg_duration = sum(durations) / len(durations) if durations else 0.0
            
            # Get last successful job
            last_success_result = db.client.table('scrape_jobs').select('completed_at').eq('retailer_code', retailer.code).eq('status', 'completed').order('completed_at.desc').limit(1).execute()
            last_success = last_success_result.data[0]['completed_at'] if last_success_result.data else None
            
            # Get products scraped count
            products = db.client.table('products').select('id').eq('retailer_code', retailer.code).gte('created_at', last_24h).execute()
            products_count = len(products.data) if products.data else 0
            
            # Calculate success rate
            success_rate = (successful / total * 100) if total > 0 else 0.0
            
            # Determine retailer status
            if not last_success:
                status = "offline"
            elif success_rate >= 95:
                status = "healthy"
            elif success_rate >= 85:
                status = "warning"
            else:
                status = "critical"
            
            retailer_health.append(RetailerHealthResponse(
                retailer_code=retailer.code,
                retailer_name=retailer.name,
                status=status,
                success_rate=success_rate,
                avg_response_time=avg_duration,
                last_successful_scrape=last_success,
                error_count_24h=failed,
                products_scraped_24h=products_count
            ))
        
        return retailer_health
        
    except Exception as e:
        logger.error(f"Error getting retailer health: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get retailer health")


@router.get("/metrics", response_model=List[JobMetricsResponse])
async def get_job_metrics():
    """Get hourly job metrics for charts"""
    try:
        db = SupabaseService()
        now = datetime.utcnow()
        last_24h = (now - timedelta(hours=24)).isoformat()
        
        # Get all jobs from last 24 hours
        jobs = db.client.table('scrape_jobs').select('created_at,status,duration_seconds').gte('created_at', last_24h).execute()
        jobs_data = jobs.data if jobs.data else []
        
        # Group by hour
        hourly_metrics = {}
        for job in jobs_data:
            # Parse created_at and truncate to hour
            created_at = datetime.fromisoformat(job['created_at'].replace('Z', '+00:00'))
            hour_key = created_at.replace(minute=0, second=0, microsecond=0)
            hour_str = hour_key.strftime('%H:%M')
            
            if hour_str not in hourly_metrics:
                hourly_metrics[hour_str] = {
                    'successful': 0,
                    'failed': 0,
                    'durations': []
                }
            
            if job.get('status') == 'completed':
                hourly_metrics[hour_str]['successful'] += 1
            elif job.get('status') == 'failed':
                hourly_metrics[hour_str]['failed'] += 1
            
            if job.get('duration_seconds'):
                hourly_metrics[hour_str]['durations'].append(job['duration_seconds'])
        
        # Fill in missing hours and create response
        metrics = []
        current_hour = datetime.utcnow() - timedelta(hours=24)
        current_hour = current_hour.replace(minute=0, second=0, microsecond=0)
        
        while current_hour <= now:
            hour_str = current_hour.strftime('%H:%M')
            
            if hour_str in hourly_metrics:
                data = hourly_metrics[hour_str]
                avg_duration = sum(data['durations']) / len(data['durations']) if data['durations'] else 0.0
                
                metrics.append(JobMetricsResponse(
                    hour=hour_str,
                    successful=data['successful'],
                    failed=data['failed'],
                    avg_duration=avg_duration
                ))
            else:
                metrics.append(JobMetricsResponse(
                    hour=hour_str,
                    successful=0,
                    failed=0,
                    avg_duration=0.0
                ))
            
            current_hour += timedelta(hours=1)
        
        return metrics
        
    except Exception as e:
        logger.error(f"Error getting job metrics: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get job metrics")


@router.get("/alerts")
async def get_active_alerts():
    """Get active system alerts"""
    try:
        db = SupabaseService()
        alerts = []
        now = datetime.utcnow()
        last_hour = (now - timedelta(hours=1)).isoformat()
        
        # Check for high failure rate
        recent_jobs = db.client.table('scrape_jobs').select('status').gte('created_at', last_hour).execute()
        recent_jobs_data = recent_jobs.data if recent_jobs.data else []
        
        total = len(recent_jobs_data)
        failed = sum(1 for job in recent_jobs_data if job.get('status') == 'failed')
        
        if total > 10 and failed / total > 0.2:
            alerts.append({
                "level": "warning",
                "message": f"High failure rate detected: {(failed / total * 100):.1f}% in the last hour",
                "timestamp": now.isoformat()
            })
        
        # Check for stuck jobs
        thirty_min_ago = (now - timedelta(minutes=30)).isoformat()
        stuck_result = db.client.table('scrape_jobs').select('id').eq('status', 'in_progress').lt('started_at', thirty_min_ago).execute()
        stuck_jobs = len(stuck_result.data) if stuck_result.data else 0
        
        if stuck_jobs > 0:
            alerts.append({
                "level": "error",
                "message": f"{stuck_jobs} jobs appear to be stuck (running for over 30 minutes)",
                "timestamp": now.isoformat()
            })
        
        # Check for offline retailers
        six_hours_ago = (now - timedelta(hours=6)).isoformat()
        
        for retailer in retailer_manager.get_all_retailers():
            last_success_result = db.client.table('scrape_jobs').select('completed_at').eq('retailer_code', retailer.code).eq('status', 'completed').order('completed_at.desc').limit(1).execute()
            
            if not last_success_result.data or last_success_result.data[0]['completed_at'] < six_hours_ago:
                alerts.append({
                    "level": "warning",
                    "message": f"{retailer.name} hasn't had a successful scrape in over 6 hours",
                    "timestamp": now.isoformat()
                })
        
        return alerts
        
    except Exception as e:
        logger.error(f"Error getting alerts: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get alerts")