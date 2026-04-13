from django.db import models
from django.utils.text import slugify


class Category(models.Model):
    store = models.ForeignKey("core.Store", on_delete=models.CASCADE, related_name="categories")
    parent = models.ForeignKey("self", on_delete=models.CASCADE, null=True, blank=True, related_name="children")
    name = models.CharField(max_length=200)
    slug = models.SlugField(max_length=220, allow_unicode=True)
    description = models.TextField(blank=True, default="")
    image = models.ImageField(upload_to="categories/", blank=True, null=True)
    meta_title = models.CharField(max_length=200, blank=True, default="")
    meta_description = models.TextField(blank=True, default="")
    sort_order = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "categories"
        unique_together = ("store", "slug")
        ordering = ["sort_order", "name"]
        verbose_name_plural = "categories"

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name, allow_unicode=True)
        super().save(*args, **kwargs)


class Product(models.Model):
    class Status(models.TextChoices):
        DRAFT = "draft", "Draft"
        ACTIVE = "active", "Active"
        ARCHIVED = "archived", "Archived"

    store = models.ForeignKey("core.Store", on_delete=models.CASCADE, related_name="products")
    name = models.CharField(max_length=300)
    slug = models.SlugField(max_length=320, allow_unicode=True)
    description = models.TextField(blank=True, default="")
    sku = models.CharField(max_length=100, blank=True, default="")
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.DRAFT)
    categories = models.ManyToManyField(Category, blank=True, related_name="products")
    meta_title = models.CharField(max_length=200, blank=True, default="")
    meta_description = models.TextField(blank=True, default="")
    focus_keywords = models.CharField(max_length=500, blank=True, default="", help_text="Comma-separated keywords for SEO (SO-17)")
    og_description = models.TextField(blank=True, default="", help_text="Open Graph description for social share (SO-17)")
    requires_shipping = models.BooleanField(default=True, help_text="آیا این محصول نیاز به ارسال فیزیکی دارد؟")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "products"
        unique_together = ("store", "slug")
        indexes = [
            models.Index(fields=["store", "status"]),
            models.Index(fields=["store", "created_at"]),
        ]

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name, allow_unicode=True)
        super().save(*args, **kwargs)

    @property
    def primary_image(self):
        return self.images.filter(is_primary=True).first() or self.images.first()

    @property
    def shipping_enabled(self):
        """Compatibility alias used by checkout/business rules."""
        return self.requires_shipping


class ProductImage(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="images")
    image = models.ImageField(upload_to="products/")
    alt_text = models.CharField(max_length=300, blank=True, default="")
    is_primary = models.BooleanField(default=False)
    sort_order = models.IntegerField(default=0)

    class Meta:
        db_table = "product_images"
        ordering = ["sort_order"]

    def __str__(self):
        return f"Image for {self.product.name} (#{self.sort_order})"


class ProductVariant(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="variants")
    name = models.CharField(max_length=200, help_text="e.g. Red / Large")
    sku = models.CharField(max_length=100, blank=True, default="")
    price = models.PositiveBigIntegerField(help_text="Price in IRR")
    compare_at_price = models.PositiveBigIntegerField(null=True, blank=True)
    stock = models.PositiveIntegerField(
        default=0,
        help_text="Legacy: total stock. Prefer total_stock (sum of warehouse_stocks) when using multi-warehouse.",
    )
    weight = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, help_text="Weight in grams")
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "product_variants"

    def __str__(self):
        return f"{self.product.name} — {self.name}"

    @property
    def total_stock(self):
        """Total available quantity across all warehouses (available = quantity - reserved)."""
        from django.db.models import Sum
        agg = self.warehouse_stocks.aggregate(s=Sum("quantity"), r=Sum("reserved"))
        if agg["s"] is not None:
            return max(0, (agg["s"] or 0) - (agg["r"] or 0))
        return self.stock  # backward compat when no WarehouseStock rows

    @property
    def total_reserved(self):
        from django.db.models import Sum
        r = self.warehouse_stocks.aggregate(s=Sum("reserved"))["s"]
        return r or 0


