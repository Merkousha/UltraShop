from django.db import models


class Order(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        PAID = "paid", "Paid"
        PACKED = "packed", "Packed"
        SHIPPED = "shipped", "Shipped"
        DELIVERED = "delivered", "Delivered"
        CANCELLED = "cancelled", "Cancelled"
        REFUNDED = "refunded", "Refunded"

    store = models.ForeignKey("core.Store", on_delete=models.CASCADE, related_name="orders")
    customer = models.ForeignKey("customers.Customer", on_delete=models.SET_NULL, null=True, blank=True)
    guest_phone = models.CharField(max_length=20, blank=True, default="")
    guest_name = models.CharField(max_length=200, blank=True, default="")
    shipping_address = models.TextField(blank=True, default="")
    shipping_city = models.CharField(max_length=100, blank=True, default="")
    shipping_province = models.CharField(max_length=100, blank=True, default="")
    shipping_postal_code = models.CharField(max_length=20, blank=True, default="")
    shipping_email = models.EmailField(blank=True, default="")
    shipping_method = models.CharField(max_length=50, blank=True, default="")
    status = models.CharField(max_length=12, choices=Status.choices, default=Status.PENDING)
    payment_reference = models.CharField(max_length=200, blank=True, default="")
    refunded_amount = models.PositiveBigIntegerField(default=0)
    note = models.TextField(blank=True, default="")
    routing_plan = models.JSONField(
        null=True,
        blank=True,
        default=None,
        help_text="Auto-routing result from SmartRoutingService (SO-52).",
    )
    discount_code_used = models.CharField(max_length=50, blank=True, default="")
    discount_amount = models.PositiveBigIntegerField(default=0, help_text="Discount applied in IRR")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "orders"
        indexes = [
            models.Index(fields=["store", "status"]),
            models.Index(fields=["store", "created_at"]),
        ]
        ordering = ["-created_at"]

    def __str__(self):
        return f"Order #{self.pk} — {self.store.name}"

    @property
    def total(self):
        return sum(line.line_total for line in self.lines.all())

    @property
    def total_after_discount(self):
        return max(0, self.total - self.discount_amount)


class OrderLine(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="lines")
    product_name = models.CharField(max_length=300)
    variant_name = models.CharField(max_length=200, blank=True, default="")
    sku = models.CharField(max_length=100, blank=True, default="")
    quantity = models.PositiveIntegerField(default=1)
    unit_price = models.PositiveBigIntegerField()
    product = models.ForeignKey("catalog.Product", on_delete=models.SET_NULL, null=True, blank=True)
    variant = models.ForeignKey("catalog.ProductVariant", on_delete=models.SET_NULL, null=True, blank=True)

    class Meta:
        db_table = "order_lines"

    @property
    def line_total(self):
        return self.quantity * self.unit_price


class OrderStatusEvent(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="status_events")
    status = models.CharField(max_length=12)
    actor = models.ForeignKey("core.User", on_delete=models.SET_NULL, null=True, blank=True)
    note = models.TextField(blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "order_status_events"
        ordering = ["created_at"]
