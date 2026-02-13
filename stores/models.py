import re
from django.db import models
from django.conf import settings
from django.core.exceptions import ValidationError


def validate_domain_value(value):
    """Domain: no spaces, no path, no leading dot."""
    if not value or " " in value or "/" in value or value.strip().startswith("."):
        raise ValidationError("دامنه معتبر نیست.", code="invalid_domain")


def validate_username(value):
    """Subdomain-safe: lowercase letters, numbers, hyphen only; 2–63 chars."""
    if not re.match(r"^[a-z0-9][a-z0-9-]{1,61}[a-z0-9]$", value):
        raise ValidationError(
            "فقط حروف کوچک انگلیسی، عدد و خط تیره مجاز است؛ بین ۳ تا ۶۳ کاراکتر.",
            code="invalid_username",
        )
    reserved = {"www", "api", "admin", "mail", "ftp", "platform", "app", "dashboard", "login", "signup", "static"}
    if value.lower() in reserved:
        raise ValidationError("این نام برای فروشگاه رزرو شده است.", code="reserved_username")


class Store(models.Model):
    """Tenant: one store per subdomain (username)."""
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="owned_stores",
    )
    name = models.CharField("نام فروشگاه", max_length=255)
    username = models.SlugField(
        "نام کاربری (زیردامنه)",
        max_length=63,
        unique=True,
        help_text="فروشگاه شما در آدرس username.ultrashop.local در دسترس خواهد بود.",
        validators=[validate_username],
    )
    slug = models.SlugField(max_length=63, unique=True, blank=True)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    allow_guest_checkout = models.BooleanField("خرید مهمان", default=True, help_text="اگر خاموش باشد، مشتری باید با موبایل و OTP وارد شود.")
    # Branding
    logo = models.ImageField("لوگو", upload_to="stores/logos/", blank=True, null=True)
    favicon = models.ImageField("فاویکون", upload_to="stores/favicons/", blank=True, null=True)
    primary_color = models.CharField("رنگ اصلی", max_length=7, blank=True, help_text="مثال: #3B82F6")
    theme_preset = models.CharField(
        "قالب ظاهری",
        max_length=20,
        choices=[("default", "پیش‌فرض"), ("minimal", "مینیمال"), ("bold", "پررنگ")],
        default="default",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "فروشگاه"
        verbose_name_plural = "فروشگاه‌ها"
        ordering = ["name"]

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = self.username
        super().save(*args, **kwargs)


class StoreDomain(models.Model):
    """Custom or subdomain for a store. Subdomain is derived from store.username; this model is for custom domains."""
    TYPE_SUBDOMAIN = "subdomain"
    TYPE_CUSTOM = "custom"
    TYPE_CHOICES = [(TYPE_SUBDOMAIN, "زیردامنه"), (TYPE_CUSTOM, "دامنه سفارشی")]
    SSL_PENDING = "pending"
    SSL_ACTIVE = "active"
    SSL_ERROR = "error"
    SSL_CHOICES = [(SSL_PENDING, "در انتظار"), (SSL_ACTIVE, "فعال"), (SSL_ERROR, "خطا")]

    store = models.ForeignKey(Store, on_delete=models.CASCADE, related_name="domains")
    domain = models.CharField("دامنه", max_length=253, validators=[validate_domain_value])
    domain_type = models.CharField(max_length=20, choices=TYPE_CHOICES, default=TYPE_CUSTOM)
    verified = models.BooleanField("تأیید شده", default=False)
    ssl_status = models.CharField("وضعیت SSL", max_length=20, choices=SSL_CHOICES, default=SSL_PENDING)
    is_primary = models.BooleanField("اصلی", default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "دامنه فروشگاه"
        verbose_name_plural = "دامنه‌های فروشگاه"
        unique_together = [["store", "domain"]]
        ordering = ["-is_primary", "domain"]

    def __str__(self):
        return f"{self.domain} → {self.store.name}"

    def save(self, *args, **kwargs):
        self.domain = self.domain.strip().lower()
        if self.is_primary:
            StoreDomain.objects.filter(store=self.store).exclude(pk=self.pk).update(is_primary=False)
        super().save(*args, **kwargs)


class StoreStaff(models.Model):
    """Staff member with access to store dashboard (not owner). Role can restrict sections (e.g. no accounting)."""
    ROLE_STAFF = "staff"
    ROLE_MANAGER = "manager"
    ROLE_CHOICES = [(ROLE_STAFF, "کارمند"), (ROLE_MANAGER, "مدیر")]

    store = models.ForeignKey(Store, on_delete=models.CASCADE, related_name="staff_members")
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="store_staff",
    )
    role = models.CharField("نقش", max_length=20, choices=ROLE_CHOICES, default=ROLE_STAFF)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "کارمند فروشگاه"
        verbose_name_plural = "کارمندان فروشگاه"
        unique_together = [["store", "user"]]
        ordering = ["store", "user"]

    def __str__(self):
        return f"{self.user.email} @ {self.store.name}"


def user_can_access_store(user, store):
    """True if user is owner or staff of the store."""
    if not user.is_authenticated or not store:
        return False
    if store.owner_id == user.pk:
        return True
    return StoreStaff.objects.filter(store=store, user=user).exists()


def user_is_store_owner(user, store):
    """True only if user is the store owner (for accounting and sensitive sections)."""
    if not user.is_authenticated or not store:
        return False
    return store.owner_id == user.pk
