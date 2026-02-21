from core.models import AuditLog


def log_action(*, actor=None, store=None, action, resource_type="", resource_id="", details=None):
    AuditLog.objects.create(
        actor=actor,
        store=store,
        action=action,
        resource_type=resource_type,
        resource_id=str(resource_id) if resource_id else "",
        details=details or {},
    )
