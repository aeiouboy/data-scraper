"""
Centralized logging configuration for the project
"""
import logging
import logging.handlers
import os
from pathlib import Path

# Create logs directory if it doesn't exist
LOGS_DIR = Path(__file__).parent / "logs"
LOGS_DIR.mkdir(exist_ok=True)

def setup_file_logging(logger_name: str, log_file: str, level=logging.INFO):
    """
    Set up file logging for a specific logger
    
    Args:
        logger_name: Name of the logger
        log_file: Name of the log file (will be created in logs/ directory)
        level: Logging level
    """
    logger = logging.getLogger(logger_name)
    logger.setLevel(level)
    
    # Create file handler
    file_handler = logging.handlers.RotatingFileHandler(
        LOGS_DIR / log_file,
        maxBytes=10 * 1024 * 1024,  # 10MB
        backupCount=5
    )
    
    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    file_handler.setFormatter(formatter)
    
    # Add handler to logger
    logger.addHandler(file_handler)
    
    return logger

# Configure default loggers
def configure_all_loggers():
    """Configure all application loggers to use the logs directory"""
    # API logger
    setup_file_logging("uvicorn", "api.log")
    setup_file_logging("uvicorn.access", "api_access.log", logging.WARNING)
    setup_file_logging("uvicorn.error", "api_error.log")
    
    # Application loggers
    setup_file_logging("app", "app.log")
    setup_file_logging("app.api", "app_api.log")
    setup_file_logging("app.scrapers", "scrapers.log")
    setup_file_logging("app.services", "services.log")
    
    # HTTP client loggers (reduce noise)
    setup_file_logging("httpx", "http.log", logging.WARNING)
    setup_file_logging("httpcore", "http.log", logging.WARNING)