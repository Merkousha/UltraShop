import json

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Q, F
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect
from django.utils.text import slugify
from django.views import View
from django.views.generic import ListView, TemplateView

from catalog.models import Category, Product, ProductImage, ProductVariant
from core.models import PlatformSettings, Store, StoreStaff, StoreTheme, ThemePreset
from core.theme_service import generate_color_scale, validate_contrast
from core.css_sanitizer import sanitize_css
from orders.models import Order


class StoreAccessMixin(LoginRequiredMixin):
    """Ensure user has access to a store (owner or staff)."""

    def dispatch(self, request, *args, **kwargs):
        store = self.get_current_store(request)
        if not store:
            return redirect("dashboard:home")
        request.current_store = store
        return super().dispatch(request, *args, **kwargs)

    def get_current_store(self, request):
        store_id = request.session.get("current_store_id")
        if not store_id:
            return None
        store = Store.objects.filter(pk=store_id).first()
        if not store:
            return None
        if store.owner == request.user:
            return store
        if StoreStaff.objects.filter(store=store, user=request.user).exists():
            return store
        return None


class DashboardHomeView(LoginRequiredMixin, TemplateView):
    template_name = "dashboard/home.html"

    def get(self, request, *args, **kwargs):
        user = request.user
        owned = Store.objects.filter(owner=user)
        staff = Store.objects.filter(staff_members__user=user)
        stores = (owned | staff).distinct()

        # If current_store_id is set but invalid (deleted or no access), clear it
        current_id = request.session.get("current_store_id")
        if current_id:
            store = Store.objects.filter(pk=current_id).first()
            if not store or (store.owner != user and not StoreStaff.objects.filter(store=store, user=user).exists()):
                del request.session["current_store_id"]
                request.session.modified = True
                current_id = None

        # No store selected: auto-select or create one so dashboard links (products, categories, etc.) work
        if not current_id:
            if stores:
                first = stores.first()
                if first and (
                    first.owner == user or StoreStaff.objects.filter(store=first, user=user).exists()
                ):
                    request.session["current_store_id"] = first.pk
                    request.session.modified = True
            else:
                # User has no store (e.g. old account or edge case): create default store (PA-11, PA-12)
                ps = PlatformSettings.load()
                reserved = set(ps.reserved_usernames or [])
                base_username = f"store-{user.pk}"
                username = base_username
                suffix = 0
                while username in reserved or Store.objects.filter(username=username).exists():
                    suffix += 1
                    username = f"{base_username}-{suffix}"
                store = Store.objects.create(
                    owner=user,
                    name="فروشگاه من",
                    username=username,
                    timezone=ps.default_timezone,
                    currency=ps.default_currency,
                    allow_guest_checkout=ps.default_guest_checkout,
                )
                request.session["current_store_id"] = store.pk
                request.session.modified = True
        return super().get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        user = self.request.user
        owned = Store.objects.filter(owner=user)
        staff = Store.objects.filter(staff_members__user=user)
        ctx["stores"] = (owned | staff).distinct()
        ctx["current_store_id"] = self.request.session.get("current_store_id")
        return ctx


class SelectStoreView(LoginRequiredMixin, View):
    def post(self, request, store_id):
        store = get_object_or_404(Store, pk=store_id)
        if store.owner == request.user or StoreStaff.objects.filter(store=store, user=request.user).exists():
            request.session["current_store_id"] = store.pk
        return redirect("dashboard:home")


# ─── Products ──────────────────────────────────────────────
class ProductListView(StoreAccessMixin, ListView):
    template_name = "dashboard/product_list.html"
    context_object_name = "products"
    paginate_by = 25

    def get_queryset(self):
        qs = Product.objects.filter(store=self.request.current_store).prefetch_related("images", "variants")
        q = self.request.GET.get("q")
        if q:
            qs = qs.filter(Q(name__icontains=q) | Q(sku__icontains=q))
        status = self.request.GET.get("status")
        if status:
            qs = qs.filter(status=status)
        category = self.request.GET.get("category")
        if category:
            qs = qs.filter(categories__id=category)
        return qs.order_by("-created_at")

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["categories"] = Category.objects.filter(store=self.request.current_store)
        ctx["statuses"] = Product.Status.choices
        return ctx