class DiscountCode(models.Model):
    """Per-store discount code (percent or fixed amount in IRR)."""

    class DiscountType(models.TextChoices):
        PERCENT = "percent", "درصد"
        FIXED = "fixed", "مبلغ ثابت"

    store = models.ForeignKey("core.Store", on_delete=models.CASCADE, related_name="discount_codes")
    code = models.CharField(max_length=50)
    discount_type = models.CharField(max_length=10, choices=DiscountType.choices)
    value = models.PositiveBigIntegerField(help_text="درصد (۰-۱۰۰) یا مبلغ ثابت به ریال")
    min_order_amount = models.PositiveBigIntegerField(default=0, help_text="حداقل مبلغ سفارش برای اعمال کد")
    max_uses = models.PositiveIntegerField(null=True, blank=True, help_text="حداکثر تعداد استفاده (خالی = نامحدود)")
    used_count = models.PositiveIntegerField(default=0)
    expires_at = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "discount_codes"
        unique_together = [("store", "code")]

    def __str__(self):
        return f"{self.code} — {self.store.name}"

    def compute_discount(self, order_total: int) -> int:
        """Return discount amount in IRR for given order total."""
        if self.discount_type == self.DiscountType.PERCENT:
            pct = min(100, max(0, self.value))
            return int(order_total * pct / 100)
        return min(self.value, order_total)


class WarehouseStock(models.Model):
    """Per-warehouse, per-variant stock (Sprint 4 — SO-50, SO-51)."""
    warehouse = models.ForeignKey(
        "core.Warehouse", on_delete=models.CASCADE, related_name="stock_lines"
    )
    variant = models.ForeignKey(
        ProductVariant, on_delete=models.CASCADE, related_name="warehouse_stocks"
    )
    quantity = models.PositiveIntegerField(default=0)
    reserved = models.PositiveIntegerField(
        default=0,
        help_text="Quantity reserved for orders (e.g. pending shipment).",
    )
    last_restocked_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "warehouse_stocks"
        unique_together = ("warehouse", "variant")
        indexes = [
            models.Index(fields=["warehouse"]),
            models.Index(fields=["variant"]),
        ]

    def __str__(self):
        return f"{self.variant} @ {self.warehouse.name}: {self.quantity}"

    @property
    def available(self):
        return max(0, self.quantity - self.reserved)


# ─── SS-13: Inventory Audit Log ────────────────────────────────
class InventoryLog(models.Model):
    """ثبت تمام تغییرات موجودی انبار برای هر تنوع محصول (SS-13)."""

    class Action(models.TextChoices):
        ADJUST = "adjust", "تنظیم موجودی"
        TRANSFER = "transfer", "انتقال"
        RECEIPT = "receipt", "رسید کالا"
        SALE = "sale", "فروش"
        RETURN = "return", "مرجوعی"

    warehouse = models.ForeignKey(
        "core.Warehouse",
        on_delete=models.CASCADE,
        related_name="inventory_logs",
    )
    variant = models.ForeignKey(
        ProductVariant,
        on_delete=models.CASCADE,
        related_name="inventory_logs",
    )
    action = models.CharField(max_length=20, choices=Action.choices)
    quantity_before = models.IntegerField()
    quantity_change = models.IntegerField(
        help_text="مثبت = افزایش، منفی = کاهش"
    )
    quantity_after = models.IntegerField()
    note = models.TextField(blank=True, default="")
    actor = models.ForeignKey(
        "core.User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="inventory_log_entries",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "inventory_logs"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["warehouse", "created_at"]),
            models.Index(fields=["variant", "created_at"]),
        ]

    def __str__(self):
        return (
            f"[{self.get_action_display()}] {self.variant} @ {self.warehouse.name}: "
            f"{self.quantity_before} → {self.quantity_after}"
        )
