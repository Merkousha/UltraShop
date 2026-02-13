from decimal import Decimal
from django.shortcuts import redirect, get_object_or_404, render
from django.views.generic import View, ListView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.db import transaction
from django.http import HttpResponseForbidden
from django.urls import reverse_lazy

from catalog.cart import get_cart_items, cart_total, set_cart_items
from catalog.models import ProductVariant

from .models import Order, OrderLine


from stores.mixins import StoreAccessMixin

class StoreOwnerOrderMixin(StoreAccessMixin):
    """Require login and store access (owner or staff)."""
    pass


def _cart_context(request, store):
    """Build cart items with variants for order creation."""
    items = get_cart_items(request.session, store.pk)
    variants = ProductVariant.objects.filter(
        pk__in=[x.get("variant_id") for x in items],
        product__store=store,
    ).select_related("product")
    variant_map = {v.pk: v for v in variants}
    result = []
    for item in items:
        v = variant_map.get(item.get("variant_id"))
        if v and item.get("qty", 0) > 0:
            result.append((item, v))
    return result


class PlaceOrderView(View):
    """Create order from cart and checkout_address; reduce stock; clear cart."""
    def post(self, request):
        store = getattr(request, "store", None)
        if not store:
            return redirect("core:home")
        address = request.session.get("checkout_address") or {}
        if not address.get("full_name") or not address.get("address"):
            messages.error(request, "آدرس ارسال را تکمیل کنید.")
            return redirect("catalog:checkout_address")
        cart_items = _cart_context(request, store)
        if not cart_items:
            messages.info(request, "سبد خرید خالی است.")
            return redirect("catalog:cart_detail")
        # Re-validate stock
        for item, variant in cart_items:
            if variant.stock < item.get("qty", 0):
                messages.error(request, f"موجودی «{variant.product.name}» کافی نیست.")
                return redirect("catalog:checkout_review")
        customer = getattr(request, "customer", None)
        total = cart_total(cart_items)
        with transaction.atomic():
            order = Order.objects.create(
                store=store,
                customer=customer,
                guest_phone=address.get("phone", "") if not customer else "",
                guest_name=address.get("full_name", "") if not customer else "",
                shipping_full_name=address.get("full_name", ""),
                shipping_phone=address.get("phone", ""),
                shipping_email=address.get("email", ""),
                shipping_address=address.get("address", ""),
                shipping_city=address.get("city", ""),
                shipping_method="platform",
                status=Order.STATUS_PENDING,
                total=total,
            )
            for item, variant in cart_items:
                qty = item.get("qty", 0)
                price = Decimal(str(item.get("price", 0)))
                OrderLine.objects.create(
                    order=order,
                    product=variant.product,
                    variant=variant,
                    quantity=qty,
                    price=price,
                )
                variant.stock -= qty
                variant.save(update_fields=["stock"])
            from .models import record_order_status
            record_order_status(order, Order.STATUS_PENDING, actor=None)
        # Clear cart and address for this store
        set_cart_items(request.session, store.pk, [])
        request.session.pop("checkout_address", None)
        request.session.modified = True
        messages.success(request, f"سفارش #{order.pk} با موفقیت ثبت شد.")
        try:
            from core.notifications import send_order_confirmation
            send_order_confirmation(order, request=request)
        except Exception:
            pass
        return redirect("orders:confirmation", order_id=order.pk)


class OrderConfirmationView(View):
    """Thank-you page after placing order; show order number and link to track (if logged in)."""
    def get(self, request, order_id):
        store = getattr(request, "store", None)
        if not store:
            return redirect("core:home")
        order = get_object_or_404(Order, pk=order_id, store=store)
        customer = getattr(request, "customer", None)
        if order.customer_id and order.customer_id != (customer.pk if customer else None):
            from stores.models import user_can_access_store
            if not request.user.is_authenticated or not user_can_access_store(request.user, store):
                return redirect("core:home")
        return render(request, "orders/confirmation.html", {"order": order})


# ---------- Store dashboard (owner) ----------

class DashboardOrderListView(StoreOwnerOrderMixin, ListView):
    model = Order
    template_name = "orders/dashboard/order_list.html"
    context_object_name = "orders"
    paginate_by = 20

    def get_queryset(self):
        store = getattr(self.request, "store", None)
        if not store:
            return Order.objects.none()
        qs = Order.objects.filter(store=store).prefetch_related("lines")
        status = self.request.GET.get("status")
        if status:
            qs = qs.filter(status=status)
        return qs.order_by("-created_at")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["order_status_choices"] = Order.STATUS_CHOICES
        return context


