from django.db import models
from django.utils import timezone


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
