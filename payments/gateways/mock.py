"""Mock gateway for development: no redirect, simulate success in callback."""
from .base import BaseGateway


class MockGateway(BaseGateway):
    def request(self, amount_rials, callback_url, description, order_id=None):
        authority = f"mock-{order_id or 0}-{id(self)}"
        sep = "&" if "?" in callback_url else "?"
        payment_url = f"{callback_url}{sep}Authority={authority}&Status=OK"
        return True, payment_url, authority, ""

    def verify(self, authority, amount_rials):
        if authority and authority.startswith("mock-"):
            return True, f"REF-{authority}", ""
        return False, "", "Invalid authority"
