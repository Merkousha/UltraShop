from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """Custom user model for store owners & staff. Email-based login."""
    email = models.EmailField(unique=True)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["username"]

    class Meta:
        db_table = "users"

    def __str__(self):
        return self.email


class Store(models.Model):
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name="stores")
    name = models.CharField(max_length=200)
    username = models.SlugField(max_length=60, unique=True, help_text="Subdomain: username.ultra-shop.com")
    tagline = models.CharField(max_length=300, blank=True, default="", help_text="Short slogan (SO-07)")
    description = models.TextField(blank=True, default="")
    logo = models.ImageField(upload_to="stores/logos/", blank=True, null=True)
    favicon = models.ImageField(upload_to="stores/favicons/", blank=True, null=True)
    primary_color = models.CharField(max_length=7, default="#6366f1")
    theme_preset = models.CharField(max_length=30, default="minimal")
    phone = models.CharField(max_length=20, blank=True, default="")
    support_email = models.EmailField(blank=True, default="")

    # Per-store notification config (SO-NotifConfig)
    sms_provider = models.CharField(
        max_length=50,
        blank=True,
        default="",
        choices=[("kavenegar", "کاوه نگار"), ("smsir", "sms.ir")],
    )
    sms_api_key_encrypted = models.TextField(blank=True, default="")
    sms_sender = models.CharField(max_length=30, blank=True, default="")
    email_host = models.CharField(max_length=200, blank=True, default="")
    email_port = models.PositiveIntegerField(default=587)
    email_username = models.CharField(max_length=200, blank=True, default="")
    email_password_encrypted = models.TextField(blank=True, default="")
    email_use_tls = models.BooleanField(default=True)
    email_from = models.EmailField(blank=True, default="")

    timezone = models.CharField(max_length=50, default="Asia/Tehran")
    currency = models.CharField(max_length=10, default="IRR")
    allow_guest_checkout = models.BooleanField(default=True)
    plan = models.ForeignKey("StorePlan", on_delete=models.SET_NULL, null=True, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "stores"

    def __str__(self):
        return self.name


class StoreDomain(models.Model):
    class DomainType(models.TextChoices):
        SUBDOMAIN = "subdomain", "Subdomain"
        CUSTOM = "custom", "Custom Domain"

    class SSLStatus(models.TextChoices):
        NONE = "none", "None"
        PENDING = "pending", "Pending"
        ACTIVE = "active", "Active"

    store = models.ForeignKey(Store, on_delete=models.CASCADE, related_name="domains")
    domain = models.CharField(max_length=253, unique=True)
    type = models.CharField(max_length=10, choices=DomainType.choices)
    verified = models.BooleanField(default=False)
    ssl_status = models.CharField(max_length=10, choices=SSLStatus.choices, default=SSLStatus.NONE)
    is_primary = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "store_domains"

    def __str__(self):
        return self.domain


class PlatformSettings(models.Model):
    """Singleton platform-wide settings."""
    name = models.CharField(max_length=200, default="UltraShop")
    support_email = models.EmailField(default="support@ultra-shop.com")
    terms_url = models.URLField(blank=True, default="")
    privacy_url = models.URLField(blank=True, default="")
    logo = models.ImageField(upload_to="platform/", blank=True, null=True)
    favicon = models.ImageField(upload_to="platform/", blank=True, null=True)

    # PA-11: Default store settings
    default_timezone = models.CharField(max_length=50, default="Asia/Tehran")
    default_currency = models.CharField(max_length=10, default="IRR")
    default_guest_checkout = models.BooleanField(default=True)

    # PA-12: Reserved subdomain names (JSON array)
    reserved_usernames = models.JSONField(
        default=list,
        blank=True,
        help_text="JSON array of reserved subdomain names",
    )

    # PA-15: SMS/Email provider config
    sms_provider = models.CharField(max_length=50, blank=True, default="")
    sms_api_key_encrypted = models.TextField(blank=True, default="")
    sms_sender = models.CharField(max_length=30, blank=True, default="")
    email_host = models.CharField(max_length=200, blank=True, default="")
    email_port = models.PositiveIntegerField(default=587)
    email_username = models.CharField(max_length=200, blank=True, default="")
    email_password_encrypted = models.TextField(blank=True, default="")
    email_use_tls = models.BooleanField(default=True)
    email_from = models.EmailField(blank=True, default="")

    # PA-20: Shipping service toggle
    shipping_enabled = models.BooleanField(default=True)

    # PA-13: AI service config (Sprint 5)
    openai_api_key_encrypted = models.TextField(blank=True, default="")
    anthropic_api_key_encrypted = models.TextField(blank=True, default="")
    vision_model = models.CharField(max_length=80, default="gpt-4o")
    text_model = models.CharField(max_length=80, default="gpt-4o-mini")
    image_gen_model = models.CharField(max_length=80, default="flux")
    ai_enabled = models.BooleanField(default=False)
    rate_limit_per_store_daily = models.PositiveIntegerField(default=50)

    class Meta:
        db_table = "platform_settings"
        verbose_name_plural = "Platform Settings"

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        self.pk = 1
        super().save(*args, **kwargs)

    @classmethod
    def load(cls):
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj


class ThemePreset(models.Model):
    """Platform-managed theme presets."""
    
    class Status(models.TextChoices):
        ACTIVE = "active", "فعال"
        DEPRECATED = "deprecated", "منسوخ"
        DRAFT = "draft", "پیشنویس"
    
    name = models.CharField(max_length=100)
    slug = models.SlugField(max_length=100, unique=True)
    description = models.TextField(blank=True, default="")
    tokens = models.JSONField(default=dict, help_text="Token values for this preset")
    thumbnail = models.ImageField(upload_to="theme_presets/", blank=True, null=True)
    version = models.CharField(max_length=20, default="1.0.0")
    status = models.CharField(max_length=15, choices=Status.choices, default=Status.ACTIVE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = "theme_presets"
        ordering = ["name"]
    
    def __str__(self):
        return f"{self.name} (v{self.version})"


class StoreTheme(models.Model):
    """Per-store design token overrides and theme configuration."""
    
    class RadiusScale(models.TextChoices):
        NONE = "none", "بدون گردی"
        SM = "sm", "کم"
        MD = "md", "متوسط"
        LG = "lg", "زیاد"
        XL = "xl", "خیلی زیاد"
        FULL = "full", "کامل"
    
    class ShadowLevel(models.TextChoices):
        NONE = "none", "بدون سایه"
        SM = "sm", "سبک"
        MD = "md", "متوسط"
        LG = "lg", "سنگین"
        XL = "xl", "خیلی سنگین"
    
    store = models.OneToOneField(Store, on_delete=models.CASCADE, related_name="theme")
    theme_preset = models.ForeignKey(
        "ThemePreset", on_delete=models.SET_NULL, null=True, blank=True, related_name="stores"
    )
    primary_color = models.CharField(max_length=7, default="#6366f1")
    secondary_color = models.CharField(max_length=7, default="#8b5cf6")
    accent_color = models.CharField(max_length=7, default="#f59e0b")
    heading_font = models.CharField(max_length=100, default="Vazirmatn", help_text="فونت تیترها")
    body_font = models.CharField(max_length=100, default="Vazirmatn", help_text="فونت متن")
    radius_scale = models.CharField(max_length=10, choices=RadiusScale.choices, default=RadiusScale.MD)
    shadow_level = models.CharField(max_length=10, choices=ShadowLevel.choices, default=ShadowLevel.MD)
    custom_css = models.TextField(blank=True, default="", help_text="CSS سفارشی (حداکثر ۵۰ کیلوبایت)")
    version = models.PositiveIntegerField(default=1)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = "store_themes"
    
    def __str__(self):
        return f"Theme for {self.store.name}"


class AuditLog(models.Model):
    actor = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    store = models.ForeignKey(Store, on_delete=models.SET_NULL, null=True, blank=True)
    action = models.CharField(max_length=100, db_index=True)
    resource_type = models.CharField(max_length=100, blank=True, default="")
    resource_id = models.CharField(max_length=100, blank=True, default="")
    details = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        db_table = "audit_logs"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.action} by {self.actor} at {self.created_at}"


class StorePlan(models.Model):
    """Platform-level subscription plan with feature limits."""
    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True)
    max_warehouses = models.PositiveIntegerField(default=1)
    max_products = models.PositiveIntegerField(default=100)
    max_ai_requests_daily = models.PositiveIntegerField(default=10)
    allow_custom_domain = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "store_plans"

    def __str__(self):
        return self.name


