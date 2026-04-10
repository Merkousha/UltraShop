"""Iranian Post (پست جمهوری اسلامی) integration — stub implementation.

Production endpoint: https://newtracking.post.ir/api/
"""

import logging

from core.integrations.base import BaseIntegration

logger = logging.getLogger(__name__)


class IranPostIntegration(BaseIntegration):
    integration_id = "iran_post"
    integration_name = "پست جمهوری اسلامی ایران"

    # In production this would be the real tracking API base URL.
    _API_BASE = "https://newtracking.post.ir/api"

    def track_shipment(self, tracking_number: str) -> dict:
        """Track a shipment via Iran Post API.

        Returns a status dict with keys:
            tracking_number, status, status_fa, last_event, events (list)

        This is a *stub*: it logs the attempt and returns mock data.
        Replace with a real HTTP call in production.
        """
        logger.info(
            "[IranPost] track_shipment called for store=%s tracking=%s (stub)",
            getattr(self.store, "name", self.store),
            tracking_number,
        )
        return {
            "tracking_number": tracking_number,
            "status": "in_transit",
            "status_fa": "در راه",
            "last_event": "بسته توسط مرکز توزیع تهران اسکن شد",
            "events": [
                {"date": "1403/09/01", "time": "10:30", "description": "تحویل به پست"},
                {"date": "1403/09/02", "time": "08:15", "description": "ورود به مرکز توزیع تهران"},
            ],
            "_stub": True,
        }

    def test_connection(self) -> dict:
        """Sandbox always returns success with a note that this is a stub."""
        logger.info(
            "[IranPost] test_connection called for store=%s (stub)",
            getattr(self.store, "name", self.store),
        )
        return {
            "success": True,
            "message": (
                "اتصال به سرویس پست موفق بود (محیط آزمایشی — stub). "
                "در محیط واقعی کلید API معتبر وارد کنید."
            ),
        }
