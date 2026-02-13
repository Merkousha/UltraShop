from django.db import models
from django.conf import settings


class Order(models.Model):
    """Order per store; customer or guest; line items and shipping snapshot."""
    STATUS_PENDING = "pending"
    STATUS_PAID = "paid"
    STATUS_PACKED = "packed"
    STATUS_SHIPPED = "shipped"
    STATUS_DELIVERED = "delivered"
    STATUS_CANCELLED = "cancelled"
    STATUS_REFUNDED = "refunded"
    STATUS_CHOICES = [
        (STATUS_PENDING, "در انتظار پرداخت"),
        (STATUS_PAID, "پرداخت شده"),
        (STATUS_PACKED, "آماده ارسال"),
        (STATUS_SHIPPED, "ارسال شده"),
        (STATUS_DELIVERED, "تحویل داده شده"),
        (STATUS_CANCELLED, "لغو شده"),
        (STATUS_REFUNDED, "بازپرداخت شده"),
    ]

    store = models.ForeignKey(
        "stores.Store",
        on_delete=models.CASCADE,
        related_name="orders",
    )
    customer = models.ForeignKey(
        "customers.Customer",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="orders",
    )
    guest_phone = models.CharField(max_length=20, blank=True)
    guest_name = models.CharField(max_length=255, blank=True)
    # Shipping snapshot
    shipping_full_name = models.CharField(max_length=255)
    shipping_phone = models.CharField(max_length=20)
    shipping_email = models.EmailField(blank=True)
    shipping_address = models.TextField()
    shipping_city = models.CharField(max_length=100)
    shipping_method = models.CharField(max_length=50, default="platform")  # platform, pickup, local
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_PENDING)
    payment_reference = models.CharField(max_length=255, blank=True)
    total = models.DecimalField(max_digits=14, decimal_places=0, default=0)
    refunded_amount = models.DecimalField("مبلغ بازپرداخت شده", max_digits=14, decimal_places=0, default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    @property
    def refundable_amount(self):
        """Amount that can still be refunded."""
        return max(self.total - self.refunded_amount, 0)

    class Meta:
        verbose_name = "سفارش"
        verbose_name_plural = "سفارش‌ها"
        ordering = ["-created_at"]

    def __str__(self):
        return f"#{self.pk} @ {self.store.name}"

    @property
    def display_customer(self):
        if self.customer_id:
            return self.customer.phone or "مشتری"
        return self.guest_phone or self.guest_name or "مهمان"


class OrderLine(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="lines")
    product = models.ForeignKey(
        "catalog.Product",
        on_delete=models.PROTECT,
        related_name="order_lines",
    )
    variant = models.ForeignKey(
        "catalog.ProductVariant",
        on_delete=models.PROTECT,
        related_name="order_lines",
    )
    quantity = models.PositiveIntegerField()
    price = models.DecimalField(max_digits=14, decimal_places=0)  # snapshot

    class Meta:
        verbose_name = "آیتم سفارش"
        verbose_name_plural = "آیتم‌های سفارش"

    @property
    def line_total(self):
        return self.price * self.quantity


class OrderStatusEvent(models.Model):
    """Record each order status change for timeline (SO-21)."""
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="status_events")
    status = models.CharField(max_length=20, choices=Order.STATUS_CHOICES)
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="order_status_events",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at"]
        verbose_name = "تغییر وضعیت سفارش"
        verbose_name_plural = "تغییرات وضعیت سفارش"

    def __str__(self):
        return f"#{self.order_id} -> {self.get_status_display()}"


def record_order_status(order, status, actor=None):
    """Append a status change to order timeline."""
    OrderStatusEvent.objects.create(order=order, status=status, actor=actor)
