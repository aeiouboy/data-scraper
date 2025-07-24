"""
Proxy environment variable manager for Railway deployment
"""
import os
import logging
from typing import Dict, Optional, List
from contextlib import contextmanager

logger = logging.getLogger(__name__)


class ProxyManager:
    """Manages proxy environment variables to prevent client initialization errors"""
    
    PROXY_VARS = [
        'HTTP_PROXY', 'HTTPS_PROXY', 'FTP_PROXY', 'SOCKS_PROXY',
        'http_proxy', 'https_proxy', 'ftp_proxy', 'socks_proxy',
        'ALL_PROXY', 'all_proxy', 'NO_PROXY', 'no_proxy'
    ]
    
    @classmethod
    def clear_all_proxy_vars(cls) -> Dict[str, str]:
        """Clear all proxy environment variables and return original values"""
        original_values = {}
        cleared_vars = []
        
        for var in cls.PROXY_VARS:
            if var in os.environ:
                original_values[var] = os.environ[var]
                del os.environ[var]
                cleared_vars.append(f"{var}={original_values[var]}")
        
        if cleared_vars:
            logger.info(f"🔧 Cleared proxy variables: {', '.join(cleared_vars)}")
        
        return original_values
    
    @classmethod
    def restore_proxy_vars(cls, original_values: Dict[str, str]) -> None:
        """Restore proxy environment variables"""
        for var, value in original_values.items():
            os.environ[var] = value
        
        if original_values:
            logger.info(f"🔧 Restored proxy variables: {', '.join(original_values.keys())}")
    
    @classmethod
    @contextmanager
    def without_proxy(cls):
        """Context manager that temporarily clears proxy variables"""
        original_values = cls.clear_all_proxy_vars()
        try:
            yield
        finally:
            cls.restore_proxy_vars(original_values)


# Global proxy clearing on module import for Railway
if os.getenv('RAILWAY_ENVIRONMENT') or os.getenv('ENVIRONMENT') == 'production':
    logger.info("🚂 Railway environment detected - clearing proxy variables globally")
    ProxyManager.clear_all_proxy_vars()