class ProductCreateView(StoreAccessMixin, TemplateView):
    template_name = "dashboard/product_form.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["categories"] = Category.objects.filter(store=self.request.current_store)
        return ctx

    def post(self, request, *args, **kwargs):
        store = request.current_store
        product = Product.objects.create(
            store=store,
            name=request.POST.get("name", ""),
            description=request.POST.get("description", ""),
            sku=request.POST.get("sku", ""),
            status=request.POST.get("status", "draft"),
        )
        cats = request.POST.getlist("categories")
        if cats:
            product.categories.set(cats)

        # Create default variant
        price = request.POST.get("price", "0")
        stock = request.POST.get("stock", "0")
        ProductVariant.objects.create(
            product=product,
            name="پیش‌فرض",
            price=int(price) if price else 0,
            stock=int(stock) if stock else 0,
        )

        # Upload images
        for f in request.FILES.getlist("images"):
            ProductImage.objects.create(
                product=product,
                image=f,
                is_primary=not product.images.exists(),
            )

        return redirect("dashboard:product-edit", pk=product.pk)


class ProductEditView(StoreAccessMixin, TemplateView):
    template_name = "dashboard/product_form.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        product = get_object_or_404(
            Product, pk=self.kwargs["pk"], store=self.request.current_store
        )
        ctx["product"] = product
        ctx["categories"] = Category.objects.filter(store=self.request.current_store)
        ctx["selected_categories"] = list(product.categories.values_list("pk", flat=True))
        ctx["variants"] = product.variants.all()
        return ctx

    def post(self, request, pk, *args, **kwargs):
        product = get_object_or_404(Product, pk=pk, store=request.current_store)
        product.name = request.POST.get("name", product.name)
        product.description = request.POST.get("description", product.description)
        product.sku = request.POST.get("sku", product.sku)
        product.status = request.POST.get("status", product.status)
        product.meta_title = request.POST.get("meta_title", product.meta_title)
        product.meta_description = request.POST.get("meta_description", product.meta_description)
        slug = request.POST.get("slug", "").strip()
        if slug:
            product.slug = slug
        product.save()

        cats = request.POST.getlist("categories")
        product.categories.set(cats)

        # Update variants
        variant_ids = request.POST.getlist("variant_id")
        variant_names = request.POST.getlist("variant_name")
        variant_skus = request.POST.getlist("variant_sku")
        variant_prices = request.POST.getlist("variant_price")
        variant_compares = request.POST.getlist("variant_compare")
        variant_stocks = request.POST.getlist("variant_stock")
        variant_weights = request.POST.getlist("variant_weight")

        for i in range(len(variant_names)):
            vid = variant_ids[i] if i < len(variant_ids) else ""
            data = {
                "name": variant_names[i],
                "sku": variant_skus[i] if i < len(variant_skus) else "",
                "price": int(variant_prices[i]) if i < len(variant_prices) and variant_prices[i] else 0,
                "compare_at_price": int(variant_compares[i]) if i < len(variant_compares) and variant_compares[i] else None,
                "stock": int(variant_stocks[i]) if i < len(variant_stocks) and variant_stocks[i] else 0,
                "weight": variant_weights[i] if i < len(variant_weights) and variant_weights[i] else None,
            }
            if vid:
                ProductVariant.objects.filter(pk=vid, product=product).update(**data)
            else:
                ProductVariant.objects.create(product=product, **data)

        # Upload new images
        for f in request.FILES.getlist("images"):
            ProductImage.objects.create(
                product=product,
                image=f,
                is_primary=not product.images.exists(),
            )

        return redirect("dashboard:product-edit", pk=product.pk)


