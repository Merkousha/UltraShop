from django.db import models


class StoreTransaction(models.Model):
    class Type(models.TextChoices):
        REVENUE = "revenue", "Revenue"
        EXPENSE = "expense", "Expense"
        COMMISSION = "commission", "Commission"
        REFUND = "refund", "Refund"
        PAYOUT = "payout", "Payout"
        SHIPPING = "shipping", "Shipping"

    store = models.ForeignKey("core.Store", on_delete=models.CASCADE, related_name="transactions")
    amount = models.BigIntegerField(help_text="Positive = credit, Negative = debit (IRR)")
    type = models.CharField(max_length=12, choices=Type.choices, default=Type.REVENUE)
    description = models.CharField(max_length=500, blank=True, default="")
    order = models.ForeignKey("orders.Order", on_delete=models.SET_NULL, null=True, blank=True)
    payout_request = models.ForeignKey("PayoutRequest", on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "store_transactions"
        indexes = [
            models.Index(fields=["store", "created_at"]),
        ]
        ordering = ["-created_at"]


class PayoutRequest(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        APPROVED = "approved", "Approved"
        REJECTED = "rejected", "Rejected"

    store = models.ForeignKey("core.Store", on_delete=models.CASCADE, related_name="payout_requests")
    amount = models.PositiveBigIntegerField()
    payment_details = models.TextField(help_text="Bank account / card info")
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.PENDING)
    admin_note = models.TextField(blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)
    resolved_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "payout_requests"
        ordering = ["-created_at"]


class PlatformCommission(models.Model):
    store = models.ForeignKey("core.Store", on_delete=models.CASCADE, related_name="commissions")
    order = models.ForeignKey("orders.Order", on_delete=models.CASCADE, related_name="commissions")
    amount = models.PositiveBigIntegerField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "platform_commissions"
