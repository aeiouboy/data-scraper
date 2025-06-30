"""
Scraping API endpoints
"""
from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from typing import Optional, List
import logging
import asyncio

from app.api.models import (
    ScrapeJobRequest,
    ScrapeJobResponse,
    ScrapeJobListResponse
)
from app.services.supabase_service import SupabaseService
from app.scrapers.homepro_scraper import HomeProScraper

logger = logging.getLogger(__name__)
router = APIRouter()

def get_supabase() -> SupabaseService:
    """Dependency to get Supabase service"""
    return SupabaseService()


async def update_job_in_db(job_id: str, updates: dict):
    """Update job in database"""
    supabase = get_supabase()
    await supabase.update_scrape_job(job_id, updates)

async def run_scraping_job(job_id: str, job_type: str, target_url: str, urls: List[str] = None, max_pages: int = 5, retailer_code: str = None):
    """Background task to run scraping job"""
    from datetime import datetime
    from app.scrapers import get_scraper_for_retailer
    
    try:
        # Update job status to running
        await update_job_in_db(job_id, {
            'status': 'running',
            'started_at': datetime.now().isoformat()
        })
        
        # Initialize appropriate scraper based on retailer
        if retailer_code:
            scraper = get_scraper_for_retailer(retailer_code)
        else:
            # Default to HomePro for backward compatibility
            scraper = HomeProScraper()
            
        total_items = 0
        success_items = 0
        failed_items = 0
        
        if job_type == 'category':
            # Real category scraping
            logger.info(f"Starting category scraping for {target_url}")
            result = await scraper.scrape_category(target_url, max_pages=max_pages)
            
            total_items = result.get('discovered', 0)
            success_items = result.get('success', 0)
            failed_items = result.get('failed', 0)
            
            logger.info(f"Category scraping completed: {success_items}/{total_items} successful")
            
        elif job_type == 'product' and urls:
            # Real product scraping
            logger.info(f"Starting product scraping for {len(urls)} URLs")
            result = await scraper.scrape_batch(urls)
            
            total_items = result.get('total', len(urls))
            success_items = result.get('success', 0)
            failed_items = result.get('failed', 0)
            
            logger.info(f"Product scraping completed: {success_items}/{total_items} successful")
            
        else:
            raise ValueError('Invalid job type or missing parameters')
        
        # Update job as completed
        await update_job_in_db(job_id, {
            'status': 'completed',
            'total_items': total_items,
            'processed_items': total_items,
            'success_items': success_items,
            'failed_items': failed_items,
            'completed_at': datetime.now().isoformat()
        })
        
        logger.info(f"Scraping job {job_id} completed successfully")
        
    except Exception as e:
        logger.error(f"Scraping job {job_id} failed: {str(e)}")
        await update_job_in_db(job_id, {
            'status': 'failed',
            'error_message': str(e),
            'completed_at': datetime.now().isoformat()
        })


