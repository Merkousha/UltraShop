from django.db import models


class ShippingCarrier(models.Model):
    """PA-21: Platform-level carrier config (name, code, optional API credentials)."""
    name = models.CharField("Name", max_length=100)
    code = models.CharField("Code", max_length=50, unique=True)
    is_active = models.BooleanField(default=True)
    api_credentials = models.TextField("API credentials (e.g. key=value)", blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Shipping carrier"
        verbose_name_plural = "Shipping carriers"
        ordering = ["name"]

    def __str__(self):
        return f"{self.name} ({self.code})"


class Shipment(models.Model):
    """Platform-level shipment; linked to one order (and store)."""
    STATUS_CREATED = "created"
    STATUS_PICKED_UP = "picked_up"
    STATUS_IN_TRANSIT = "in_transit"
    STATUS_DELIVERED = "delivered"
    STATUS_EXCEPTION = "exception"
    STATUS_CHOICES = [
        (STATUS_CREATED, "ثبت شده"),
        (STATUS_PICKED_UP, "تحویل به مرکز"),
        (STATUS_IN_TRANSIT, "در راه"),
        (STATUS_DELIVERED, "تحویل داده شده"),
        (STATUS_EXCEPTION, "مشکل"),
    ]

    store = models.ForeignKey(
        "stores.Store",
        on_delete=models.CASCADE,
        related_name="shipments",
    )
    order = models.OneToOneField(
        "orders.Order",
        on_delete=models.CASCADE,
        related_name="shipment",
        null=True,
        blank=True,
    )
    carrier = models.CharField("حمل‌کننده", max_length=100, default="پلتفرم")
    tracking_number = models.CharField("کد رهگیری", max_length=100, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_CREATED)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "ارسال"
        verbose_name_plural = "ارسال‌ها"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.tracking_number or self.pk} @ {self.store.name}"
