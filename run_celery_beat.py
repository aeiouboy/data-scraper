#!/usr/bin/env python3
"""
Run Celery Beat scheduler for automated monitoring
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
    """Start Celery Beat scheduler"""
    from app.config.celery_config import celery_app
    
    logger.info("Starting Celery Beat scheduler...")
    logger.info("This will run scheduled monitoring tasks based on database configuration")
    logger.info("Press Ctrl+C to stop")
    
    # Start beat
    celery_app.start([
        'celery',
        '-A', 'app.config.celery_config:celery_app',
        'beat',
        '--loglevel=info'
    ])


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        logger.info("Celery Beat stopped by user")
    except Exception as e:
        logger.error(f"Error running Celery Beat: {e}")
        sys.exit(1)