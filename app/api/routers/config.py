"""
Configuration API endpoints
"""
from fastapi import APIRouter, HTTPException, Depends
import logging
import os

from app.api.models import ConfigResponse, ConfigUpdateRequest

logger = logging.getLogger(__name__)
router = APIRouter()

# In-memory config (in production, use database or config service)
config_store = {
    "scraping_enabled": True,
    "max_concurrent_jobs": 5,
    "default_max_pages": 10,
    "rate_limit_delay": 5
}


@router.get("", response_model=ConfigResponse)
async def get_config():
    """Get current configuration"""
    try:
        return ConfigResponse(
            scraping_enabled=config_store["scraping_enabled"],
            max_concurrent_jobs=config_store["max_concurrent_jobs"],
            default_max_pages=config_store["default_max_pages"],
            rate_limit_delay=config_store["rate_limit_delay"],
            environments=["development", "staging", "production"],
            current_environment=os.getenv("ENVIRONMENT", "development")
        )
        
    except Exception as e:
        logger.error(f"Get config error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get configuration")


@router.patch("", response_model=ConfigResponse)
async def update_config(
    request: ConfigUpdateRequest
):
    """Update configuration settings"""
    try:
        # Update only provided fields
        if request.scraping_enabled is not None:
            config_store["scraping_enabled"] = request.scraping_enabled
        if request.max_concurrent_jobs is not None:
            config_store["max_concurrent_jobs"] = request.max_concurrent_jobs
        if request.default_max_pages is not None:
            config_store["default_max_pages"] = request.default_max_pages
        if request.rate_limit_delay is not None:
            config_store["rate_limit_delay"] = request.rate_limit_delay
        
        return ConfigResponse(
            scraping_enabled=config_store["scraping_enabled"],
            max_concurrent_jobs=config_store["max_concurrent_jobs"],
            default_max_pages=config_store["default_max_pages"],
            rate_limit_delay=config_store["rate_limit_delay"],
            environments=["development", "staging", "production"],
            current_environment=os.getenv("ENVIRONMENT", "development")
        )
        
    except Exception as e:
        logger.error(f"Update config error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to update configuration")


@router.post("/reset")
async def reset_config():
    """Reset configuration to defaults"""
    try:
        config_store.update({
            "scraping_enabled": True,
            "max_concurrent_jobs": 5,
            "default_max_pages": 10,
            "rate_limit_delay": 5
        })
        
        return {"message": "Configuration reset to defaults"}
        
    except Exception as e:
        logger.error(f"Reset config error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to reset configuration")