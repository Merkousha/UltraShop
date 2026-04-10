"""Base class for all external integrations (Phase 4)."""


class BaseIntegration:
    """Base class for external integrations."""

    integration_id: str = ""
    integration_name: str = ""

    def __init__(self, store, credentials: dict):
        self.store = store
        self.credentials = credentials

    def test_connection(self) -> dict:
        """Returns {"success": bool, "message": str}"""
        raise NotImplementedError

    def is_configured(self) -> bool:
        return bool(self.credentials)
