"""Test utilities and helper functions."""

import asyncio
import json
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
from unittest.mock import Mock, AsyncMock

import httpx
from bs4 import BeautifulSoup
from sqlalchemy.orm import Session

from src.models.product import Product
from tests.models_mock import ScrapingJob
from tests.factories import ProductFactory, ScrapingJobFactory


class TestDataLoader:
    """Load test data from files."""
    
    def __init__(self, data_dir: Path = None):
        self.data_dir = data_dir or Path(__file__).parent / "test_data"
    
    def load_html(self, filename: str) -> str:
        """Load HTML test data."""
        filepath = self.data_dir / "html" / filename
        if filepath.exists():
            return filepath.read_text(encoding="utf-8")
        return ""
    
    def load_json(self, filename: str) -> Dict[str, Any]:
        """Load JSON test data."""
        filepath = self.data_dir / "json" / filename
        if filepath.exists():
            return json.loads(filepath.read_text())
        return {}
    
    def load_product_samples(self, retailer: str) -> List[Dict[str, Any]]:
        """Load sample products for a retailer."""
        return self.load_json(f"{retailer}_products.json")


class MockHTTPClient:
    """Mock HTTP client for testing."""
    
    def __init__(self):
        self.responses = {}
        self.call_history = []
    
    def set_response(self, url: str, response: Union[str, dict], status_code: int = 200):
        """Set a mock response for a URL."""
        self.responses[url] = {
            "content": response,
            "status_code": status_code
        }
    
    async def get(self, url: str, **kwargs) -> Mock:
        """Mock GET request."""
        self.call_history.append(("GET", url, kwargs))
        
        if url in self.responses:
            resp_data = self.responses[url]
            response = Mock()
            response.status_code = resp_data["status_code"]
            
            if isinstance(resp_data["content"], str):
                response.text = resp_data["content"]
                response.content = resp_data["content"].encode()
            else:
                response.json = lambda: resp_data["content"]
                response.text = json.dumps(resp_data["content"])
            
            return response
        
        # Default 404 response
        response = Mock()
        response.status_code = 404
        response.text = "Not Found"
        return response
    
    async def post(self, url: str, **kwargs) -> Mock:
        """Mock POST request."""
        self.call_history.append(("POST", url, kwargs))
        return await self.get(url)  # Simple implementation


class DatabaseTestHelper:
    """Helper for database operations in tests."""
    
    @staticmethod
    def create_test_products(session: Session, count: int = 10) -> List[Product]:
        """Create test products in database."""
        products = ProductFactory.create_batch(count)
        session.add_all(products)
        session.commit()
        return products
    
    @staticmethod
    def create_matched_products(session: Session, retailers: List[str] = None) -> List[Product]:
        """Create products that should match across retailers."""
        if not retailers:
            retailers = ["homepro", "megahome"]
        
        base_product = ProductFactory.create(retailer_code=retailers[0])
        session.add(base_product)
        
        matched_products = [base_product]
        
        for retailer in retailers[1:]:
            # Create similar product
            matched = ProductFactory.create(
                retailer_code=retailer,
                name=base_product.name.replace("Test", "テスト"),  # Slight variation
                brand=base_product.brand,
                current_price=base_product.current_price * 1.05  # 5% price difference
            )
            session.add(matched)
            matched_products.append(matched)
        
        session.commit()
        return matched_products
    
    @staticmethod
    def create_price_history(
        session: Session,
        product: Product,
        days: int = 30,
        price_pattern: str = "stable"
    ) -> None:
        """Create price history for a product."""
        # TODO: Fix import - from src.api.models import PriceHistory
        
        base_price = product.current_price
        
        for day in range(days):
            if price_pattern == "increasing":
                price = base_price * (1 + (day * 0.01))  # 1% daily increase
            elif price_pattern == "decreasing":
                price = base_price * (1 - (day * 0.01))  # 1% daily decrease
            elif price_pattern == "volatile":
                # Random walk
                import random
                price = base_price * (1 + random.uniform(-0.05, 0.05))
            else:  # stable
                price = base_price
            
            history = PriceHistory(
                product_id=product.id,
                price=price,
                original_price=product.original_price,
                recorded_at=datetime.utcnow() - timedelta(days=day)
            )
            session.add(history)
        
        session.commit()


