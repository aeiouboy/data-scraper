"""
Secure configuration management for HomePro Scraper
"""
import os
from typing import Optional
from pydantic import BaseSettings, validator


class Settings(BaseSettings):
    """Application settings with validation"""
    
    # Supabase
    supabase_url: str
    supabase_anon_key: str
    supabase_service_role_key: str
    
    # Database
    postgres_url: str
    postgres_password: str
    
    # Firecrawl
    firecrawl_api_key: str
    
    # Application
    environment: str = "development"
    log_level: str = "info"
    
    @validator("supabase_url")
    def validate_supabase_url(cls, v):
        if not v.startswith("https://") or not v.endswith(".supabase.co"):
            raise ValueError("Invalid Supabase URL format")
        return v
    
    @validator("firecrawl_api_key")
    def validate_firecrawl_key(cls, v):
        if v.startswith("fc-"):
            return v
        raise ValueError("Invalid Firecrawl API key format")
    
    class Config:
        env_file = ".env"
        case_sensitive = False


def get_settings() -> Settings:
    """Get validated settings instance"""
    return Settings()


# Usage example
if __name__ == "__main__":
    try:
        settings = get_settings()
        print(f"Environment: {settings.environment}")
        print("✅ Configuration loaded successfully")
    except Exception as e:
        print(f"❌ Configuration error: {e}")
        print("Please check your .env file")