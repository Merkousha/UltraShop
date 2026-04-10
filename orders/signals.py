"""
orders/signals.py — Auto-trigger SmartRoutingService when an order transitions
to 'paid' status and the store has auto_route_enabled=True.
"""
import logging

from django.db.models.signals import pre_save
from django.dispatch import receiver

from orders.models import Order

logger = logging.getLogger(__name__)


@receiver(pre_save, sender=Order)
def auto_route_on_paid(sender, instance, **kwargs):
    """
    When an Order transitions to status='paid':
      - if store.auto_route_enabled is True
      - and routing_plan is not yet set
    → run SmartRoutingService, reserve stock, and persist the plan.
    """
    if not instance.pk:
        # New order being created — no previous state to compare
        return

    try:
        previous = sender.objects.get(pk=instance.pk)
    except sender.DoesNotExist:
        return

    # Only act on status transitions *to* paid
    if previous.status == instance.status:
        return
    if instance.status != "paid":
        return

    # Check store setting
    store = instance.store
    if not getattr(store, "auto_route_enabled", False):
        return

    # Skip if routing plan already computed
    if instance.routing_plan:
        return

    try:
        from core.smart_routing_service import SmartRoutingService

        service = SmartRoutingService(instance)
        plan = service.compute_plan()
        service.reserve_stock_for_plan(plan)
        instance.routing_plan = SmartRoutingService.plan_to_json(plan)
        logger.info(
            "Auto-routing applied for order #%s (store=%s)",
            instance.pk,
            store.pk,
        )
    except Exception:
        logger.exception(
            "Auto-routing failed for order #%s (store=%s)",
            instance.pk,
            store.pk,
        )
