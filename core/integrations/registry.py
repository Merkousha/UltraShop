"""Registry of all available integrations (Phase 4)."""

from core.integrations.postal import IranPostIntegration
from core.integrations.payment import ZarinpalGateway
from core.integrations.tax import MoadianTaxIntegration

AVAILABLE_INTEGRATIONS = [
    IranPostIntegration,
    ZarinpalGateway,
    MoadianTaxIntegration,
]

# Quick lookup: integration_id → class
_REGISTRY = {cls.integration_id: cls for cls in AVAILABLE_INTEGRATIONS}


def get_integration(integration_id: str, store, credentials: dict):
    """Instantiate an integration by id.

    Returns the integration instance, or None if integration_id is unknown.
    """
    cls = _REGISTRY.get(integration_id)
    if cls is None:
        return None
    return cls(store=store, credentials=credentials)
