from django.db import models
from django.utils.text import slugify


class Category(models.Model):
    """Product category per store; optional parent for hierarchy."""
    store = models.ForeignKey(
        "stores.Store",
        on_delete=models.CASCADE,
        related_name="categories",
    )
    parent = models.ForeignKey(
        "self",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="children",
    )
    name = models.CharField("نام", max_length=255)
    slug = models.SlugField(max_length=255, blank=True)
    description = models.TextField(blank=True)
    image = models.ImageField(upload_to="categories/", blank=True, null=True)
    meta_title = models.CharField(max_length=255, blank=True)
    meta_description = models.CharField(max_length=500, blank=True)
    sort_order = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "دسته‌بندی"
        verbose_name_plural = "دسته‌بندی‌ها"
        ordering = ["sort_order", "name"]
        unique_together = [["store", "slug"]]

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            base = slugify(self.name, allow_unicode=False) or "cat"
            self.slug = base
            cnt = 0
            while Category.objects.filter(store=self.store, slug=self.slug).exclude(pk=self.pk).exists():
                cnt += 1
                self.slug = f"{base}-{cnt}"
        super().save(*args, **kwargs)


class Product(models.Model):
    """Product per store; has variants for price/stock."""
    STATUS_DRAFT = "draft"
    STATUS_ACTIVE = "active"
    STATUS_ARCHIVED = "archived"
    STATUS_CHOICES = [
        (STATUS_DRAFT, "پیش‌نویس"),
        (STATUS_ACTIVE, "فعال"),
        (STATUS_ARCHIVED, "آرشیو"),
    ]

    store = models.ForeignKey(
        "stores.Store",
        on_delete=models.CASCADE,
        related_name="products",
    )
    categories = models.ManyToManyField(
        Category,
        related_name="products",
        blank=True,
    )
    name = models.CharField("نام", max_length=255)
    slug = models.SlugField(max_length=255, blank=True)
    description = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_DRAFT)
    image = models.ImageField(upload_to="products/", blank=True, null=True)
    meta_title = models.CharField(max_length=255, blank=True)
    meta_description = models.CharField(max_length=500, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "محصول"
        verbose_name_plural = "محصولات"
        ordering = ["-created_at"]
        unique_together = [["store", "slug"]]

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            base = slugify(self.name, allow_unicode=False) or "product"
            self.slug = base
            cnt = 0
            while Product.objects.filter(store=self.store, slug=self.slug).exclude(pk=self.pk).exists():
                cnt += 1
                self.slug = f"{base}-{cnt}"
        super().save(*args, **kwargs)


class ProductVariant(models.Model):
    """Single variant: SKU, price, stock. Product must have at least one variant to be sellable."""
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name="variants",
    )
    sku = models.CharField("کد کالا", max_length=100, blank=True)
    price = models.DecimalField("قیمت", max_digits=14, decimal_places=0)
    compare_at_price = models.DecimalField("قیمت مقایسه", max_digits=14, decimal_places=0, null=True, blank=True)
    stock = models.PositiveIntegerField("موجودی", default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "گونه محصول"
        verbose_name_plural = "گونه‌های محصول"
        ordering = ["pk"]

    def __str__(self):
        return f"{self.product.name} — {self.sku or self.pk}"

    @property
    def store(self):
        return self.product.store
