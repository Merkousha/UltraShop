import re
from django.db import models
from django.core.exceptions import ValidationError


def normalize_phone(value):
    """Strip non-digits and ensure leading 0 or country code for Iran."""
    digits = re.sub(r"\D", "", str(value))
    if digits.startswith("98"):
        return digits
    if digits.startswith("0"):
        return "98" + digits[1:]
    if len(digits) == 10 and digits.startswith("9"):
        return "98" + digits
    return digits


class Customer(models.Model):
    """Per-store customer; identity is (store, phone). Login via phone + OTP only."""
    store = models.ForeignKey(
        "stores.Store",
        on_delete=models.CASCADE,
        related_name="customers",
    )
    phone = models.CharField("شماره موبایل", max_length=20, db_index=True)
    name = models.CharField("نام", max_length=255, blank=True)
    email = models.EmailField(blank=True)
    last_login_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "مشتری"
        verbose_name_plural = "مشتری‌ها"
        ordering = ["-created_at"]
        unique_together = [["store", "phone"]]

    def __str__(self):
        return f"{self.phone} @ {self.store.name}"

    def save(self, *args, **kwargs):
        self.phone = normalize_phone(self.phone)
        super().save(*args, **kwargs)


class LoginOTP(models.Model):
    """One-time code for customer login/register. Scoped by store + phone."""
    PURPOSE_LOGIN = "login"
    PURPOSE_CHOICES = [(PURPOSE_LOGIN, "ورود / ثبت‌نام")]

    store = models.ForeignKey(
        "stores.Store",
        on_delete=models.CASCADE,
        related_name="login_otps",
        null=True,
        blank=True,
    )
    phone = models.CharField(max_length=20, db_index=True)
    code = models.CharField(max_length=10)
    purpose = models.CharField(max_length=20, choices=PURPOSE_CHOICES, default=PURPOSE_LOGIN)
    expires_at = models.DateTimeField()
    attempts = models.PositiveSmallIntegerField(default=0)
    is_used = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "کد ورود"
        verbose_name_plural = "کدهای ورود"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["phone", "purpose", "is_used"]),
        ]
