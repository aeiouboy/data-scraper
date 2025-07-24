#!/usr/bin/env python3
"""
Railway-specific startup script for the RIS Data Scrap API
"""
import os
import sys
import logging
from pathlib import Path

# Add project root to Python path
PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))

# Configure logging for Railway
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)

logger = logging.getLogger(__name__)

def main():
    """Start the FastAPI application for Railway deployment"""
    try:
        import uvicorn
        
        # Railway-specific environment settings
        environment = os.getenv("ENVIRONMENT", "production")
        port = int(os.getenv("PORT", 8000))  # Railway uses PORT env var
        host = "0.0.0.0"  # Must bind to all interfaces for Railway
        
        logger.info("=" * 50)
        logger.info("🚀 Starting RIS Data Scrap API for Railway")
        logger.info(f"📊 Environment: {environment}")
        logger.info(f"🌐 Host: {host}")
        logger.info(f"🔌 Port: {port}")
        logger.info(f"🌍 API will be available at: http://{host}:{port}")
        logger.info("=" * 50)
        
        # Railway production settings
        uvicorn.run(
            "src.api.main:app",
            host=host,
            port=port,
            log_level="info",
            access_log=True,
            reload=False,  # No reload in production
            workers=1,     # Single worker for Railway free tier
            timeout_keep_alive=30,
            timeout_graceful_shutdown=30
        )
        
    except Exception as e:
        logger.error(f"❌ Failed to start API server: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()