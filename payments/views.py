from django.shortcuts import redirect, get_object_or_404
from django.views.generic import View
from django.contrib import messages
from django.conf import settings
from django.db import transaction
from django.urls import reverse

from orders.models import Order
from .models import Payment
from .gateways import get_gateway


class StartPaymentView(View):
    """Start payment for an order: create Payment record, redirect to gateway."""
    def post(self, request):
        store = getattr(request, "store", None)
        if not store:
            return redirect("core:home")
        order_id = request.POST.get("order_id")
        if not order_id:
            messages.error(request, "سفارش مشخص نیست.")
            return redirect("core:home")
        order = get_object_or_404(Order, pk=order_id, store=store)
        if order.status != Order.STATUS_PENDING:
            messages.info(request, "این سفارش قبلاً پرداخت شده یا لغو شده است.")
            return redirect("orders:confirmation", order_id=order.pk)
        gateway_name = getattr(settings, "PAYMENT_GATEWAY", "mock")
        merchant_id = getattr(settings, "ZARINPAL_MERCHANT_ID", "")
        sandbox = getattr(settings, "ZARINPAL_SANDBOX", True)
        gateway = get_gateway(gateway_name, merchant_id=merchant_id, sandbox=sandbox)
        callback_url = request.build_absolute_uri(reverse("payments:callback")) + f"?order_id={order.pk}"
        success, payment_url, authority, err = gateway.request(
            amount_rials=order.total,
            callback_url=callback_url,
            description=f"سفارش #{order.pk}",
            order_id=order.pk,
        )
        if not success:
            messages.error(request, err or "خطا در اتصال به درگاه پرداخت.")
            return redirect("orders:confirmation", order_id=order.pk)
        Payment.objects.create(
            order=order,
            gateway=gateway_name,
            amount=order.total,
            authority=authority,
            status=Payment.STATUS_PENDING,
        )
        return redirect(payment_url)


class PaymentCallbackView(View):
    """Gateway callback: verify payment and set order to Paid."""
    def get(self, request):
        order_id = request.GET.get("order_id")
        authority = request.GET.get("Authority")
        status = request.GET.get("Status", "")
        if not order_id or not authority:
            messages.error(request, "پارامترهای بازگشت نامعتبر است.")
            return redirect("core:home")
        order = get_object_or_404(Order, pk=order_id)
        store = getattr(request, "store", None)
        if not store or order.store_id != store.pk:
            return redirect("core:home")
        if order.status != Order.STATUS_PENDING:
            messages.info(request, "این سفارش قبلاً پرداخت شده است.")
            return redirect("orders:confirmation", order_id=order.pk)
        payment = Payment.objects.filter(order=order, authority=authority, status=Payment.STATUS_PENDING).order_by("-created_at").first()
        if not payment:
            messages.error(request, "تراکنش یافت نشد.")
            return redirect("orders:confirmation", order_id=order.pk)
        if status != "OK":
            payment.status = Payment.STATUS_FAILED
            payment.save(update_fields=["status"])
            messages.warning(request, "پرداخت توسط کاربر لغو یا ناموفق بود.")
            return redirect("orders:confirmation", order_id=order.pk)
        gateway_name = payment.gateway
        merchant_id = getattr(settings, "ZARINPAL_MERCHANT_ID", "")
        sandbox = getattr(settings, "ZARINPAL_SANDBOX", True)
        gateway = get_gateway(gateway_name, merchant_id=merchant_id, sandbox=sandbox)
        success, reference, err = gateway.verify(authority=authority, amount_rials=order.total)
        if not success:
            payment.status = Payment.STATUS_FAILED
            payment.save(update_fields=["status"])
            messages.error(request, err or "تأیید پرداخت ناموفق بود.")
            return redirect("orders:confirmation", order_id=order.pk)
        with transaction.atomic():
            payment.reference = reference
            payment.status = Payment.STATUS_SUCCESS
            payment.save(update_fields=["reference", "status"])
            order.status = Order.STATUS_PAID
            order.payment_reference = reference
            order.save(update_fields=["status", "payment_reference"])
            from orders.models import record_order_status
            record_order_status(order, Order.STATUS_PAID, actor=None)
            from accounting.services import post_order_paid
            post_order_paid(order)
        messages.success(request, "پرداخت با موفقیت انجام شد.")
        return redirect("orders:confirmation", order_id=order.pk)
