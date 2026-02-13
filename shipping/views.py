from django.shortcuts import redirect, get_object_or_404, render
from django.views.generic import View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponseForbidden

from stores.models import user_can_access_store
from orders.models import Order
from .models import Shipment


class CreateShipmentView(LoginRequiredMixin, View):
    """Store owner or staff: create shipment for an order and set order to Shipped."""
    def post(self, request, order_id):
        store = getattr(request, "store", None)
        if not store or not user_can_access_store(request.user, store):
            return HttpResponseForbidden()
        order = get_object_or_404(Order, pk=order_id, store=store)
        if getattr(order, "shipment", None):
            from django.contrib import messages
            messages.info(request, "این سفارش قبلاً ارسال شده است.")
            return redirect("orders:dashboard_order_detail", order_id=order.pk)
        tracking = request.POST.get("tracking_number", "").strip()
        shipment = Shipment.objects.create(
            store=store,
            order=order,
            tracking_number=tracking or f"SH-{order.pk}",
            status=Shipment.STATUS_CREATED,
        )
        order.status = Order.STATUS_SHIPPED
        order.save(update_fields=["status"])
        from orders.models import record_order_status
        record_order_status(order, Order.STATUS_SHIPPED, actor=request.user)
        try:
            from core.notifications import send_shipping_notification
            send_shipping_notification(order, shipment=shipment, request=request)
        except Exception:
            pass
        from django.contrib import messages
        messages.success(request, "ارسال ثبت شد.")
        return redirect("orders:dashboard_order_detail", order_id=order.pk)


class TrackShipmentView(View):
    """Public or customer: view shipment status by shipment id (and optionally verify order belongs to customer)."""
    def get(self, request, shipment_id):
        shipment = get_object_or_404(Shipment, pk=shipment_id)
        store = getattr(request, "store", None)
        if not store or shipment.store_id != store.pk:
            return redirect("core:home")
        # Optional: if customer, ensure order belongs to them
        customer = getattr(request, "customer", None)
        if shipment.order_id and customer and shipment.order.customer_id != customer.pk:
            from django.http import HttpResponseForbidden
            return HttpResponseForbidden()
        return render(request, "shipping/track.html", {"shipment": shipment})
