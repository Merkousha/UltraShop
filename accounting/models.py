from django.db import models
from decimal import Decimal


class PayoutRequest(models.Model):
    """Store owner requests withdrawal; platform admin approves."""
    STATUS_PENDING = "pending"
    STATUS_APPROVED = "approved"
    STATUS_REJECTED = "rejected"
    STATUS_CHOICES = [
        (STATUS_PENDING, "در انتظار"),
        (STATUS_APPROVED, "تأیید شده"),
        (STATUS_REJECTED, "رد شده"),
    ]

    store = models.ForeignKey(
        "stores.Store",
        on_delete=models.CASCADE,
        related_name="payout_requests",
    )
    amount = models.DecimalField("مبلغ", max_digits=14, decimal_places=0)
    payment_details = models.TextField("اطلاعات پرداخت (شبا، شماره حساب و ...)", blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_PENDING)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "درخواست تسویه"
        verbose_name_plural = "درخواست‌های تسویه"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.store.name} {self.amount} {self.get_status_display()}"


class StoreTransaction(models.Model):
    """
    Single-entry: amount positive = store earns, negative = refund or payout.
    Store balance = sum(amount) for the store.
    """
    store = models.ForeignKey(
        "stores.Store",
        on_delete=models.CASCADE,
        related_name="transactions",
    )
    amount = models.DecimalField("مبلغ", max_digits=14, decimal_places=0)
    description = models.CharField("شرح", max_length=255)
    order = models.ForeignKey(
        "orders.Order",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="accounting_transactions",
    )
    payout_request = models.ForeignKey(
        PayoutRequest,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="transactions",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "تراکنش فروشگاه"
        verbose_name_plural = "تراکنش‌های فروشگاه"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.store.name} {self.amount} {self.description}"


class PlatformCommission(models.Model):
    """Commission earned by platform from a store order (for PA-34 report)."""
    store = models.ForeignKey(
        "stores.Store",
        on_delete=models.CASCADE,
        related_name="platform_commissions",
    )
    order = models.ForeignKey(
        "orders.Order",
        on_delete=models.CASCADE,
        related_name="platform_commissions",
    )
    amount = models.DecimalField("مبلغ کمیسیون", max_digits=14, decimal_places=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "کمیسیون پلتفرم"
        verbose_name_plural = "کمیسیون‌های پلتفرم"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.store.name} #{self.order_id} {self.amount}"