@router.post("/jobs", response_model=ScrapeJobResponse)
async def create_scrape_job(
    request: ScrapeJobRequest,
    background_tasks: BackgroundTasks,
    supabase: SupabaseService = Depends(get_supabase)
):
    """
    Create a new scraping job
    
    Job types:
    - product: Scrape specific product(s)
    - category: Discover and scrape all products in a category
    - search: Scrape products from search results
    """
    try:
        # Validate request
        if request.job_type == 'product' and not request.urls:
            raise HTTPException(status_code=400, detail="URLs required for product scraping")
        if request.job_type in ['category', 'search'] and not request.target_url:
            raise HTTPException(status_code=400, detail="Target URL required for category/search scraping")
        
        # Validate URL format
        if request.target_url and not request.target_url.startswith('http'):
            raise HTTPException(status_code=400, detail="Invalid URL format. Must start with http:// or https://")
        
        # Create job record in database
        job = await supabase.create_scrape_job(
            job_type=request.job_type,
            target_url=request.target_url or (request.urls[0] if request.urls else None)
        )
        
        if not job:
            raise HTTPException(status_code=500, detail="Failed to create job in database")
        
        # Start background task
        background_tasks.add_task(
            run_scraping_job,
            job['id'],
            request.job_type,
            request.target_url,
            request.urls,
            request.max_pages or 5,
            request.retailer_code
        )
        
        return ScrapeJobResponse(
            id=job['id'],
            job_type=job['job_type'],
            status=job['status'],
            target_url=job.get('target_url'),
            total_items=job.get('total_items'),
            processed_items=job.get('processed_items'),
            success_items=job.get('success_items'),
            failed_items=job.get('failed_items'),
            error_message=job.get('error_message'),
            created_at=job['created_at'],
            started_at=job.get('started_at'),
            completed_at=job.get('completed_at')
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Create job error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to create job")


@router.get("/jobs", response_model=ScrapeJobListResponse)
async def list_scrape_jobs(
    status: Optional[str] = None,
    limit: int = 20,
    supabase: SupabaseService = Depends(get_supabase)
):
    """List scraping jobs with optional status filter"""
    try:
        # Get jobs from database
        jobs = await supabase.get_scrape_jobs(status=status, limit=limit)
        
        # Convert to response models
        job_responses = [
            ScrapeJobResponse(
                id=job['id'],
                job_type=job['job_type'],
                status=job['status'],
                target_url=job.get('target_url'),
                total_items=job.get('total_items', 0),
                processed_items=job.get('processed_items', 0),
                success_items=job.get('success_items', 0),
                failed_items=job.get('failed_items', 0),
                error_message=job.get('error_message'),
                created_at=job['created_at'],
                started_at=job.get('started_at'),
                completed_at=job.get('completed_at')
            )
            for job in jobs
        ]
        
        # Get counts by status (separate queries for efficiency)
        all_jobs = await supabase.get_scrape_jobs(limit=1000)  # Get more for counting
        active_jobs = sum(1 for job in all_jobs if job['status'] in ['pending', 'running'])
        completed_jobs = sum(1 for job in all_jobs if job['status'] == 'completed')
        failed_jobs = sum(1 for job in all_jobs if job['status'] == 'failed')
        
        return ScrapeJobListResponse(
            jobs=job_responses,
            total=len(jobs),
            active_jobs=active_jobs,
            completed_jobs=completed_jobs,
            failed_jobs=failed_jobs
        )
        
    except Exception as e:
        logger.error(f"List jobs error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to list jobs")


@router.get("/jobs/{job_id}", response_model=ScrapeJobResponse)
async def get_scrape_job(
    job_id: str,
    supabase: SupabaseService = Depends(get_supabase)
):
    """Get scraping job by ID"""
    try:
        job = await supabase.get_scrape_job(job_id)
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")
        
        return ScrapeJobResponse(
            id=job['id'],
            job_type=job['job_type'],
            status=job['status'],
            target_url=job.get('target_url'),
            total_items=job.get('total_items'),
            processed_items=job.get('processed_items'),
            success_items=job.get('success_items'),
            failed_items=job.get('failed_items'),
            error_message=job.get('error_message'),
            created_at=job['created_at'],
            started_at=job.get('started_at'),
            completed_at=job.get('completed_at')
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get job error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get job")


@router.post("/jobs/{job_id}/cancel")
async def cancel_scrape_job(
    job_id: str,
    supabase: SupabaseService = Depends(get_supabase)
):
    """Cancel a running scraping job"""
    try:
        job = await supabase.get_scrape_job(job_id)
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")
        
        if job['status'] not in ['pending', 'running']:
            raise HTTPException(status_code=400, detail=f"Cannot cancel job with status: {job['status']}")
        
        # Update job status (use 'failed' instead of 'cancelled' due to DB constraint)
        await supabase.update_scrape_job(job_id, {
            'status': 'failed',
            'error_message': 'Cancelled by user'
        })
        
        return {"message": "Job cancelled", "job_id": job_id}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Cancel job error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to cancel job")


@router.post("/discover")
async def discover_urls(
    url: str,
    max_pages: int = 5,
    supabase: SupabaseService = Depends(get_supabase)
):
    """Discover product URLs from a category or search page"""
    try:
        discovery = URLDiscovery()
        try:
            urls = await discovery.discover_from_category(url, max_pages)
            
            return {
                "url": url,
                "max_pages": max_pages,
                "discovered_urls": urls,
                "total": len(urls)
            }
        finally:
            await discovery.close()
            
    except Exception as e:
        logger.error(f"URL discovery error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to discover URLs")