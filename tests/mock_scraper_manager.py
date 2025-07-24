"""Mock scraper manager for testing."""

from typing import List, Optional
from src.models.product import Product


class ScraperManager:
    """Mock scraper manager."""
    
    async def scrape_product(self, url: str) -> Optional[dict]:
        """Mock scrape product."""
        return {
            "retailer_code": "homepro",
            "sku": "TEST123",
            "name": "Test Product",
            "current_price": 1000.0,
            "product_url": url
        }
    
    async def scrape_retailer(self, retailer: str, category: Optional[str] = None) -> List[dict]:
        """Mock scrape retailer."""
        return [
            {
                "retailer_code": retailer,
                "sku": f"TEST{i}",
                "name": f"Test Product {i}",
                "current_price": 1000.0 * (i + 1),
                "product_url": f"https://{retailer}.com/p/{i}"
            }
            for i in range(3)
        ]
    
    async def scrape_category(self, url: str, max_pages: int = 10) -> List[dict]:
        """Mock scrape category."""
        return await self.scrape_retailer("test", "category")
    
    def get_scraper(self, retailer: str):
        """Get mock scraper."""
        from unittest.mock import AsyncMock
        mock = AsyncMock()
        mock.scrape_category.return_value = []
        mock.scrape_product.return_value = {}
        return mock
