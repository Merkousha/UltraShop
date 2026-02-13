from django.db import models


class Payment(models.Model):
    """Payment attempt for an order; stores gateway reference and status."""
    STATUS_PENDING = "pending"
    STATUS_SUCCESS = "success"
    STATUS_FAILED = "failed"
    STATUS_CHOICES = [
        (STATUS_PENDING, "pending"),
        (STATUS_SUCCESS, "success"),
        (STATUS_FAILED, "failed"),
    ]

    order = models.ForeignKey(
        "orders.Order",
        on_delete=models.CASCADE,
        related_name="payments",
    )
    gateway = models.CharField(max_length=50, default="mock")
    amount = models.DecimalField(max_digits=14, decimal_places=0)
    authority = models.CharField(max_length=255, blank=True)
    reference = models.CharField(max_length=255, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_PENDING)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Payment"
        verbose_name_plural = "Payments"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.order_id} @ {self.gateway}"
