"""Zarinpal payment gateway integration — stub implementation.

Production docs: https://docs.zarinpal.com/
"""

import logging

from core.integrations.base import BaseIntegration

logger = logging.getLogger(__name__)


class ZarinpalGateway(BaseIntegration):
    integration_id = "zarinpal"
    integration_name = "زرین‌پال"

    _PAYMENT_REQUEST_URL = "https://api.zarinpal.com/pg/v4/payment/request.json"
    _PAYMENT_VERIFY_URL = "https://api.zarinpal.com/pg/v4/payment/verify.json"
    _PAYMENT_REDIRECT = "https://www.zarinpal.com/pg/StartPay/{authority}"

    def _merchant_id(self) -> str:
        return self.credentials.get("merchant_id", "")

    def create_payment(self, amount: int, description: str, callback_url: str) -> dict:
        """Create a Zarinpal payment request.

        Returns {"authority": str, "payment_url": str} on success.
        Raises RuntimeError on failure.

        This is a *stub*: no real HTTP request is made.
        """
        merchant_id = self._merchant_id()
        logger.info(
            "[Zarinpal] create_payment store=%s amount=%s merchant=%s (stub)",
            getattr(self.store, "name", self.store),
            amount,
            merchant_id,
        )
        stub_authority = "A00000000000000000000000000STUB"
        return {
            "authority": stub_authority,
            "payment_url": self._PAYMENT_REDIRECT.format(authority=stub_authority),
            "_stub": True,
        }

    def verify_payment(self, authority: str, amount: int) -> dict:
        """Verify a Zarinpal payment after the user returns from the gateway.

        Returns {"success": bool, "ref_id": str}.

        This is a *stub*.
        """
        logger.info(
            "[Zarinpal] verify_payment store=%s authority=%s (stub)",
            getattr(self.store, "name", self.store),
            authority,
        )
        return {
            "success": True,
            "ref_id": "123456789",
            "_stub": True,
        }

    def test_connection(self) -> dict:
        merchant_id = self._merchant_id()
        logger.info(
            "[Zarinpal] test_connection store=%s merchant=%s (stub)",
            getattr(self.store, "name", self.store),
            merchant_id,
        )
        if not merchant_id:
            return {
                "success": False,
                "message": "شناسه مرچنت (merchant_id) وارد نشده است.",
            }
        return {
            "success": True,
            "message": (
                f"اتصال به زرین‌پال با merchant_id «{merchant_id}» موفق بود "
                "(محیط آزمایشی — stub)."
            ),
        }
