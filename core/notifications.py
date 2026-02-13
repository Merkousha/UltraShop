"""Send order and shipping notifications by email (Django send_mail)."""
from django.core.mail import send_mail
from django.conf import settings
from django.urls import reverse


def _from_email():
    return getattr(settings, "DEFAULT_FROM_EMAIL", "noreply@ultrashop.local")


def _store_absolute_uri(order, request, path):
    """Build absolute URL for store subdomain with given path (e.g. /order/1/confirmation/)."""
    if not request:
        return ""
    scheme = "https" if request.is_secure() else "http"
    root = getattr(settings, "PLATFORM_ROOT_DOMAIN", "ultrashop.local")
    host = f"{order.store.username}.{root}"
    port = request.get_port()
    port_suffix = f":{port}" if port not in ("80", "443") else ""
    return f"{scheme}://{host}{port_suffix}{path}"


def send_order_confirmation(order, request=None):
    """Send order confirmation email if shipping_email is set."""
    if not order.shipping_email:
        return
    store = order.store
    subject = f"[{store.name}] سفارش #{order.pk} ثبت شد"
    path = reverse("orders:confirmation", kwargs={"order_id": order.pk})
    order_url = _store_absolute_uri(order, request, path) if request else ""
    body = f"""سلام،

سفارش شما در {store.name} با شماره #{order.pk} ثبت شد.
مبلغ کل: {order.total:.0f} تومان.

"""
    if order_url:
        body += f"لینک مشاهده سفارش: {order_url}\n"
    body += "\nبا تشکر"
    try:
        send_mail(
            subject,
            body,
            _from_email(),
            [order.shipping_email],
            fail_silently=True,
        )
    except Exception:
        pass


def send_shipping_notification(order, shipment=None, request=None):
    """Send shipping notification when order is shipped (if shipping_email set). Pass shipment for track link."""
    if not order.shipping_email:
        return
    store = order.store
    subject = f"[{store.name}] سفارش #{order.pk} ارسال شد"
    track_url = ""
    if request and shipment:
        path = reverse("shipping:track", kwargs={"shipment_id": shipment.pk})
        track_url = _store_absolute_uri(order, request, path)
    tracking_number = shipment.tracking_number if shipment else ""
    body = f"""سلام،

سفارش #{order.pk} شما از {store.name} ارسال شده است.
"""
    if tracking_number:
        body += f"کد رهگیری: {tracking_number}\n"
    if track_url:
        body += f"لینک پیگیری: {track_url}\n"
    body += "\nبا تشکر"
    try:
        send_mail(
            subject,
            body,
            _from_email(),
            [order.shipping_email],
            fail_silently=True,
        )
    except Exception:
        pass
