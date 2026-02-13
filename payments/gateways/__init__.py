from .base import BaseGateway
from .mock import MockGateway
from .zarinpal import ZarinPalGateway

def get_gateway(name="mock", merchant_id="", sandbox=True, **kwargs):
    if name == "zarinpal" and merchant_id:
        return ZarinPalGateway(merchant_id=merchant_id, sandbox=sandbox)
    return MockGateway()
