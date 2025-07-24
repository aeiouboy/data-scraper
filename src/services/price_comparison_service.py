"""Mock price comparison service."""

from typing import Dict, Any, Optional


class PriceComparisonService:
    """Mock price comparison service."""
    
    async def compare_product_prices(self, product_id: int, session: Any) -> Optional[Dict[str, Any]]:
        """Compare product prices."""
        return {
            "retailers": ["homepro", "megahome"],
            "lowest_price": {"price": 1000.0, "retailer": "homepro"},
            "highest_price": {"price": 1200.0, "retailer": "megahome"},
            "price_difference": 200.0,
            "price_difference_percentage": 20.0,
            "price_trends": {
                "homepro": {"trend": "down", "change_amount": -100.0, "change_percentage": -9.0},
                "megahome": {"trend": "stable", "change_amount": 0.0, "change_percentage": 0.0}
            }
        }
