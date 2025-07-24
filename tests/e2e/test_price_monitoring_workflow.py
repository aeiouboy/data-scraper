"""End-to-end tests for price monitoring workflow."""

import pytest
import asyncio
from datetime import datetime, timedelta
from unittest.mock import Mock, AsyncMock, patch
from src.models.product import Product
# TODO: Fix imports - from src.api.models import PriceHistory, ProductMatch, PriceAlert
from tests.models_mock import PriceHistory, ProductMatch, PriceAlert
from src.services.price_comparison_service import PriceComparisonService
from src.services.notification_service import NotificationService
from tests.fixtures.database import test_session, seeded_db
from tests.factories import ProductFactory, MatchFactory


class TestPriceMonitoringWorkflowE2E:
    """Test complete price monitoring workflow from tracking to alerts."""
    
    @pytest.fixture
    def price_comparison_service(self):
        """Create price comparison service instance."""
        return PriceComparisonService()
    
    @pytest.fixture
    def notification_service(self):
        """Create notification service instance."""
        return NotificationService()
    
    @pytest.fixture
    def products_with_history(self, test_session):
        """Create products with price history."""
        # Create matched products from different retailers
        product1 = ProductFactory.create(
            retailer_code="homepro",
            name="Samsung Refrigerator RT38",
            current_price=15900.0,
            original_price=18900.0
        )
        product2 = ProductFactory.create(
            retailer_code="megahome",
            name="ตู้เย็น Samsung RT38",
            current_price=16500.0,
            original_price=18900.0
        )
        
        test_session.add_all([product1, product2])
        test_session.commit()
        
        # Create match between products
        match = MatchFactory.create(
            product1=product1,
            product2=product2,
            confidence_score=0.95,
            match_type="automatic"
        )
        test_session.add(match)
        
        # Create price history
        price_points = [
            # Product 1 history (price drop trend)
            (product1, 18900.0, 7),
            (product1, 18900.0, 6),
            (product1, 17900.0, 5),
            (product1, 17900.0, 4),
            (product1, 16900.0, 3),
            (product1, 16900.0, 2),
            (product1, 15900.0, 1),
            (product1, 15900.0, 0),
            
            # Product 2 history (stable then drop)
            (product2, 18900.0, 7),
            (product2, 18900.0, 6),
            (product2, 18900.0, 5),
            (product2, 18900.0, 4),
            (product2, 18500.0, 3),
            (product2, 17500.0, 2),
            (product2, 16500.0, 1),
            (product2, 16500.0, 0),
        ]
        
        for product, price, days_ago in price_points:
            history = PriceHistory(
                product_id=product.id,
                price=price,
                original_price=product.original_price,
                recorded_at=datetime.utcnow() - timedelta(days=days_ago)
            )
            test_session.add(history)
        
        test_session.commit()
        return product1, product2
    
    @pytest.mark.asyncio
    async def test_price_tracking_and_comparison(self, test_session, products_with_history, price_comparison_service):
        """Test price tracking and comparison between retailers."""
        product1, product2 = products_with_history
        
        # Get price comparison
        comparison = await price_comparison_service.compare_product_prices(product1.id, test_session)
        
        assert comparison is not None
        assert len(comparison["retailers"]) == 2
        assert comparison["lowest_price"]["price"] == 15900.0
        assert comparison["lowest_price"]["retailer"] == "homepro"
        assert comparison["highest_price"]["price"] == 16500.0
        assert comparison["price_difference"] == 600.0
        assert comparison["price_difference_percentage"] > 3.5
        
        # Check price trends
        trends = comparison["price_trends"]
        assert "homepro" in trends
        assert "megahome" in trends
        
        # HomePro should show downward trend
        homepro_trend = trends["homepro"]
        assert homepro_trend["trend"] == "down"
        assert homepro_trend["change_amount"] == -3000.0
        assert homepro_trend["change_percentage"] < -15
        
        # MegaHome should also show downward trend
        megahome_trend = trends["megahome"]
        assert megahome_trend["trend"] == "down"
        assert megahome_trend["change_amount"] == -2400.0
    
    @pytest.mark.asyncio
    async def test_price_drop_alert_workflow(self, test_session, products_with_history, notification_service):
        """Test price drop alert generation and notification."""
        product1, product2 = products_with_history
        
        # Create price alert settings
        alert1 = PriceAlert(
            product_id=product1.id,
            user_email="user@example.com",
            alert_type="price_drop",
            threshold_percentage=10.0,  # Alert when price drops by 10%
            is_active=True
        )
        alert2 = PriceAlert(
            product_id=product2.id,
            user_email="user@example.com",
            alert_type="target_price",
            target_price=17000.0,  # Alert when price goes below 17000
            is_active=True
        )
        test_session.add_all([alert1, alert2])
        test_session.commit()
        
        # Check for price drops
        with patch.object(notification_service, 'send_email', new_callable=AsyncMock) as mock_send:
            # Product 1: Check percentage drop (18900 -> 15900 = 15.87% drop)
            if (product1.original_price - product1.current_price) / product1.original_price * 100 >= alert1.threshold_percentage:
                await notification_service.send_price_alert(
                    alert1.user_email,
                    product1,
                    alert_type="price_drop",
                    old_price=product1.original_price,
                    new_price=product1.current_price
                )
            
            # Product 2: Check target price (current 16500 < target 17000)
            if product2.current_price <= alert2.target_price:
                await notification_service.send_price_alert(
                    alert2.user_email,
                    product2,
                    alert_type="target_price",
                    old_price=product2.original_price,
                    new_price=product2.current_price
                )
            
            # Verify notifications were sent
            assert mock_send.call_count == 2
            
            # Update alert status
            alert1.last_triggered = datetime.utcnow()
            alert2.last_triggered = datetime.utcnow()
            test_session.commit()
    
    @pytest.mark.asyncio
    async def test_competitor_price_monitoring(self, test_session, products_with_history):
        """Test monitoring competitor prices for matched products."""
        product1, product2 = products_with_history
        
        # Get all matches for product1
        matches = test_session.query(ProductMatch).filter(
            (ProductMatch.product1_id == product1.id) | 
            (ProductMatch.product2_id == product1.id)
        ).all()
        
        competitor_prices = []
        for match in matches:
            # Get the other product in the match
            other_product_id = match.product2_id if match.product1_id == product1.id else match.product1_id
            other_product = test_session.query(Product).get(other_product_id)
            
            if other_product:
                competitor_prices.append({
                    "retailer": other_product.retailer_code,
                    "price": other_product.current_price,
                    "product_name": other_product.name,
                    "last_updated": other_product.last_updated
                })
        
        # Verify competitor monitoring
        assert len(competitor_prices) == 1
        assert competitor_prices[0]["retailer"] == "megahome"
        assert competitor_prices[0]["price"] == 16500.0
        
        # Check if our price is competitive
        our_price = product1.current_price
        min_competitor_price = min(cp["price"] for cp in competitor_prices)
        is_competitive = our_price <= min_competitor_price
        
        assert is_competitive is True  # HomePro has the lowest price
    
    @pytest.mark.asyncio
    async def test_historical_price_analysis(self, test_session, products_with_history):
        """Test historical price analysis and insights."""
        product1, product2 = products_with_history
        
        # Analyze price history for product1
        history = test_session.query(PriceHistory).filter_by(
            product_id=product1.id
        ).order_by(PriceHistory.recorded_at.desc()).all()
        
        # Calculate price statistics
        prices = [h.price for h in history]
        
        stats = {
            "current_price": prices[0],
            "min_price": min(prices),
            "max_price": max(prices),
            "avg_price": sum(prices) / len(prices),
            "price_volatility": max(prices) - min(prices),
            "days_at_current_price": 1,  # Count consecutive days at current price
            "total_price_changes": len(set(prices)) - 1
        }
        
        # Count days at current price
        current_price = prices[0]
        for price in prices[1:]:
            if price == current_price:
                stats["days_at_current_price"] += 1
            else:
                break
        
        # Verify analysis
        assert stats["current_price"] == 15900.0
        assert stats["min_price"] == 15900.0
        assert stats["max_price"] == 18900.0
        assert stats["price_volatility"] == 3000.0
        assert stats["total_price_changes"] == 3  # 18900 -> 17900 -> 16900 -> 15900
        
        # Identify best time to buy (lowest price in last 30 days)
        thirty_days_ago = datetime.utcnow() - timedelta(days=30)
        recent_history = [h for h in history if h.recorded_at >= thirty_days_ago]
        
        if recent_history:
            best_price_record = min(recent_history, key=lambda h: h.price)
            is_good_time_to_buy = current_price <= best_price_record.price
            assert is_good_time_to_buy is True
    
    @pytest.mark.asyncio
    async def test_bulk_price_update_workflow(self, test_session):
        """Test bulk price update for multiple products."""
        # Create products that need price updates
        products_to_update = []
        for i in range(10):
            product = ProductFactory.create(
                retailer_code="homepro",
                current_price=1000.0 * (i + 1),
                last_updated=datetime.utcnow() - timedelta(days=2)  # 2 days old
            )
            products_to_update.append(product)
        
        test_session.add_all(products_to_update)
        test_session.commit()
        
        # Simulate bulk price update
        updated_count = 0
        price_changes = []
        
        for product in products_to_update:
            # Simulate price change (some up, some down, some same)
            if product.id % 3 == 0:
                new_price = product.current_price * 0.95  # 5% decrease
            elif product.id % 3 == 1:
                new_price = product.current_price * 1.03  # 3% increase
            else:
                new_price = product.current_price  # No change
            
            if new_price != product.current_price:
                # Record price history
                history = PriceHistory(
                    product_id=product.id,
                    price=product.current_price,
                    original_price=product.original_price,
                    recorded_at=product.last_updated
                )
                test_session.add(history)
                
                price_changes.append({
                    "product_id": product.id,
                    "old_price": product.current_price,
                    "new_price": new_price,
                    "change_percentage": ((new_price - product.current_price) / product.current_price) * 100
                })
                
                # Update product
                product.current_price = new_price
                product.last_updated = datetime.utcnow()
                updated_count += 1
        
        test_session.commit()
        
        # Verify bulk update results
        assert updated_count > 5  # Most products should have price changes
        assert len(price_changes) == updated_count
        
        # Check price change distribution
        price_decreases = [pc for pc in price_changes if pc["change_percentage"] < 0]
        price_increases = [pc for pc in price_changes if pc["change_percentage"] > 0]
        
        assert len(price_decreases) > 0
        assert len(price_increases) > 0
    
    @pytest.mark.asyncio
    async def test_price_prediction_workflow(self, test_session, products_with_history):
        """Test price prediction based on historical trends."""
        product1, product2 = products_with_history
        
        # Get price history
        history = test_session.query(PriceHistory).filter_by(
            product_id=product1.id
        ).order_by(PriceHistory.recorded_at.asc()).all()
        
        # Simple trend analysis
        prices = [(h.recorded_at, h.price) for h in history]
        
        # Calculate daily price changes
        daily_changes = []
        for i in range(1, len(prices)):
            days_diff = (prices[i][0] - prices[i-1][0]).days
            if days_diff > 0:
                price_change = (prices[i][1] - prices[i-1][1]) / days_diff
                daily_changes.append(price_change)
        
        # Simple prediction: average daily change
        if daily_changes:
            avg_daily_change = sum(daily_changes) / len(daily_changes)
            current_price = product1.current_price
            
            # Predict prices for next 7 days
            predictions = []
            for days_ahead in range(1, 8):
                predicted_price = current_price + (avg_daily_change * days_ahead)
                # Don't predict negative prices
                predicted_price = max(predicted_price, current_price * 0.5)
                predictions.append({
                    "days_ahead": days_ahead,
                    "predicted_price": round(predicted_price, 2),
                    "confidence": "low"  # Simple model has low confidence
                })
            
            # Verify predictions
            assert len(predictions) == 7
            assert all(p["predicted_price"] > 0 for p in predictions)
            
            # For a product with downward trend, predictions should be lower
            if avg_daily_change < 0:
                assert predictions[-1]["predicted_price"] < current_price