# ─── SO-15: Product Images (reorder, set-primary, delete) ──
class ProductImagesView(StoreAccessMixin, TemplateView):
    template_name = "dashboard/product_images.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        product = get_object_or_404(
            Product, pk=self.kwargs["pk"], store=self.request.current_store
        )
        ctx["product"] = product
        ctx["images"] = product.images.all()
        return ctx

    def post(self, request, pk, *args, **kwargs):
        product = get_object_or_404(Product, pk=pk, store=request.current_store)
        for f in request.FILES.getlist("images"):
            ProductImage.objects.create(
                product=product,
                image=f,
                is_primary=not product.images.exists(),
            )
        return redirect("dashboard:product-images", pk=pk)


class ProductImageReorderView(StoreAccessMixin, View):
    def post(self, request, pk):
        product = get_object_or_404(Product, pk=pk, store=request.current_store)
        try:
            order = json.loads(request.body)
            image_ids = order.get("order", [])
        except (json.JSONDecodeError, AttributeError):
            return JsonResponse({"error": "Invalid data"}, status=400)

        for idx, image_id in enumerate(image_ids):
            ProductImage.objects.filter(pk=image_id, product=product).update(sort_order=idx)

        return JsonResponse({"status": "ok"})


class ProductImageDeleteView(StoreAccessMixin, View):
    def post(self, request, pk, image_id):
        product = get_object_or_404(Product, pk=pk, store=request.current_store)
        image = get_object_or_404(ProductImage, pk=image_id, product=product)

        # Ensure at least one image for active products
        if product.status == "active" and product.images.count() <= 1:
            return JsonResponse({"error": "محصول فعال باید حداقل یک تصویر داشته باشد."}, status=400)

        was_primary = image.is_primary
        image.delete()

        # Promote next image to primary
        if was_primary:
            next_img = product.images.first()
            if next_img:
                next_img.is_primary = True
                next_img.save(update_fields=["is_primary"])

        return redirect("dashboard:product-images", pk=pk)


class ProductImageSetPrimaryView(StoreAccessMixin, View):
    def post(self, request, pk, image_id):
        product = get_object_or_404(Product, pk=pk, store=request.current_store)
        product.images.update(is_primary=False)
        ProductImage.objects.filter(pk=image_id, product=product).update(is_primary=True)
        return redirect("dashboard:product-images", pk=pk)


# ─── SO-14: Bulk Actions ──────────────────────────────────
class ProductBulkActionView(StoreAccessMixin, View):
    def post(self, request):
        store = request.current_store
        product_ids = request.POST.getlist("product_ids")
        action = request.POST.get("bulk_action")

        products = Product.objects.filter(pk__in=product_ids, store=store)

        if action == "activate":
            products.update(status="active")
        elif action == "draft":
            products.update(status="draft")
        elif action == "archive":
            products.update(status="archived")
        elif action == "change_category":
            cat_id = request.POST.get("category_id")
            if cat_id:
                cat = get_object_or_404(Category, pk=cat_id, store=store)
                for p in products:
                    p.categories.set([cat])
        elif action == "adjust_price":
            adjustment_type = request.POST.get("adjustment_type")  # "fixed" or "percent"
            amount = request.POST.get("amount", "0")
            try:
                amount = int(amount)
            except ValueError:
                amount = 0
            variants = ProductVariant.objects.filter(product__in=products)
            if adjustment_type == "fixed":
                variants.update(price=F("price") + amount)
            elif adjustment_type == "percent":
                for v in variants:
                    v.price = max(0, int(v.price * (1 + amount / 100)))
                    v.save(update_fields=["price"])
        elif action == "set_stock":
            stock_value = int(request.POST.get("stock_value", 0))
            ProductVariant.objects.filter(product__in=products).update(stock=stock_value)

        count = products.count()
        if count > 0:
            messages.success(request, f"{count} محصول به‌روزرسانی شد.")
        return redirect("dashboard:product-list")


# ─── Categories ────────────────────────────────────────────
class CategoryListView(StoreAccessMixin, ListView):
    template_name = "dashboard/category_list.html"
    context_object_name = "categories"

    def get_queryset(self):
        return Category.objects.filter(store=self.request.current_store)