class StoreStaff(models.Model):
    class Role(models.TextChoices):
        STAFF = "staff", "Staff"
        MANAGER = "manager", "Manager"
        SALES_AGENT = "sales_agent", "مسئول فروش"
        ACCOUNTANT = "accountant", "حسابدار"

    store = models.ForeignKey(Store, on_delete=models.CASCADE, related_name="staff_members")
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="staff_roles")
    role = models.CharField(max_length=20, choices=Role.choices, default=Role.STAFF)
    warehouses = models.ManyToManyField(
        "Warehouse",
        related_name="staff_members",
        blank=True,
        help_text="Empty = access to all warehouses; otherwise only listed warehouses.",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "store_staff"
        unique_together = ("store", "user")

    def __str__(self):
        return f"{self.user.email} @ {self.store.name} ({self.role})"


# ─── Sprint 4: Multi-Warehouse (SO-50) ─────────────────────
class Warehouse(models.Model):
    """Per-store warehouse for inventory and shipping routing."""
    store = models.ForeignKey(Store, on_delete=models.CASCADE, related_name="warehouses")
    name = models.CharField(max_length=200)
    address = models.TextField(blank=True, default="")
    city = models.CharField(max_length=100, blank=True, default="")
    province = models.CharField(max_length=100, blank=True, default="")
    postal_code = models.CharField(max_length=20, blank=True, default="")
    phone = models.CharField(max_length=20, blank=True, default="")
    is_active = models.BooleanField(default=True)
    is_default = models.BooleanField(
        default=False,
        help_text="First warehouse for this store; used when no warehouse is specified.",
    )
    priority = models.PositiveIntegerField(
        default=0,
        help_text="Lower = higher priority for routing (e.g. nearest).",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "warehouses"
        ordering = ["priority", "name"]
        indexes = [
            models.Index(fields=["store", "is_active"]),
        ]

    def __str__(self):
        return f"{self.name} — {self.store.name}"


# ─── SO-46: Block Page Editor ─────────────────────────────
class AIDailyUsage(models.Model):
    """Per-store daily AI usage for rate limiting (Sprint 5 — PA-13)."""
    store = models.ForeignKey(Store, on_delete=models.CASCADE, related_name="ai_daily_usage")
    date = models.DateField(db_index=True)
    usage_count = models.PositiveIntegerField(default=0)

    class Meta:
        db_table = "ai_daily_usage"
        unique_together = ("store", "date")
        ordering = ["-date"]

    def __str__(self):
        return f"{self.store.name} — {self.date}: {self.usage_count}"


class LayoutConfiguration(models.Model):
    """Per-store, per-page layout: block order and block settings (drag & drop editor)."""

    class PageType(models.TextChoices):
        HOME = "home", "صفحه اصلی"
        CATEGORY = "category", "صفحه دسته‌بندی"
        PRODUCT = "product", "صفحه محصول"
        CUSTOM = "custom", "صفحه سفارشی"

    store = models.ForeignKey(Store, on_delete=models.CASCADE, related_name="layout_configs")
    page_type = models.CharField(max_length=20, choices=PageType.choices, default=PageType.HOME)
    block_order = models.JSONField(default=list, help_text="Ordered list of block IDs, e.g. ['hero', 'product_grid', 'category_grid']")
    block_settings = models.JSONField(default=dict, help_text="Per-block settings: { block_id: { ... } }")
    block_enabled = models.JSONField(default=dict, help_text="Per-block enabled: { block_id: true/false }")
    version = models.PositiveIntegerField(default=1)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "layout_configurations"
        unique_together = ("store", "page_type")
        ordering = ["store", "page_type"]

    def __str__(self):
        return f"Layout {self.get_page_type_display()} — {self.store.name}"


class LayoutConfigurationSnapshot(models.Model):
    """Snapshot of a layout for rollback (version history)."""
    store = models.ForeignKey(Store, on_delete=models.CASCADE, related_name="layout_snapshots")
    page_type = models.CharField(max_length=20)
    version = models.PositiveIntegerField()
    block_order = models.JSONField(default=list)
    block_settings = models.JSONField(default=dict)
    block_enabled = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "layout_configuration_snapshots"
        ordering = ["-created_at"]
        unique_together = ("store", "page_type", "version")


# ─── Phase 4: External Integrations (SO-Phase4) ───────────────
class StoreIntegration(models.Model):
    """Per-store external integration credentials and status.

    Credentials are stored encrypted using core.encryption helpers.
    """

    store = models.ForeignKey(
        Store,
        on_delete=models.CASCADE,
        related_name="integrations",
    )
    # e.g. "zarinpal", "iran_post", "moadian"
    integration_id = models.CharField(max_length=50, db_index=True)
    # JSON blob, encrypted via core.encryption.encrypt_value()
    credentials_encrypted = models.TextField(blank=True, default="")
    is_active = models.BooleanField(default=False)
    last_tested_at = models.DateTimeField(null=True, blank=True)
    test_result = models.CharField(max_length=200, blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "store_integrations"
        unique_together = [("store", "integration_id")]
        ordering = ["integration_id"]

    def __str__(self):
        return f"{self.integration_id} @ {self.store.name}"
