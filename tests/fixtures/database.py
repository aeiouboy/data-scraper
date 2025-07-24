"""Database fixtures for testing."""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
# TODO: Update for SQLAlchemy/Supabase
from tests.models_mock import Base, get_db
from src.models.product import Product
from tests.models_mock import ScrapingJob, ProductMatch, PriceHistory
from tests.models_mock import ScrapingJob
import asyncio
from datetime import datetime, timedelta


@pytest.fixture(scope="session")
def test_engine():
    """Create a test database engine."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    return engine


@pytest.fixture(scope="function")
def test_session(test_engine):
    """Create a test database session."""
    TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)
    session = TestSessionLocal()
    yield session
    session.rollback()
    session.close()


@pytest.fixture
def override_get_db(test_session):
    """Override the get_db dependency."""
    def _override_get_db():
        try:
            yield test_session
        finally:
            pass
    return _override_get_db


@pytest.fixture
async def seeded_db(test_session):
    """Database with test data."""
    # Add retailers
    retailers = ["homepro", "megahome", "thaiwatsadu", "boonthavorn"]
    
    # Add products
    products = []
    for i, retailer in enumerate(retailers):
        for j in range(5):
            product = Product(
                retailer_code=retailer,
                sku=f"{retailer}_SKU_{j:03d}",
                name=f"Test Product {j} from {retailer.title()}",
                current_price=100.0 * (j + 1),
                original_price=120.0 * (j + 1),
                brand=f"Brand {j % 3}",
                category=["Tools", "Power Tools", "Drills"][j % 3],
                is_promotion=j % 2 == 0,
                image_url=f"https://example.com/{retailer}/product_{j}.jpg",
                product_url=f"https://example.com/{retailer}/product_{j}",
                specifications={"power": f"{100 * (j + 1)}W", "voltage": "220V"},
                in_stock=j % 3 != 0,
                last_updated=datetime.utcnow() - timedelta(hours=j)
            )
            test_session.add(product)
            products.append(product)
    
    # Add scraping jobs
    for retailer in retailers:
        job = ScrapingJob(
            retailer_code=retailer,
            job_type="category",
            status="completed",
            started_at=datetime.utcnow() - timedelta(hours=2),
            completed_at=datetime.utcnow() - timedelta(hours=1),
            total_products=5,
            successful_products=5,
            failed_products=0
        )
        test_session.add(job)
    
    # Add product matches
    for i in range(0, len(products), 2):
        if i + 1 < len(products):
            match = ProductMatch(
                product1_id=products[i].id,
                product2_id=products[i + 1].id,
                confidence_score=0.85 + (i * 0.02),
                match_type="automatic",
                matched_at=datetime.utcnow()
            )
            test_session.add(match)
    
    # Add price history
    for product in products[:10]:
        for days_ago in range(7):
            price_history = PriceHistory(
                product_id=product.id,
                price=product.current_price * (1 + (days_ago * 0.01)),
                original_price=product.original_price,
                recorded_at=datetime.utcnow() - timedelta(days=days_ago)
            )
            test_session.add(price_history)
    
    test_session.commit()
    
    yield test_session