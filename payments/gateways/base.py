class BaseGateway:
    """Abstract payment gateway: request returns (success, payment_url, authority); verify(authority) returns (success, reference)."""
    def request(self, amount_rials, callback_url, description, order_id=None):
        """
        Start payment. Returns (success: bool, payment_url: str, authority: str, error: str).
        """
        raise NotImplementedError

    def verify(self, authority, amount_rials):
        """
        Verify after callback. Returns (success: bool, reference: str, error: str).
        """
        raise NotImplementedError
