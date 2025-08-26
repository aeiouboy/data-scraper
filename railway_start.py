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

# CRITICAL: Clear proxy variables BEFORE any imports that might create HTTP clients
from src.utils.proxy_manager import ProxyManager
ProxyManager.clear_all_proxy_vars()

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
        logger.info("🔧 Starting Railway deployment process...")
        
        # Ensure proxy variables are cleared (redundant safety check)
        ProxyManager.clear_all_proxy_vars()
        
        logger.info("📦 Importing uvicorn...")
        import uvicorn
        logger.info("✅ uvicorn imported successfully")
        
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
        
        # Import the FastAPI app to check for import errors
        logger.info("📦 Importing FastAPI app...")
        try:
            from src.api.main import app
            logger.info("✅ FastAPI app imported successfully")
        except Exception as import_error:
            logger.error(f"❌ Failed to import FastAPI app: {import_error}")
            import traceback
            traceback.print_exc()
            raise
        
        # Railway production settings
        logger.info("🚀 Starting uvicorn server...")
        logger.info(f"📋 Configuration summary:")
        logger.info(f"   - Host: {host}")
        logger.info(f"   - Port: {port}")
        logger.info(f"   - Workers: 1")
        logger.info(f"   - Environment: {environment}")
        
        uvicorn.run(
            "src.api.main:app",
            host=host,
            port=port,
            log_level="info",
            access_log=True,
            reload=False,  # No reload in production
            workers=1,     # Single worker for Railway free tier
            timeout_keep_alive=30
        )
        
    except Exception as e:
        logger.error(f"❌ Failed to start API server: {str(e)}")
        logger.error("📍 FULL ERROR TRACEBACK:")
        import traceback
        traceback.print_exc()
        logger.error("📍 END TRACEBACK")
        
        # Additional error analysis
        if 'proxy' in str(e).lower():
            logger.error("🔍 PROXY ERROR DETECTED!")
            logger.error(f"📊 Error type: {type(e).__name__}")
            logger.error(f"📊 Error args: {getattr(e, 'args', 'No args')}")
            
        sys.exit(1)

if __name__ == "__main__":
    main()