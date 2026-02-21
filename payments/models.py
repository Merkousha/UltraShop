from django.db import models


class Payment(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        SUCCESS = "success", "Success"
        FAILED = "failed", "Failed"

    order = models.ForeignKey("orders.Order", on_delete=models.CASCADE, related_name="payments")
    gateway = models.CharField(max_length=50)
    amount = models.PositiveBigIntegerField()
    authority = models.CharField(max_length=200, blank=True, default="")
    reference = models.CharField(max_length=200, blank=True, default="")
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.PENDING)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "payments"
