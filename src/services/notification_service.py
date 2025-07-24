"""Mock notification service."""

from typing import Any


class NotificationService:
    """Mock notification service."""
    
    async def send_price_alert(self, email: str, product: Any, alert_type: str, old_price: float, new_price: float):
        """Send price alert."""
        pass
    
    async def send_email(self, to: str, subject: str, body: str):
        """Send email."""
        pass