class CategoryCreateView(StoreAccessMixin, TemplateView):
    template_name = "dashboard/category_form.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["categories"] = Category.objects.filter(store=self.request.current_store)
        return ctx

    def post(self, request, *args, **kwargs):
        store = request.current_store
        name = (request.POST.get("name") or "").strip()
        if not name:
            messages.error(request, "نام دسته‌بندی را وارد کنید.")
            return redirect("dashboard:category-create")
        parent_id = request.POST.get("parent_id") or ""
        parent = None
        if parent_id:
            parent = Category.objects.filter(pk=parent_id, store=store).first()
        description = (request.POST.get("description") or "").strip()
        slug = (request.POST.get("slug") or "").strip()
        Category.objects.create(
            store=store,
            parent=parent,
            name=name,
            slug=slug or slugify(name, allow_unicode=True),
            description=description,
        )
        messages.success(request, f"دسته‌بندی «{name}» اضافه شد.")
        return redirect("dashboard:category-list")


# ─── Orders ────────────────────────────────────────────────
class OrderListView(StoreAccessMixin, ListView):
    template_name = "dashboard/order_list.html"
    context_object_name = "orders"
    paginate_by = 25

    def get_queryset(self):
        qs = Order.objects.filter(store=self.request.current_store)
        status = self.request.GET.get("status")
        if status:
            qs = qs.filter(status=status)
        return qs


class OrderDetailView(StoreAccessMixin, TemplateView):
    template_name = "dashboard/order_detail.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["order"] = get_object_or_404(
            Order, pk=self.kwargs["pk"], store=self.request.current_store
        )
        return ctx


# ─── Accounting ────────────────────────────────────────────
class AccountingLedgerView(StoreAccessMixin, ListView):
    template_name = "dashboard/accounting_ledger.html"
    context_object_name = "transactions"
    paginate_by = 50

    def get_queryset(self):
        return self.request.current_store.transactions.all()

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        from accounting.services import get_store_balance
        ctx["balance"] = get_store_balance(self.request.current_store)
        return ctx


# ─── Store Settings ────────────────────────────────────────
class StoreSettingsView(StoreAccessMixin, TemplateView):
    template_name = "dashboard/store_settings.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["store"] = self.request.current_store
        return ctx

    def post(self, request, *args, **kwargs):
        store = request.current_store
        if store.owner != request.user:
            return redirect("dashboard:store-settings")

        store.name = request.POST.get("store_name", request.POST.get("name", store.name))
        store.description = request.POST.get("store_description", request.POST.get("description", store.description))
        store.phone = request.POST.get("phone", store.phone)
        store.support_email = request.POST.get("support_email", store.support_email)
        store.allow_guest_checkout = request.POST.get("allow_guest_checkout") == "on"
        if request.FILES.get("logo"):
            store.logo = request.FILES["logo"]

        # Editable username: normalize to slug and check availability
        raw_username = (request.POST.get("username") or "").strip().lower()
        if raw_username:
            slug = slugify(raw_username, allow_unicode=False)
            slug = "".join(c for c in slug if c.isalnum() or c == "-").strip("-") or None
            if not slug or len(slug) < 2:
                messages.error(request, "نام‌کاربری باید حداقل ۲ کاراکتر و فقط حروف انگلیسی، عدد و خط تیره باشد.")
                return redirect("dashboard:store-settings")
            if len(slug) > 60:
                messages.error(request, "نام‌کاربری نباید بیشتر از ۶۰ کاراکتر باشد.")
                return redirect("dashboard:store-settings")
            reserved = list(PlatformSettings.load().reserved_usernames or [])
            if slug in reserved:
                messages.error(request, "این نام‌کاربری رزرو شده و قابل استفاده نیست.")
                return redirect("dashboard:store-settings")
            if Store.objects.filter(username=slug).exclude(pk=store.pk).exists():
                messages.error(request, "این نام‌کاربری قبلاً انتخاب شده. یک نام دیگر وارد کنید.")
                return redirect("dashboard:store-settings")
            store.username = slug

        store.save()
        messages.success(request, "تنظیمات ذخیره شد.")
        return redirect("dashboard:store-settings")


