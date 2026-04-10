from django.db import models
from django.utils import timezone


class AbandonedCart(models.Model):
    """Persisted cart snapshot for recovery campaigns."""
    store = models.ForeignKey("core.Store", on_delete=models.CASCADE, related_name="abandoned_carts")
    customer = models.ForeignKey(
        "customers.Customer", on_delete=models.SET_NULL,
        null=True, blank=True, related_name="abandoned_carts"
    )
    session_key = models.CharField(max_length=100, blank=True, default="")
    phone = models.CharField(max_length=20, blank=True, default="")
    email = models.EmailField(blank=True, default="")
    cart_data = models.JSONField(default=dict, help_text="{str(variant_pk): quantity}")
    recovered = models.BooleanField(default=False)
    recovery_sent_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "abandoned_carts"
        indexes = [
            models.Index(fields=["store", "recovered", "updated_at"]),
        ]

    def __str__(self):
        return f"AbandonedCart #{self.pk} — {self.store.name} — {'بازیابی شد' if self.recovered else 'رها شده'}"

    @property
    def item_count(self):
        return sum(self.cart_data.values()) if self.cart_data else 0


class Customer(models.Model):
    """Per-store customer identified by phone + OTP."""
    store = models.ForeignKey("core.Store", on_delete=models.CASCADE, related_name="customers")
    phone = models.CharField(max_length=20)
    name = models.CharField(max_length=200, blank=True, default="")
    email = models.EmailField(blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "customers"
        unique_together = ("store", "phone")

    def __str__(self):
        return f"{self.phone} @ {self.store.name}"


class LoginOTP(models.Model):
    store = models.ForeignKey("core.Store", on_delete=models.CASCADE)
    phone = models.CharField(max_length=20)
    code = models.CharField(max_length=6)
    attempts = models.PositiveSmallIntegerField(default=0)
    is_used = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()

    class Meta:
        db_table = "login_otps"

    def is_expired(self):
        return timezone.now() > self.expires_at
