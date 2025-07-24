"""Factory for generating test scraping jobs."""

import random
from datetime import datetime, timedelta
from typing import Optional
from tests.models_mock import ScrapingJob


class ScrapingJobFactory:
    """Generate test scraping jobs."""
    
    RETAILERS = ['homepro', 'megahome', 'thaiwatsadu', 'boonthavorn']
    JOB_TYPES = ['full', 'category', 'product', 'update']
    STATUSES = ['pending', 'running', 'completed', 'failed', 'cancelled']
    
    @classmethod
    def create(
        cls,
        retailer_code: Optional[str] = None,
        job_type: Optional[str] = None,
        status: Optional[str] = None,
        **kwargs
    ) -> ScrapingJob:
        """Create a single scraping job."""
        
        retailer_code = retailer_code or random.choice(cls.RETAILERS)
        job_type = job_type or random.choice(cls.JOB_TYPES)
        status = status or random.choice(cls.STATUSES)
        
        # Generate timing based on status
        now = datetime.utcnow()
        
        if status == 'pending':
            started_at = None
            completed_at = None
            duration = None
        elif status == 'running':
            started_at = now - timedelta(minutes=random.randint(1, 30))
            completed_at = None
            duration = None
        else:  # completed, failed, cancelled
            duration_minutes = random.randint(5, 120)
            started_at = now - timedelta(minutes=duration_minutes + random.randint(0, 60))
            completed_at = started_at + timedelta(minutes=duration_minutes)
            duration = duration_minutes * 60  # in seconds
        
        # Generate product counts based on job type and status
        if status in ['pending', 'running']:
            total_products = 0
            successful_products = 0
            failed_products = 0
        else:
            if job_type == 'full':
                total_products = random.randint(1000, 5000)
            elif job_type == 'category':
                total_products = random.randint(50, 500)
            elif job_type == 'product':
                total_products = random.randint(1, 10)
            else:  # update
                total_products = random.randint(100, 1000)
            
            if status == 'completed':
                failed_rate = random.uniform(0, 0.05)  # 0-5% failure rate
            elif status == 'failed':
                failed_rate = random.uniform(0.5, 1.0)  # 50-100% failure rate
            else:  # cancelled
                failed_rate = 0
            
            failed_products = int(total_products * failed_rate)
            successful_products = total_products - failed_products
        
        # Generate metadata
        metadata = {}
        
        if job_type == 'category':
            metadata['category'] = random.choice(['power-tools', 'hand-tools', 'paint', 'tiles', 'bathroom'])
            metadata['page_count'] = random.randint(1, 20)
        
        if status == 'failed':
            metadata['error'] = random.choice([
                'Connection timeout',
                'Rate limit exceeded',
                'Invalid response format',
                'Authentication failed'
            ])
        
        job_data = {
            'retailer_code': retailer_code,
            'job_type': job_type,
            'status': status,
            'started_at': started_at,
            'completed_at': completed_at,
            'total_products': total_products,
            'successful_products': successful_products,
            'failed_products': failed_products,
            'metadata': metadata
        }
        
        # Override with any provided kwargs
        job_data.update(kwargs)
        
        return ScrapingJob(**job_data)
    
    @classmethod
    def create_batch(
        cls,
        count: int,
        **kwargs
    ) -> list[ScrapingJob]:
        """Create multiple scraping jobs."""
        return [cls.create(**kwargs) for _ in range(count)]
    
    @classmethod
    def create_job_sequence(
        cls,
        retailer_code: str,
        job_count: int = 5
    ) -> list[ScrapingJob]:
        """Create a realistic sequence of jobs for a retailer."""
        
        jobs = []
        base_time = datetime.utcnow() - timedelta(days=7)
        
        for i in range(job_count):
            # Jobs get progressively newer
            time_offset = timedelta(days=i * 1.5)
            
            # Mix of job types
            if i == 0:
                job_type = 'full'  # Start with full scrape
            else:
                job_type = random.choice(['category', 'update', 'product'])
            
            # Most jobs succeed
            status = 'completed' if random.random() > 0.1 else 'failed'
            
            job = cls.create(
                retailer_code=retailer_code,
                job_type=job_type,
                status=status,
                started_at=base_time + time_offset
            )
            
            jobs.append(job)
        
        return jobs