class AsyncTestHelper:
    """Helper for async testing."""
    
    @staticmethod
    def run_async(coro):
        """Run an async coroutine in a test."""
        loop = asyncio.get_event_loop()
        return loop.run_until_complete(coro)
    
    @staticmethod
    async def wait_for_condition(
        condition_fn,
        timeout: float = 10.0,
        interval: float = 0.1
    ) -> bool:
        """Wait for a condition to become true."""
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            if await condition_fn():
                return True
            await asyncio.sleep(interval)
        
        return False
    
    @staticmethod
    def create_async_mock(return_value=None, side_effect=None):
        """Create an async mock function."""
        mock = AsyncMock()
        if return_value is not None:
            mock.return_value = return_value
        if side_effect is not None:
            mock.side_effect = side_effect
        return mock


class PerformanceTestHelper:
    """Helper for performance testing."""
    
    def __init__(self):
        self.timings = {}
    
    def start_timer(self, name: str):
        """Start a named timer."""
        self.timings[name] = {"start": time.time()}
    
    def stop_timer(self, name: str):
        """Stop a named timer."""
        if name in self.timings:
            self.timings[name]["end"] = time.time()
            self.timings[name]["duration"] = (
                self.timings[name]["end"] - self.timings[name]["start"]
            )
    
    def get_timing(self, name: str) -> float:
        """Get duration for a named timer."""
        if name in self.timings and "duration" in self.timings[name]:
            return self.timings[name]["duration"]
        return 0.0
    
    def assert_performance(self, name: str, max_duration: float):
        """Assert that operation completed within time limit."""
        duration = self.get_timing(name)
        assert duration > 0, f"Timer '{name}' was not run"
        assert duration <= max_duration, (
            f"Operation '{name}' took {duration:.2f}s, "
            f"exceeding limit of {max_duration}s"
        )


class ScraperTestHelper:
    """Helper for testing scrapers."""
    
    @staticmethod
    def create_mock_page(html_content: str) -> BeautifulSoup:
        """Create a BeautifulSoup object from HTML."""
        return BeautifulSoup(html_content, 'html.parser')
    
    @staticmethod
    def generate_product_html(
        name: str = "Test Product",
        price: str = "฿1,999",
        sku: str = "SKU123",
        brand: str = "TestBrand"
    ) -> str:
        """Generate sample product HTML."""
        return f"""
        <div class="product">
            <h1>{name}</h1>
            <div class="sku">{sku}</div>
            <div class="brand">{brand}</div>
            <div class="price">{price}</div>
        </div>
        """
    
    @staticmethod
    def generate_category_html(product_count: int = 10) -> str:
        """Generate sample category page HTML."""
        products_html = []
        for i in range(product_count):
            products_html.append(f"""
            <div class="product-item">
                <a href="/product/{i}">Product {i}</a>
                <span class="price">฿{1000 + i * 100}</span>
            </div>
            """)
        
        return f"""
        <div class="category-page">
            <div class="products">
                {''.join(products_html)}
            </div>
            <a href="?page=2" class="next-page">Next</a>
        </div>
        """


# Fixtures data for quick access
TEST_FIXTURES = {
    "products": {
        "bosch_drill": {
            "name": "Bosch Professional Drill GBM 13 RE",
            "brand": "Bosch",
            "sku": "GBM13RE",
            "price": 2990.0,
            "category": "Power Tools/Drills"
        },
        "makita_drill": {
            "name": "Makita Cordless Drill DF457D",
            "brand": "Makita",
            "sku": "DF457D",
            "price": 4500.0,
            "category": "Power Tools/Drills"
        }
    },
    "retailers": {
        "homepro": {
            "base_url": "https://www.homepro.co.th",
            "name": "HomePro"
        },
        "megahome": {
            "base_url": "https://www.megahome.co.th",
            "name": "MegaHome"
        }
    }
}