from django.db import models


class ShippingCarrier(models.Model):
    name = models.CharField(max_length=200)
    code = models.SlugField(max_length=50, unique=True)
    is_active = models.BooleanField(default=True)
    api_credentials = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "shipping_carriers"

    def __str__(self):
        return self.name


class Shipment(models.Model):
    class Status(models.TextChoices):
        CREATED = "created", "Created"
        PICKED_UP = "picked_up", "Picked Up"
        IN_TRANSIT = "in_transit", "In Transit"
        DELIVERED = "delivered", "Delivered"
        EXCEPTION = "exception", "Exception"

    store = models.ForeignKey("core.Store", on_delete=models.CASCADE, related_name="shipments")
    order = models.ForeignKey("orders.Order", on_delete=models.CASCADE, related_name="shipments")
    carrier = models.ForeignKey(ShippingCarrier, on_delete=models.SET_NULL, null=True, blank=True)
    warehouse = models.ForeignKey(
        "core.Warehouse",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="shipments",
        help_text="Originating warehouse for this shipment (SO-52).",
    )
    tracking_number = models.CharField(max_length=200, blank=True, default="")
    status = models.CharField(max_length=12, choices=Status.choices, default=Status.CREATED)
    cost = models.PositiveBigIntegerField(default=0, help_text="Shipping cost in IRR")
    note = models.TextField(blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "shipments"
        indexes = [
            models.Index(fields=["store", "status"]),
            models.Index(fields=["store", "created_at"]),
        ]
        ordering = ["-created_at"]

    def __str__(self):
        return f"Shipment #{self.pk} — Order #{self.order_id}"

    ALLOWED_TRANSITIONS = {
        "created": ["picked_up", "exception"],
        "picked_up": ["in_transit", "exception"],
        "in_transit": ["delivered", "exception"],
        "exception": ["picked_up", "in_transit", "delivered"],
    }

    def can_transition_to(self, new_status):
        return new_status in self.ALLOWED_TRANSITIONS.get(self.status, [])