class DashboardOrderDetailView(StoreOwnerOrderMixin, View):
    def get(self, request, order_id):
        store = getattr(request, "store", None)
        order = get_object_or_404(Order, pk=order_id, store=store)
        order = Order.objects.prefetch_related("lines", "status_events__actor").get(pk=order.pk)
        from shipping.models import Shipment
        order_shipment = Shipment.objects.filter(order=order).first()
        return render(request, "orders/dashboard/order_detail.html", {"order": order, "status_choices": Order.STATUS_CHOICES, "order_shipment": order_shipment})

    def post(self, request, order_id):
        store = getattr(request, "store", None)
        order = get_object_or_404(Order, pk=order_id, store=store)
        action = request.POST.get("action")
        if action == "status":
            new_status = request.POST.get("status", "").strip()
            if new_status in dict(Order.STATUS_CHOICES):
                order.status = new_status
                order.save(update_fields=["status"])
                from .models import record_order_status
                record_order_status(order, new_status, actor=request.user)
                messages.success(request, "وضعیت سفارش به‌روز شد.")
        elif action == "cancel":
            if order.status in (Order.STATUS_PENDING, Order.STATUS_PAID):
                with transaction.atomic():
                    for line in order.lines.all():
                        line.variant.stock += line.quantity
                        line.variant.save(update_fields=["stock"])
                    order.status = Order.STATUS_CANCELLED
                    order.save(update_fields=["status"])
                    from .models import record_order_status
                    record_order_status(order, Order.STATUS_CANCELLED, actor=request.user)
                messages.success(request, "سفارش لغو شد و موجودی بازگردانده شد.")
            else:
                messages.error(request, "امکان لغو این سفارش نیست.")
        elif action == "refund":
            refundable = order.refundable_amount
            if refundable <= 0:
                messages.error(request, "مبلغ قابل بازپرداخت برای این سفارش صفر است.")
            elif order.status not in (Order.STATUS_PAID, Order.STATUS_PACKED, Order.STATUS_SHIPPED, Order.STATUS_DELIVERED):
                messages.error(request, "فقط برای سفارش‌های پرداخت‌شده امکان بازپرداخت وجود دارد.")
            else:
                try:
                    amount_str = request.POST.get("refund_amount", "").strip()
                    if amount_str.lower() in ("full", "کامل", ""):
                        amount = refundable
                    else:
                        amount = Decimal(amount_str.replace(",", ""))
                    if amount <= 0 or amount > refundable:
                        messages.error(request, f"مبلغ باید بین ۱ تا {refundable:.0f} تومان باشد.")
                    else:
                        reason = request.POST.get("refund_reason", "").strip()
                        with transaction.atomic():
                            from accounting.services import post_order_refunded
                            post_order_refunded(order, amount=amount, reason=reason or None)
                            order.refunded_amount += amount
                            if order.refunded_amount >= order.total:
                                order.status = Order.STATUS_REFUNDED
                            order.save(update_fields=["refunded_amount", "status", "updated_at"])
                            if order.status == Order.STATUS_REFUNDED:
                                from .models import record_order_status
                                record_order_status(order, Order.STATUS_REFUNDED, actor=request.user)
                            from core.models import log_audit
                            log_audit(request.user, "refund", "order", order.pk, f"amount={amount} reason={reason or '-'}", store=store)
                        messages.success(request, f"بازپرداخت {amount:.0f} تومان ثبت شد.")
                except (ValueError, TypeError):
                    messages.error(request, "مبلغ معتبر نیست.")
        return redirect("orders:dashboard_order_detail", order_id=order.pk)


# ---------- Customer (storefront) ----------

class MyOrdersView(View):
    """Customer order history (requires phone+OTP login for this store)."""
    def get(self, request):
        store = getattr(request, "store", None)
        if not store:
            return redirect("core:home")
        customer = getattr(request, "customer", None)
        if not customer:
            from django.urls import reverse
            next_url = request.build_absolute_uri(reverse("orders:my_orders"))
            return redirect("customers:login_phone" + "?next=" + next_url)
        orders = Order.objects.filter(store=store, customer=customer).order_by("-created_at")
        return render(request, "orders/my_orders.html", {"orders": orders})


class CustomerOrderDetailView(View):
    """Customer views their order detail; can see shipment/track link."""
    def get(self, request, order_id):
        store = getattr(request, "store", None)
        if not store:
            return redirect("core:home")
        customer = getattr(request, "customer", None)
        if not customer:
            from django.urls import reverse
            next_url = request.build_absolute_uri(reverse("orders:customer_order_detail", kwargs={"order_id": order_id}))
            return redirect("customers:login_phone" + "?next=" + next_url)
        order = get_object_or_404(Order, pk=order_id, store=store, customer=customer)
        order = Order.objects.prefetch_related("lines").get(pk=order.pk)
        from shipping.models import Shipment
        order_shipment = Shipment.objects.filter(order=order).first()
        return render(request, "orders/customer_order_detail.html", {"order": order, "order_shipment": order_shipment})
