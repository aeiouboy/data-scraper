"""Mock models for testing when actual models don't exist."""

from datetime import datetime
from typing import Optional, Dict, Any, List
from pydantic import BaseModel


class ScrapingJob(BaseModel):
    """Mock ScrapingJob model for testing."""
    id: Optional[int] = None
    retailer_code: str
    job_type: str = "full"
    status: str = "pending"
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    total_products: int = 0
    successful_products: int = 0
    failed_products: int = 0
    metadata: Dict[str, Any] = {}


class ProductMatch(BaseModel):
    """Mock ProductMatch model for testing."""
    id: Optional[int] = None
    product1_id: int
    product2_id: int
    confidence_score: float
    match_type: str = "automatic"
    match_details: Dict[str, Any] = {}
    matched_at: datetime = datetime.utcnow()


class PriceHistory(BaseModel):
    """Mock PriceHistory model for testing."""
    id: Optional[int] = None
    product_id: int
    price: float
    original_price: Optional[float] = None
    recorded_at: datetime = datetime.utcnow()


class PriceAlert(BaseModel):
    """Mock PriceAlert model for testing."""
    id: Optional[int] = None
    product_id: int
    user_email: str
    alert_type: str = "price_drop"
    threshold_percentage: Optional[float] = None
    target_price: Optional[float] = None
    is_active: bool = True
    last_triggered: Optional[datetime] = None


# Mock database models if needed
class Base:
    """Mock SQLAlchemy Base."""
    metadata = type('metadata', (), {
        'create_all': lambda self, bind: None
    })()


def get_db():
    """Mock get_db function."""
    return None