# ─── SO-44: Theme Selection ─────────────────────────────────
class ThemeSelectView(StoreAccessMixin, TemplateView):
    template_name = "dashboard/theme_select.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["presets"] = ThemePreset.objects.filter(status=ThemePreset.Status.ACTIVE)
        theme, _ = StoreTheme.objects.get_or_create(store=self.request.current_store)
        ctx["current_theme"] = theme
        return ctx

    def post(self, request, *args, **kwargs):
        store = request.current_store
        preset_id = request.POST.get("preset_id")
        if preset_id:
            preset = get_object_or_404(ThemePreset, pk=preset_id, status=ThemePreset.Status.ACTIVE)
            theme, _ = StoreTheme.objects.get_or_create(store=store)
            theme.theme_preset = preset
            # Apply preset primary color if in tokens
            if "primary_color" in preset.tokens:
                theme.primary_color = preset.tokens["primary_color"]
            if "radius" in preset.tokens:
                theme.radius_scale = preset.tokens["radius"]
            if "shadow" in preset.tokens:
                theme.shadow_level = preset.tokens["shadow"]
            theme.version += 1
            theme.save()
            messages.success(request, f"پوسته «{preset.name}» با موفقیت اعمال شد.")
        return redirect("dashboard:theme-select")


# ─── SO-44: Theme Customization ──────────────────────────────
class ThemeCustomizeView(StoreAccessMixin, TemplateView):
    template_name = "dashboard/theme_customize.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        theme, _ = StoreTheme.objects.get_or_create(store=self.request.current_store)
        ctx["theme"] = theme
        ctx["radius_choices"] = StoreTheme.RadiusScale.choices
        ctx["shadow_choices"] = StoreTheme.ShadowLevel.choices
        ctx["primary_scale"] = generate_color_scale(theme.primary_color)
        ctx["contrast_warnings"] = validate_contrast(theme)
        return ctx

    def post(self, request, *args, **kwargs):
        store = request.current_store
        theme, _ = StoreTheme.objects.get_or_create(store=store)
        theme.primary_color = request.POST.get("primary_color", theme.primary_color)
        theme.secondary_color = request.POST.get("secondary_color", theme.secondary_color)
        theme.accent_color = request.POST.get("accent_color", theme.accent_color)
        theme.heading_font = request.POST.get("heading_font", theme.heading_font)
        theme.body_font = request.POST.get("body_font", theme.body_font)
        theme.radius_scale = request.POST.get("radius_scale", theme.radius_scale)
        theme.shadow_level = request.POST.get("shadow_level", theme.shadow_level)
        theme.version += 1
        theme.save()
        messages.success(request, "تنظیمات ظاهری با موفقیت ذخیره شد.")
        return redirect("dashboard:theme-customize")


# ─── SO-48: Custom CSS ────────────────────────────────────────
class ThemeCustomCSSView(StoreAccessMixin, TemplateView):
    template_name = "dashboard/theme_custom_css.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        theme, _ = StoreTheme.objects.get_or_create(store=self.request.current_store)
        ctx["theme"] = theme
        css_bytes = len(theme.custom_css.encode("utf-8"))
        ctx["css_size"] = css_bytes
        ctx["css_size_kb"] = round(css_bytes / 1024, 1)
        return ctx

    def post(self, request, *args, **kwargs):
        store = request.current_store
        theme, _ = StoreTheme.objects.get_or_create(store=store)
        raw_css = request.POST.get("custom_css", "")
        sanitized, warnings = sanitize_css(raw_css)
        if len(sanitized.encode("utf-8")) > 50 * 1024:
            messages.error(request, "CSS بیش از ۵۰ کیلوبایت است. لطفاً حجم آن را کاهش دهید.")
            return redirect("dashboard:theme-custom-css")
        theme.custom_css = sanitized
        theme.version += 1
        theme.save()
        for w in warnings:
            messages.warning(request, w)
        messages.success(request, "CSS سفارشی با موفقیت ذخیره شد.")
        return redirect("dashboard:theme-custom-css")
