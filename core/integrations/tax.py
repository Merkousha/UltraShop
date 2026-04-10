"""Moadian (سامانه مودیان) tax system integration — stub implementation.

Production docs: https://tp.tax.gov.ir/
"""

import logging

from core.integrations.base import BaseIntegration

logger = logging.getLogger(__name__)


class MoadianTaxIntegration(BaseIntegration):
    integration_id = "moadian"
    integration_name = "سامانه مودیان"

    _API_BASE = "https://tp.tax.gov.ir/requestsmanager/api/v2"

    def submit_invoice(self, order) -> dict:
        """Submit a sales invoice to Moadian tax system.

        Returns {"fiscal_id": str, "status": str} on success.

        This is a *stub*: logs the attempt and returns a mock fiscal ID.
        In production call the Moadian REST API with a signed JWT payload.
        """
        order_id = getattr(order, "pk", order)
        logger.info(
            "[Moadian] submit_invoice store=%s order_id=%s (stub)",
            getattr(self.store, "name", self.store),
            order_id,
        )
        mock_fiscal_id = f"STUB-FISCAL-{order_id:08d}"
        return {
            "fiscal_id": mock_fiscal_id,
            "status": "pending",
            "message": "صورتحساب در صف ارسال قرار گرفت (محیط آزمایشی).",
            "_stub": True,
        }

    def test_connection(self) -> dict:
        logger.info(
            "[Moadian] test_connection store=%s (stub)",
            getattr(self.store, "name", self.store),
        )
        client_id = self.credentials.get("client_id", "")
        if not client_id:
            return {
                "success": False,
                "message": "شناسه مؤدی (client_id) وارد نشده است.",
            }
        return {
            "success": True,
            "message": (
                f"اتصال به سامانه مودیان با client_id «{client_id}» موفق بود "
                "(محیط آزمایشی — stub)."
            ),
        }
