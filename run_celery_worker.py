#!/usr/bin/env python3
"""
Run Celery Worker for processing monitoring tasks
"""
import os
import sys
import logging
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def main():
    """Start Celery Worker"""
    from app.config.celery_config import celery_app
    
    logger.info("Starting Celery Worker...")
    logger.info("This will process monitoring tasks from the queue")
    logger.info("Press Ctrl+C to stop")
    
    # Start worker
    celery_app.start([
        'celery',
        '-A', 'app.config.celery_config:celery_app',
        'worker',
        '--loglevel=info',
        '--concurrency=2',  # Number of concurrent workers
        '-Q', 'monitoring,default'  # Queues to process
    ])


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        logger.info("Celery Worker stopped by user")
    except Exception as e:
        logger.error(f"Error running Celery Worker: {e}")
        sys.exit(1)