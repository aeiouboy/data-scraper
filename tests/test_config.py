"""Test configuration and settings."""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load test environment variables
TEST_ENV_PATH = Path(__file__).parent / ".env.test"
if TEST_ENV_PATH.exists():
    load_dotenv(TEST_ENV_PATH)


class TestConfig:
    """Test configuration settings."""
    
    # Database
    TEST_DATABASE_URL = os.getenv(
        "TEST_DATABASE_URL",
        "sqlite:///./test_ris_scraping.db"
    )
    
    # API Settings
    TEST_API_HOST = os.getenv("TEST_API_HOST", "localhost")
    TEST_API_PORT = int(os.getenv("TEST_API_PORT", "8001"))
    TEST_API_URL = f"http://{TEST_API_HOST}:{TEST_API_PORT}"
    
    # Frontend Settings
    TEST_FRONTEND_HOST = os.getenv("TEST_FRONTEND_HOST", "localhost")
    TEST_FRONTEND_PORT = int(os.getenv("TEST_FRONTEND_PORT", "3001"))
    TEST_FRONTEND_URL = f"http://{TEST_FRONTEND_HOST}:{TEST_FRONTEND_PORT}"
    
    # External Services (Mocked in tests)
    MOCK_FIRECRAWL = os.getenv("MOCK_FIRECRAWL", "true").lower() == "true"
    MOCK_SUPABASE = os.getenv("MOCK_SUPABASE", "true").lower() == "true"
    
    # Test Data
    TEST_DATA_DIR = Path(__file__).parent / "test_data"
    FIXTURES_DIR = Path(__file__).parent / "fixtures"
    
    # Performance Testing
    LOAD_TEST_USERS = int(os.getenv("LOAD_TEST_USERS", "10"))
    LOAD_TEST_DURATION = int(os.getenv("LOAD_TEST_DURATION", "60"))  # seconds
    
    # Coverage Settings
    MIN_COVERAGE_PERCENT = int(os.getenv("MIN_COVERAGE_PERCENT", "80"))
    
    # Timeouts
    DEFAULT_TIMEOUT = int(os.getenv("DEFAULT_TIMEOUT", "30"))  # seconds
    SCRAPING_TIMEOUT = int(os.getenv("SCRAPING_TIMEOUT", "300"))  # seconds
    
    # Retailers to test
    TEST_RETAILERS = [
        "homepro",
        "megahome",
        "thaiwatsadu",
        "boonthavorn"
    ]
    
    # Sample test URLs
    TEST_URLS = {
        "homepro": {
            "category": "https://www.homepro.co.th/c/tools",
            "product": "https://www.homepro.co.th/p/1234567"
        },
        "megahome": {
            "category": "https://www.megahome.co.th/category/tools",
            "product": "https://www.megahome.co.th/product/test-product"
        },
        "thaiwatsadu": {
            "category": "https://www.thaiwatsadu.com/th/category/tools",
            "product": "https://www.thaiwatsadu.com/th/product/12345"
        },
        "boonthavorn": {
            "category": "https://www.boonthavorn.com/th/category/tiles",
            "product": "https://www.boonthavorn.com/th/product/tile-001"
        }
    }
    
    @classmethod
    def get_test_database_url(cls, test_name: str = None) -> str:
        """Get database URL for a specific test."""
        if "sqlite" in cls.TEST_DATABASE_URL:
            # Use separate SQLite database for each test
            if test_name:
                return f"sqlite:///./test_{test_name}.db"
        return cls.TEST_DATABASE_URL
    
    @classmethod
    def get_retailer_config(cls, retailer: str) -> dict:
        """Get test configuration for a specific retailer."""
        return {
            "urls": cls.TEST_URLS.get(retailer, {}),
            "mock_enabled": cls.MOCK_FIRECRAWL,
            "timeout": cls.SCRAPING_TIMEOUT
        }


# Test markers configuration for pytest
MARKERS = {
    "unit": "Unit tests that test individual components",
    "integration": "Integration tests that test multiple components",
    "e2e": "End-to-end tests that test complete workflows",
    "slow": "Tests that take more than 5 seconds to run",
    "external": "Tests that require external services",
    "security": "Security-related tests",
    "performance": "Performance and load tests",
}


# Test categories for organizing test runs
TEST_CATEGORIES = {
    "quick": ["unit"],
    "standard": ["unit", "integration"],
    "full": ["unit", "integration", "e2e"],
    "external": ["external"],
    "security": ["security"],
    "performance": ["performance", "slow"]
}