#!/usr/bin/env python3
"""
Run the FastAPI server for the RIS Data Scrap project.

This script provides a convenient way to start the API server with
appropriate settings for development or production environments.
"""

import os
import sys
import uvicorn
import logging
from pathlib import Path

# Add project root to Python path
PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))

# Import and configure logging
from config.logging_config import configure_all_loggers

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Set up file logging
configure_all_loggers()

def main():
    """Run the FastAPI application."""
    # Environment settings
    environment = os.getenv("ENVIRONMENT", "development")
    port = int(os.getenv("PORT", 8001))  # Railway/Render use different defaults
    host = os.getenv("HOST", "0.0.0.0")
    
    # Uvicorn settings based on environment
    if environment == "development":
        # Development settings with auto-reload
        uvicorn.run(
            "src.api.main:app",
            host=host,
            port=port,
            reload=True,
            reload_dirs=[str(PROJECT_ROOT / "src")],
            log_level="info",
            access_log=True
        )
    else:
        # Production settings
        uvicorn.run(
            "src.api.main:app",
            host=host,
            port=port,
            workers=4,
            log_level="warning",
            access_log=True,
            loop="uvloop"  # Better performance on Linux/Mac
        )

if __name__ == "__main__":
    print(f"Starting RIS Data Scrap API...")
    print(f"Environment: {os.getenv('ENVIRONMENT', 'development')}")
    print(f"API will be available at: http://localhost:{os.getenv('PORT', 8001)}")
    print(f"Documentation at: http://localhost:{os.getenv('PORT', 8001)}/docs")
    print(f"Alternative docs at: http://localhost:{os.getenv('PORT', 8001)}/redoc")
    print("-" * 50)
    
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nShutting down API server...")
    except Exception as e:
        print(f"\nError starting server: {e}")
        sys.exit(1)