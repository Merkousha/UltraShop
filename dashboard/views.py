import json
import logging

from django.contrib import messages
from core.encryption import encrypt_value
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Q, F
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect
from django.utils import timezone
from django.utils.text import slugify
from django.views import View
from django.views.generic import ListView, TemplateView

from catalog.models import Category, Product, ProductImage, ProductVariant, WarehouseStock
from core.blocks import (
    BLOCK_REGISTRY,
    get_block_by_id,
    get_default_block_order,
    get_block_type_id,
    get_instance_number,
    next_instance_id,
)
from core.models import (
    LayoutConfiguration,
    LayoutConfigurationSnapshot,
    PlatformSettings,
    Store,
    StoreIntegration,
    StoreStaff,
    StoreTheme,
    ThemePreset,
    Warehouse,
)
from core.warehouse_service import (
    get_default_warehouse,
    get_warehouses_for_user,
    MAX_WAREHOUSES_PER_STORE,
    set_default_warehouse_quantity,
)
from core.theme_service import generate_color_scale, validate_contrast
from core.css_sanitizer import sanitize_css
from orders.models import Order

from core.ai_service import (
    AIError,
    get_ai_usage_today,
    is_ai_available_for_store,
    onboarding_suggest_theme,
    text_generate_brand_identity,
    text_generate_seo,
    vision_extract_product,
)


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

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        store = self.request.current_store
        user = self.request.user
        if store.owner == user:
            ctx["current_role"] = "owner"
        else:
            staff = StoreStaff.objects.filter(store=store, user=user).first()
            ctx["current_role"] = staff.role if staff else "staff"
        return ctx


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
        ctx["ai_available"] = is_ai_available_for_store(self.request.current_store)
        ctx["ai_usage"] = get_ai_usage_today(self.request.current_store)
        return ctx


class ProductFromImageView(StoreAccessMixin, TemplateView):
    """SO-16: Upload image → Vision API → pre-fill product create form."""
    template_name = "dashboard/product_from_image.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["ai_available"] = is_ai_available_for_store(self.request.current_store)
        ctx["ai_usage"] = get_ai_usage_today(self.request.current_store)
        return ctx

    def post(self, request, *args, **kwargs):
        store = request.current_store
        if not is_ai_available_for_store(store):
            messages.error(request, "سرویس AI غیرفعال یا اعتبار روزانه تمام شده است.")
            return redirect("dashboard:product-from-image")
        image_file = request.FILES.get("image")
        if not image_file:
            messages.error(request, "لطفاً یک تصویر انتخاب کنید.")
            return redirect("dashboard:product-from-image")
        try:
            import base64
            data = image_file.read()
            if len(data) > 10 * 1024 * 1024:  # 10 MB
                messages.error(request, "حجم تصویر بیش از ۱۰ مگابایت است.")
                return redirect("dashboard:product-from-image")
            b64 = base64.b64encode(data).decode("ascii")
            result = vision_extract_product(b64, store)
            request.session["vision_prefill"] = result
            return redirect("dashboard:product-create")
        except AIError as e:
            messages.error(request, e.user_message)
            return redirect("dashboard:product-from-image")
        except Exception as e:
            messages.error(request, "خطای غیرمنتظره. لطفاً دوباره امتحان کنید.")
            return redirect("dashboard:product-from-image")


class ProductCreateView(StoreAccessMixin, TemplateView):
    template_name = "dashboard/product_form.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        store = self.request.current_store
        ctx["categories"] = Category.objects.filter(store=store)
        ctx["product"] = None
        ctx["selected_categories"] = []
        ctx["variants"] = []
        vision_prefill = self.request.session.pop("vision_prefill", None)
        ctx["vision_prefill"] = vision_prefill
        ctx["seo_prefill"] = None
        ctx["ai_available"] = is_ai_available_for_store(store)
        if vision_prefill and vision_prefill.get("category_suggestion"):
            suggestion = vision_prefill["category_suggestion"]
            suggested = list(
                Category.objects.filter(store=store, name__icontains=suggestion).values_list("pk", flat=True)
            )
            ctx["selected_categories"] = suggested[:5]
        return ctx

    def post(self, request, *args, **kwargs):
        store = request.current_store
        product = Product.objects.create(
            store=store,
            name=request.POST.get("name", ""),
            description=request.POST.get("description", ""),
            sku=request.POST.get("sku", ""),
            status=request.POST.get("status", "draft"),
            requires_shipping=request.POST.get("requires_shipping") == "on",
        )
        cats = request.POST.getlist("categories")
        if cats:
            product.categories.set(cats)

        # Create default variant
        price = request.POST.get("price", "0")
        stock_val = int(stock) if (stock := request.POST.get("stock", "0")) else 0
        variant = ProductVariant.objects.create(
            product=product,
            name="پیش‌فرض",
            price=int(price) if price else 0,
            stock=stock_val,
        )
        set_default_warehouse_quantity(store, variant, stock_val)

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
        ctx["ai_available"] = is_ai_available_for_store(self.request.current_store)
        ctx["ai_usage"] = get_ai_usage_today(self.request.current_store)
        ctx["seo_prefill"] = self.request.session.pop("seo_prefill", None)
        return ctx

    def post(self, request, pk, *args, **kwargs):
        product = get_object_or_404(Product, pk=pk, store=request.current_store)
        product.name = request.POST.get("name", product.name)
        product.description = request.POST.get("description", product.description)
        product.sku = request.POST.get("sku", product.sku)
        product.status = request.POST.get("status", product.status)
        product.meta_title = request.POST.get("meta_title", product.meta_title)
        product.meta_description = request.POST.get("meta_description", product.meta_description)
        product.focus_keywords = request.POST.get("focus_keywords", product.focus_keywords)
        product.og_description = request.POST.get("og_description", product.og_description)
        product.requires_shipping = request.POST.get("requires_shipping") == "on"
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

        default_wh = get_default_warehouse(request.current_store)
        for i in range(len(variant_names)):
            vid = variant_ids[i] if i < len(variant_ids) else ""
            stock_val = int(variant_stocks[i]) if i < len(variant_stocks) and variant_stocks[i] else 0
            data = {
                "name": variant_names[i],
                "sku": variant_skus[i] if i < len(variant_skus) else "",
                "price": int(variant_prices[i]) if i < len(variant_prices) and variant_prices[i] else 0,
                "compare_at_price": int(variant_compares[i]) if i < len(variant_compares) and variant_compares[i] else None,
                "stock": stock_val,
                "weight": variant_weights[i] if i < len(variant_weights) and variant_weights[i] else None,
            }
            if vid:
                v = ProductVariant.objects.filter(pk=vid, product=product).first()
                if v:
                    ProductVariant.objects.filter(pk=vid, product=product).update(**data)
                    set_default_warehouse_quantity(request.current_store, v, stock_val)
            else:
                v = ProductVariant.objects.create(product=product, **data)
                set_default_warehouse_quantity(request.current_store, v, stock_val)

        # Upload new images
        for f in request.FILES.getlist("images"):
            ProductImage.objects.create(
                product=product,
                image=f,
                is_primary=not product.images.exists(),
            )

        return redirect("dashboard:product-edit", pk=product.pk)


class ProductGenerateSEOView(StoreAccessMixin, View):
    """SO-17: Generate SEO fields via AI (JSON response for AJAX)."""
    def post(self, request, pk, *args, **kwargs):
        product = get_object_or_404(Product, pk=pk, store=request.current_store)
        if not is_ai_available_for_store(request.current_store):
            return JsonResponse(
                {"error": "سرویس AI غیرفعال یا اعتبار روزانه تمام شده است."},
                status=400,
            )
        category_names = list(product.categories.values_list("name", flat=True))
        try:
            result = text_generate_seo(
                name=product.name,
                description=product.description or "",
                category_names=category_names,
                lang="fa-IR",
                store=request.current_store,
            )
            return JsonResponse(result)
        except AIError as e:
            return JsonResponse({"error": e.user_message}, status=400)
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)


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
            for variant in ProductVariant.objects.filter(product__in=products):
                set_default_warehouse_quantity(request.current_store, variant, stock_value)
        elif action == "generate_seo":
            used, limit = get_ai_usage_today(store)
            plist = list(products)
            if used + len(plist) > limit:
                messages.error(
                    request,
                    f"اعتبار AI کافی نیست. امروز {used}/{limit} استفاده شده؛ برای {len(plist)} محصول به {len(plist)} درخواست دیگر نیاز است.",
                )
                return redirect("dashboard:product-list")
            done = 0
            for product in plist:
                try:
                    cat_names = list(product.categories.values_list("name", flat=True))
                    result = text_generate_seo(
                        product.name,
                        product.description or "",
                        cat_names,
                        "fa-IR",
                        store,
                    )
                    product.meta_title = result.get("meta_title", "")[:200]
                    product.meta_description = result.get("meta_description", "")[:500]
                    product.focus_keywords = result.get("focus_keywords", "")[:500]
                    product.og_description = result.get("og_description", "")[:1000]
                    product.save(update_fields=["meta_title", "meta_description", "focus_keywords", "og_description"])
                    done += 1
                except AIError:
                    pass
                except Exception:
                    pass
            if done:
                messages.success(request, f"SEO برای {done} محصول با AI تولید شد.")
            else:
                messages.error(request, "خطا در تولید SEO یا اعتبار AI تمام شده.")
            return redirect("dashboard:product-list")

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


# ─── Sprint 4: Warehouses (SO-50, SS-13) ─────────────────────
class WarehouseListView(StoreAccessMixin, ListView):
    template_name = "dashboard/warehouse_list.html"
    context_object_name = "warehouses"

    def get_queryset(self):
        return get_warehouses_for_user(self.request.current_store, self.request.user)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        store = self.request.current_store
        ctx["max_warehouses"] = MAX_WAREHOUSES_PER_STORE
        ctx["can_add"] = (
            store.owner == self.request.user
            and Warehouse.objects.filter(store=store).count() < MAX_WAREHOUSES_PER_STORE
        )
        return ctx


class WarehouseCreateView(StoreAccessMixin, TemplateView):
    template_name = "dashboard/warehouse_form.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["warehouse"] = None
        ctx["is_edit"] = False
        return ctx

    def post(self, request, *args, **kwargs):
        store = request.current_store
        if store.owner_id != request.user.id:
            messages.error(request, "فقط مالک فروشگاه می‌تواند انبار جدید اضافه کند.")
            return redirect("dashboard:warehouse-list")
        from core.services import check_plan_limit, PlanLimitExceeded
        current_count = Warehouse.objects.filter(store=store).count()
        try:
            check_plan_limit(store, "warehouses", current_count)
        except PlanLimitExceeded as e:
            messages.error(request, str(e))
            return redirect("dashboard:warehouse-list")
        name = (request.POST.get("name") or "").strip()
        if not name:
            messages.error(request, "نام انبار را وارد کنید.")
            return redirect("dashboard:warehouse-add")
        is_first = not Warehouse.objects.filter(store=store).exists()
        Warehouse.objects.create(
            store=store,
            name=name,
            address=(request.POST.get("address") or "").strip(),
            city=(request.POST.get("city") or "").strip(),
            province=(request.POST.get("province") or "").strip(),
            postal_code=(request.POST.get("postal_code") or "").strip(),
            phone=(request.POST.get("phone") or "").strip(),
            is_default=is_first,
            priority=int(request.POST.get("priority") or 0),
        )
        messages.success(request, f"انبار «{name}» اضافه شد.")
        return redirect("dashboard:warehouse-list")


class WarehouseEditView(StoreAccessMixin, TemplateView):
    template_name = "dashboard/warehouse_form.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        warehouse = get_object_or_404(
            Warehouse, pk=self.kwargs["pk"], store=self.request.current_store
        )
        if not get_warehouses_for_user(self.request.current_store, self.request.user).filter(pk=warehouse.pk).exists():
            from django.http import Http404
            raise Http404
        ctx["warehouse"] = warehouse
        ctx["is_edit"] = True
        return ctx

    def post(self, request, pk, *args, **kwargs):
        warehouse = get_object_or_404(Warehouse, pk=pk, store=request.current_store)
        if not get_warehouses_for_user(request.current_store, request.user).filter(pk=warehouse.pk).exists():
            from django.http import Http404
            raise Http404
        name = (request.POST.get("name") or "").strip()
        if not name:
            messages.error(request, "نام انبار را وارد کنید.")
            return redirect("dashboard:warehouse-edit", pk=pk)
        warehouse.name = name
        warehouse.address = (request.POST.get("address") or "").strip()
        warehouse.city = (request.POST.get("city") or "").strip()
        warehouse.province = (request.POST.get("province") or "").strip()
        warehouse.postal_code = (request.POST.get("postal_code") or "").strip()
        warehouse.phone = (request.POST.get("phone") or "").strip()
        warehouse.is_active = request.POST.get("is_active") == "on"
        warehouse.priority = int(request.POST.get("priority") or 0)
        if request.POST.get("is_default") == "on":
            Warehouse.objects.filter(store=warehouse.store).update(is_default=False)
            warehouse.is_default = True
        warehouse.save()
        messages.success(request, f"انبار «{name}» به‌روزرسانی شد.")
        return redirect("dashboard:warehouse-list")


class WarehouseInventoryView(StoreAccessMixin, TemplateView):
    """SO-51: Per-warehouse stock list (SS-13: only allowed warehouses)."""
    template_name = "dashboard/warehouse_inventory.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        warehouse = get_object_or_404(Warehouse, pk=self.kwargs["pk"], store=self.request.current_store)
        if not get_warehouses_for_user(self.request.current_store, self.request.user).filter(pk=warehouse.pk).exists():
            from django.http import Http404
            raise Http404
        ctx["warehouse"] = warehouse
        ctx["stock_lines"] = (
            WarehouseStock.objects.filter(warehouse=warehouse)
            .select_related("variant", "variant__product")
            .order_by("variant__product__name", "variant__name")
        )
        return ctx


class StockTransferView(StoreAccessMixin, TemplateView):
    """SO-51: Transfer stock between warehouses."""
    template_name = "dashboard/stock_transfer.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["warehouses"] = get_warehouses_for_user(self.request.current_store, self.request.user)
        ctx["variants"] = ProductVariant.objects.filter(
            product__store=self.request.current_store
        ).select_related("product").order_by("product__name", "name")
        return ctx

    def post(self, request, *args, **kwargs):
        store = request.current_store
        warehouses_qs = get_warehouses_for_user(store, request.user)
        from_id = request.POST.get("from_warehouse")
        to_id = request.POST.get("to_warehouse")
        variant_id = request.POST.get("variant_id")
        qty = int(request.POST.get("quantity") or 0)
        if not from_id or not to_id or from_id == to_id or not variant_id or qty <= 0:
            messages.error(request, "ورودی‌ها را بررسی کنید (انبار مبدأ و مقصد متفاوت، تعداد مثبت).")
            return redirect("dashboard:stock-transfer")
        from_wh = get_object_or_404(Warehouse, pk=from_id, store=store)
        to_wh = get_object_or_404(Warehouse, pk=to_id, store=store)
        allowed_ids = set(warehouses_qs.values_list("pk", flat=True))
        if from_wh.pk not in allowed_ids or to_wh.pk not in allowed_ids:
            messages.error(request, "دسترسی به یکی از انبارها مجاز نیست.")
            return redirect("dashboard:stock-transfer")
        variant = get_object_or_404(
            ProductVariant, pk=variant_id, product__store=store
        )
        from_ws = WarehouseStock.objects.filter(
            warehouse=from_wh, variant=variant
        ).first()
        if not from_ws or from_ws.available < qty:
            messages.error(request, "موجودی کافی در انبار مبدأ نیست.")
            return redirect("dashboard:stock-transfer")
        to_ws, _ = WarehouseStock.objects.get_or_create(
            warehouse=to_wh, variant=variant, defaults={"quantity": 0}
        )
        from_ws.quantity -= qty
        to_ws.quantity += qty
        from_ws.save(update_fields=["quantity"])
        to_ws.save(update_fields=["quantity"])
        from django.db.models import Sum
        agg = variant.warehouse_stocks.aggregate(s=Sum("quantity"), r=Sum("reserved"))
        variant.stock = max(0, (agg["s"] or 0) - (agg["r"] or 0))
        variant.save(update_fields=["stock"])
        messages.success(request, f"{qty} عدد از «{variant.product.name} — {variant.name}» به انبار «{to_wh.name}» منتقل شد.")
        return redirect("dashboard:warehouse-inventory", pk=to_wh.pk)


class StaffWarehouseAssignmentView(StoreAccessMixin, TemplateView):
    """SS-13: Owner assigns which warehouses each staff can access."""
    template_name = "dashboard/staff_warehouses.html"

    def dispatch(self, request, *args, **kwargs):
        if request.current_store.owner_id != request.user.id:
            messages.error(request, "فقط مالک فروشگاه می‌تواند دسترسی انبار استاف را تنظیم کند.")
            return redirect("dashboard:warehouse-list")
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["staff_list"] = StoreStaff.objects.filter(store=self.request.current_store).prefetch_related("warehouses")
        ctx["warehouses"] = Warehouse.objects.filter(store=self.request.current_store)
        return ctx

    def post(self, request, *args, **kwargs):
        store = request.current_store
        if store.owner_id != request.user.id:
            return redirect("dashboard:warehouse-list")
        staff_id = request.POST.get("staff_id")
        warehouse_ids = request.POST.getlist("warehouse_ids")
        if staff_id:
            staff = StoreStaff.objects.filter(pk=staff_id, store=store).first()
            if staff:
                staff.warehouses.set(
                    Warehouse.objects.filter(pk__in=warehouse_ids, store=store)
                )
                messages.success(request, "دسترسی انبار استاف به‌روزرسانی شد.")
        return redirect("dashboard:staff-warehouses")


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
        ctx["active_tab"] = self.request.GET.get("tab", "general")
        return ctx

    def post(self, request, *args, **kwargs):
        store = request.current_store
        if store.owner != request.user:
            return redirect("dashboard:store-settings")

        tab = request.POST.get("tab", "general")

        if tab == "email":
            store.email_from = request.POST.get("email_from", store.email_from).strip()
            store.email_host = request.POST.get("email_host", store.email_host).strip()
            try:
                store.email_port = int(request.POST.get("email_port", store.email_port))
            except (ValueError, TypeError):
                store.email_port = 587
            store.email_username = request.POST.get("email_username", store.email_username).strip()
            new_password = request.POST.get("email_password", "").strip()
            if new_password:
                store.email_password_encrypted = encrypt_value(new_password)
            store.email_use_tls = request.POST.get("email_use_tls") == "on"
            store.save()
            messages.success(request, "تنظیمات ایمیل ذخیره شد.")
            return redirect(f"{request.path}?tab=email")

        elif tab == "sms":
            store.sms_provider = request.POST.get("sms_provider", store.sms_provider).strip()
            new_api_key = request.POST.get("sms_api_key", "").strip()
            if new_api_key:
                store.sms_api_key_encrypted = encrypt_value(new_api_key)
            store.sms_sender = request.POST.get("sms_sender", store.sms_sender).strip()
            store.save()
            messages.success(request, "تنظیمات پیامک ذخیره شد.")
            return redirect(f"{request.path}?tab=sms")

        else:
            # general tab — existing behaviour preserved exactly
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


# ─── SO-06: Onboarding Wizard ─────────────────────────────────
ONBOARDING_SESSION_KEY = "onboarding_wizard"


class OnboardingWizardView(StoreAccessMixin, TemplateView):
    """Multi-step onboarding: business info → AI suggestion → confirm/apply → first product."""
    template_name = "dashboard/onboarding_step1.html"

    def _session(self, request):
        if ONBOARDING_SESSION_KEY not in request.session:
            request.session[ONBOARDING_SESSION_KEY] = {"step": 1, "data": {}, "suggestion": None}
        return request.session[ONBOARDING_SESSION_KEY]

    def get_template_names(self):
        step = self._session(self.request).get("step", 1)
        return [f"dashboard/onboarding_step{step}.html"]

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        sess = self._session(self.request)
        ctx["onboarding"] = sess
        ctx["step"] = sess.get("step", 1)
        ctx["data"] = sess.get("data") or {}
        ctx["suggestion"] = sess.get("suggestion")
        ctx["presets"] = ThemePreset.objects.filter(status=ThemePreset.Status.ACTIVE)
        ctx["preset_slugs"] = list(ctx["presets"].values_list("slug", flat=True))
        ctx["block_ids"] = get_default_block_order()
        ctx["ai_available"] = is_ai_available_for_store(self.request.current_store)
        return ctx

    def post(self, request, *args, **kwargs):
        sess = self._session(request)
        step = sess.get("step", 1)
        store = request.current_store

        if step == 1:
            sess["data"] = {
                "business_type": request.POST.get("business_type", "").strip(),
                "brand_name": request.POST.get("brand_name", "").strip(),
                "slogan": request.POST.get("slogan", "").strip(),
                "audience": request.POST.get("audience", "").strip(),
                "style": request.POST.get("style", "").strip(),
                "favorite_color": request.POST.get("favorite_color", "").strip(),
            }
            if request.POST.get("skip_ai"):
                sess["step"] = 3
                sess["suggestion"] = None
                request.session.modified = True
                return redirect("dashboard:theme-select")
            sess["step"] = 2
            request.session.modified = True
            return redirect("dashboard:onboarding")

        if step == 2:
            if request.POST.get("run_ai") and is_ai_available_for_store(store):
                data = sess.get("data") or {}
                preset_slugs = list(ThemePreset.objects.filter(status=ThemePreset.Status.ACTIVE).values_list("slug", flat=True))
                block_ids = get_default_block_order()
                try:
                    suggestion = onboarding_suggest_theme(
                        business_type=data.get("business_type", ""),
                        brand_name=data.get("brand_name", ""),
                        slogan=data.get("slogan", ""),
                        audience=data.get("audience", ""),
                        style=data.get("style", ""),
                        favorite_color=data.get("favorite_color", ""),
                        store=store,
                        preset_slugs=preset_slugs,
                        block_ids=block_ids,
                    )
                    sess["suggestion"] = suggestion
                    sess["step"] = 3
                except AIError as e:
                    messages.error(request, e.user_message)
            else:
                sess["step"] = 3
                sess["suggestion"] = None
            request.session.modified = True
            return redirect("dashboard:onboarding")

        if step == 3:
            if request.POST.get("apply"):
                suggestion = sess.get("suggestion")
                if suggestion:
                    preset = ThemePreset.objects.filter(slug=suggestion["theme_slug"], status=ThemePreset.Status.ACTIVE).first()
                    theme, _ = StoreTheme.objects.get_or_create(store=store)
                    if preset:
                        theme.theme_preset = preset
                    theme.primary_color = suggestion.get("primary_color", theme.primary_color)
                    theme.secondary_color = suggestion.get("secondary_color", theme.secondary_color)
                    theme.accent_color = suggestion.get("accent_color", theme.accent_color)
                    theme.version += 1
                    theme.save()
                    layout, _ = LayoutConfiguration.objects.get_or_create(
                        store=store, page_type=LayoutConfiguration.PageType.HOME,
                        defaults={"block_order": get_default_block_order(), "block_settings": {}, "block_enabled": {}},
                    )
                    layout.block_order = suggestion.get("block_order", layout.block_order)
                    layout.block_enabled = {bid: True for bid in layout.block_order}
                    layout.save()
                data = sess.get("data") or {}
                if data.get("brand_name"):
                    store.name = data["brand_name"][:200]
                    store.save(update_fields=["name"])
                sess["step"] = 4
                request.session.modified = True
                messages.success(request, "تنظیمات اعمال شد. می‌توانید اولین محصول را اضافه کنید.")
                return redirect("dashboard:onboarding")
            if request.POST.get("start_from_scratch"):
                sess["step"] = 1
                sess["data"] = {}
                sess["suggestion"] = None
                request.session.modified = True
                return redirect("dashboard:theme-select")

        if step == 4:
            if request.POST.get("done"):
                request.session.pop(ONBOARDING_SESSION_KEY, None)
                return redirect("dashboard:home")

        return redirect("dashboard:onboarding")


# ─── SO-07: Brand Identity (AI) ─────────────────────────────────
class BrandIdentityView(StoreAccessMixin, TemplateView):
    """Generate tagline and brand story with AI; apply to store."""
    template_name = "dashboard/brand_identity.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        store = self.request.current_store
        ctx["store"] = store
        ctx["ai_available"] = is_ai_available_for_store(store)
        ctx["ai_usage"] = get_ai_usage_today(store)
        prefill = self.request.session.pop("brand_identity_prefill", None)
        ctx["tagline"] = prefill.get("tagline", store.tagline) if prefill else store.tagline
        ctx["brand_story"] = prefill.get("brand_story", store.description) if prefill else store.description
        return ctx

    def post(self, request, *args, **kwargs):
        store = request.current_store
        if request.POST.get("generate") and is_ai_available_for_store(store):
            try:
                result = text_generate_brand_identity(
                    brand_name=request.POST.get("brand_name", store.name),
                    business_type=request.POST.get("business_type", ""),
                    style=request.POST.get("style", ""),
                    base_color=request.POST.get("base_color", ""),
                    store=store,
                )
                request.session["brand_identity_prefill"] = result
            except AIError as e:
                messages.error(request, e.user_message)
        elif request.POST.get("apply"):
            store.tagline = (request.POST.get("tagline") or "")[:300]
            store.description = request.POST.get("description", store.description)[:5000]
            store.save(update_fields=["tagline", "description"])
            messages.success(request, "هویت برند روی فروشگاه اعمال شد.")
        return redirect("dashboard:brand-identity")


# ─── SO-46: Block Page Editor ─────────────────────────────────
class PageEditorView(StoreAccessMixin, TemplateView):
    template_name = "dashboard/page_editor.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        store = self.request.current_store
        try:
            layout = LayoutConfiguration.objects.get(store=store, page_type=LayoutConfiguration.PageType.HOME)
        except LayoutConfiguration.DoesNotExist:
            layout = LayoutConfiguration(
                store=store,
                page_type=LayoutConfiguration.PageType.HOME,
                block_order=get_default_block_order(),
                block_settings={},
                block_enabled={b["id"]: True for b in BLOCK_REGISTRY},
            )
        order = layout.block_order or get_default_block_order()
        enabled_map = layout.block_enabled or {}
        settings_map = layout.block_settings or {}
        types_in_order = {get_block_type_id(bid) for bid in order}

        def _settings_for_display(defaults, saved):
            out = {}
            merged = {**defaults, **(saved or {})}
            for k, v in merged.items():
                if isinstance(v, (list, dict)):
                    out[k] = json.dumps(v, ensure_ascii=False)
                else:
                    out[k] = v if v is not None else ""
            return out

        layout_blocks = []
        for bid in order:
            meta = get_block_by_id(bid)
            if not meta:
                continue
            defaults = meta.get("default_settings") or {}
            instance_num = get_instance_number(bid)
            label = meta["label"] + (f" ({instance_num})" if instance_num > 1 else "")
            layout_blocks.append({
                "id": bid,
                "label": label,
                "enabled": enabled_map.get(bid, True),
                "settings": _settings_for_display(defaults, settings_map.get(bid)),
                "block_id_safe": bid.replace("_", "-"),
            })
        for b in BLOCK_REGISTRY:
            if b["id"] not in types_in_order:
                defaults = b.get("default_settings") or {}
                layout_blocks.append({
                    "id": b["id"],
                    "label": b["label"],
                    "enabled": enabled_map.get(b["id"], True),
                    "settings": _settings_for_display(defaults, settings_map.get(b["id"])),
                    "block_id_safe": b["id"].replace("_", "-"),
                })
        ctx["layout"] = layout
        ctx["layout_blocks"] = layout_blocks
        ctx["store_username"] = store.username
        ctx["block_types"] = [{"id": b["id"], "label": b["label"]} for b in BLOCK_REGISTRY]
        setting_labels = {
            "title": "عنوان",
            "subtitle": "زیرعنوان",
            "cta_text": "متن دکمه",
            "cta_url": "لینک دکمه",
            "image": "آدرس تصویر",
            "columns": "تعداد ستون",
            "limit": "تعداد محصول",
            "link": "لینک",
            "alt": "متن جایگزین تصویر",
            "button_text": "متن دکمه",
            "html": "HTML سفارشی",
            "items": "آیتم‌ها (JSON)",
        }
        for lb in layout_blocks:
            meta = get_block_by_id(lb["id"])
            items_schema = (meta or {}).get("items_schema")
            if items_schema:
                lb["items_schema"] = items_schema
                merged = {**(meta.get("default_settings") or {}), **(settings_map.get(lb["id"]) or {})}
                raw_items = merged.get("items")
                items_list = raw_items if isinstance(raw_items, list) else []
                # Pad to 10 slots so user can add items without JS; each row is [(key, label, value), ...]
                padded = (items_list + [{}] * 10)[:10]
                lb["items_display"] = []
                for it in padded:
                    row = []
                    for f in items_schema:
                        val = it.get(f["key"], "") if isinstance(it, dict) else ""
                        if isinstance(val, str):
                            pass
                        else:
                            val = str(val) if val is not None else ""
                        row.append((f["key"], f["label"], val))
                    lb["items_display"].append(row)
                lb["settings_list"] = [(setting_labels.get(k, k), k, v) for k, v in lb["settings"].items() if k != "items"]
            else:
                lb["items_schema"] = None
                lb["items_list"] = []
                lb["settings_list"] = [(setting_labels.get(k, k), k, v) for k, v in lb["settings"].items()]
        snapshots = LayoutConfigurationSnapshot.objects.filter(
            store=store, page_type=LayoutConfiguration.PageType.HOME
        ).order_by("-version")[:10]
        ctx["snapshots"] = snapshots
        return ctx

    def post(self, request, *args, **kwargs):
        store = request.current_store
        order_raw = request.POST.get("block_order", "")
        block_order = [x.strip() for x in order_raw.split(",") if x.strip()]
        block_order = block_order or get_default_block_order()
        block_enabled = {}
        for bid in block_order:
            block_enabled[bid] = request.POST.get("enabled_" + bid) == "on"
        block_settings = {}
        # Collect item-based keys: setting_{block_id_safe}_item_{index}_{field}
        items_by_block = {}
        for key, value in request.POST.items():
            if key.startswith("setting_") and "_item_" in key:
                rest = key.replace("setting_", "", 1)
                if "_item_" not in rest:
                    continue
                safe_id, tail = rest.split("_item_", 1)
                block_id = safe_id.replace("-", "_")
                parts = tail.split("_", 1)
                if len(parts) == 2:
                    try:
                        idx = int(parts[0])
                        field = parts[1]
                        items_by_block.setdefault(block_id, {}).setdefault(idx, {})[field] = value
                    except ValueError:
                        pass
                continue
            if key.startswith("setting_") and "_" in key:
                parts = key.replace("setting_", "", 1).split("_", 1)
                if len(parts) == 2:
                    block_id = parts[0].replace("-", "_")
                    setting_key = parts[1]
                    if setting_key == "items":
                        continue
                    block_settings.setdefault(block_id, {})[setting_key] = value
        for block_id, indices_map in items_by_block.items():
            max_i = max(indices_map.keys()) if indices_map else -1
            items_list = []
            for i in range(max_i + 1):
                row = indices_map.get(i, {})
                if any(v and str(v).strip() for v in row.values()):
                    items_list.append(row)
            block_settings.setdefault(block_id, {})["items"] = items_list
        layout, _ = LayoutConfiguration.objects.get_or_create(
            store=store,
            page_type=LayoutConfiguration.PageType.HOME,
            defaults={"block_order": get_default_block_order(), "block_settings": {}, "block_enabled": {}},
        )
        layout.block_order = block_order
        layout.block_settings = {**layout.block_settings, **block_settings}
        layout.block_enabled = block_enabled
        layout.save()
        messages.success(request, "چیدمان ذخیره شد. برای اعمال روی فروشگاه «انتشار» را بزنید.")
        return redirect("dashboard:page-editor")


class PageEditorAddBlockView(StoreAccessMixin, View):
    """Add another instance of a block type (e.g. second banner). POST: block_type_id."""
    def post(self, request, *args, **kwargs):
        store = request.current_store
        block_type_id = (request.POST.get("block_type_id") or "").strip()
        if not block_type_id or not get_block_by_id(block_type_id):
            messages.error(request, "نوع بلوک نامعتبر است.")
            return redirect("dashboard:page-editor")
        layout, _ = LayoutConfiguration.objects.get_or_create(
            store=store,
            page_type=LayoutConfiguration.PageType.HOME,
            defaults={"block_order": get_default_block_order(), "block_settings": {}, "block_enabled": {}},
        )
        order = list(layout.block_order or get_default_block_order())
        new_id = next_instance_id(block_type_id, order)
        order.append(new_id)
        layout.block_order = order
        layout.block_enabled = {**layout.block_enabled, new_id: True}
        meta = get_block_by_id(block_type_id)
        if meta and meta.get("default_settings"):
            layout.block_settings = {**layout.block_settings, new_id: dict(meta["default_settings"])}
        layout.save()
        messages.success(request, f"بلوک «{meta.get('label', new_id)}» اضافه شد. ذخیره و انتشار را بزنید.")
        return redirect("dashboard:page-editor")


class PageEditorRemoveBlockView(StoreAccessMixin, View):
    """Remove one block instance from the layout. POST: block_id."""
    def post(self, request, *args, **kwargs):
        store = request.current_store
        block_id = (request.POST.get("block_id") or "").strip()
        if not block_id:
            return redirect("dashboard:page-editor")
        try:
            layout = LayoutConfiguration.objects.get(store=store, page_type=LayoutConfiguration.PageType.HOME)
        except LayoutConfiguration.DoesNotExist:
            return redirect("dashboard:page-editor")
        order = list(layout.block_order or [])
        if block_id in order:
            order.remove(block_id)
            layout.block_order = order
            enabled = dict(layout.block_enabled or {})
            enabled.pop(block_id, None)
            layout.block_enabled = enabled
            settings = dict(layout.block_settings or {})
            settings.pop(block_id, None)
            layout.block_settings = settings
            layout.save()
            messages.success(request, "بلوک حذف شد.")
        return redirect("dashboard:page-editor")


class PagePublishView(StoreAccessMixin, View):
    def post(self, request, *args, **kwargs):
        store = request.current_store
        try:
            layout = LayoutConfiguration.objects.get(store=store, page_type=LayoutConfiguration.PageType.HOME)
        except LayoutConfiguration.DoesNotExist:
            messages.warning(request, "ابتدا چیدمان را ذخیره کنید.")
            return redirect("dashboard:page-editor")
        LayoutConfigurationSnapshot.objects.create(
            store=store,
            page_type=layout.page_type,
            version=layout.version,
            block_order=layout.block_order,
            block_settings=layout.block_settings,
            block_enabled=layout.block_enabled,
        )
        layout.version += 1
        layout.save()
        messages.success(request, f"صفحه اصلی منتشر شد (نسخه {layout.version}).")
        return redirect("dashboard:page-editor")


class PageRollbackView(StoreAccessMixin, View):
    def post(self, request, *args, **kwargs):
        store = request.current_store
        version = request.POST.get("version")
        if not version:
            messages.error(request, "نسخه انتخاب نشده.")
            return redirect("dashboard:page-editor")
        try:
            snap = LayoutConfigurationSnapshot.objects.get(
                store=store, page_type=LayoutConfiguration.PageType.HOME, version=int(version)
            )
        except (LayoutConfigurationSnapshot.DoesNotExist, ValueError):
            messages.error(request, "نسخه یافت نشد.")
            return redirect("dashboard:page-editor")
        layout, _ = LayoutConfiguration.objects.get_or_create(
            store=store,
            page_type=LayoutConfiguration.PageType.HOME,
            defaults={"block_order": [], "block_settings": {}, "block_enabled": {}},
        )
        layout.block_order = snap.block_order
        layout.block_settings = snap.block_settings
        layout.block_enabled = snap.block_enabled
        layout.version += 1
        layout.save()
        messages.success(request, f"بازگشت به نسخه {snap.version} انجام شد.")
        return redirect("dashboard:page-editor")


# ─── SO-52: Smart Routing ─────────────────────────────────────
class OrderSmartRouteView(StoreAccessMixin, TemplateView):
    """
    GET  → compute smart routing plan and show it for operator review.
    POST → confirm plan: reserve stock + persist routing_plan on the order.
    """

    template_name = "dashboard/order_smart_route.html"

    def _get_order(self, request, pk):
        return get_object_or_404(Order, pk=pk, store=request.current_store)

    def get(self, request, *args, **kwargs):
        from core.smart_routing_service import SmartRoutingService

        order = self._get_order(request, kwargs["pk"])
        service = SmartRoutingService(order)
        plan = service.compute_plan()
        # Enrich plan entries with per-line available stock info for display
        enriched = _enrich_plan_for_display(plan)
        return self.render_to_response(
            self.get_context_data(order=order, plan=enriched, confirmed=False)
        )

    def post(self, request, *args, **kwargs):
        from core.smart_routing_service import SmartRoutingService

        order = self._get_order(request, kwargs["pk"])
        service = SmartRoutingService(order)
        plan = service.compute_plan()

        # Reserve stock atomically
        service.reserve_stock_for_plan(plan)

        # Persist the routing plan on the order
        order.routing_plan = SmartRoutingService.plan_to_json(plan)
        order.save(update_fields=["routing_plan"])

        messages.success(
            request,
            f"مسیریابی سفارش #{order.pk} تأیید شد و موجودی رزرو گردید.",
        )
        return redirect("dashboard:order-detail", pk=order.pk)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        # Allow callers to inject order/plan/confirmed directly (GET path)
        ctx.setdefault("order", None)
        ctx.setdefault("plan", [])
        ctx.setdefault("confirmed", False)
        ctx.update(kwargs)
        return ctx


def _enrich_plan_for_display(plan):
    """
    Add available-stock info to each line in the plan for template rendering.
    Returns a list of dicts:
        [{"warehouse": wh, "lines": [{"line": ol, "available": int}, ...]}]
    """
    from catalog.models import WarehouseStock

    enriched = []
    for entry in plan:
        wh = entry["warehouse"]
        enriched_lines = []
        for line in entry["lines"]:
            available = None
            if wh and line.variant_id:
                ws = WarehouseStock.objects.filter(
                    warehouse=wh, variant_id=line.variant_id
                ).first()
                available = ws.available if ws else 0
            enriched_lines.append({"line": line, "available": available})
        enriched.append({"warehouse": wh, "lines": enriched_lines})
    return enriched


# ─── Phase 4: BI Analytics ────────────────────────────────────
class DashboardAnalyticsView(StoreAccessMixin, TemplateView):
    """BI Dashboard with KPI cards and revenue trend table."""

    template_name = "dashboard/analytics.html"

    def get_context_data(self, **kwargs):
        from dashboard.analytics_service import get_store_analytics

        ctx = super().get_context_data(**kwargs)
        store = self.request.current_store

        days_param = self.request.GET.get("days", "30")
        try:
            days = int(days_param)
            if days not in (7, 14, 30, 60, 90):
                days = 30
        except (ValueError, TypeError):
            days = 30

        analytics = get_store_analytics(store, days=days)
        ctx["analytics"] = analytics
        ctx["days"] = days
        ctx["days_options"] = [7, 14, 30, 60, 90]
        return ctx


# ─── Phase 3: Abandoned Cart Recovery ────────────────────────
class AbandonedCartListView(StoreAccessMixin, ListView):
    """List persisted abandoned carts for the current store."""
    template_name = "dashboard/abandoned_cart_list.html"
    context_object_name = "abandoned_carts"
    paginate_by = 25

    def get_queryset(self):
        from customers.models import AbandonedCart
        qs = AbandonedCart.objects.filter(
            store=self.request.current_store
        ).select_related("customer").order_by("-updated_at")
        # Optional filter by recovered status
        status = self.request.GET.get("status", "")
        if status == "recovered":
            qs = qs.filter(recovered=True)
        elif status == "pending":
            qs = qs.filter(recovered=False)
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["status_filter"] = self.request.GET.get("status", "")
        return ctx


# ─── Phase 3: AI Chat History ─────────────────────────────────
class ChatHistoryView(StoreAccessMixin, ListView):
    """List AI chat sessions for the current store."""
    template_name = "dashboard/chat_history.html"
    context_object_name = "chat_sessions"
    paginate_by = 25

    def get_queryset(self):
        from crm.models import ChatSession
        return ChatSession.objects.filter(
            store=self.request.current_store
        ).select_related("customer").prefetch_related("messages").order_by("-updated_at")


# ─── Phase 4: External Integrations ───────────────────────────
_integrations_logger = logging.getLogger(__name__)


class IntegrationsView(StoreAccessMixin, TemplateView):
    """List and configure external integrations for the current store."""

    template_name = "dashboard/integrations.html"

    def _get_integration_list(self, store):
        """Return a list of dicts with integration metadata + current store config."""
        from core.integrations.registry import AVAILABLE_INTEGRATIONS
        from core.encryption import decrypt_value

        result = []
        for cls in AVAILABLE_INTEGRATIONS:
            obj = StoreIntegration.objects.filter(
                store=store, integration_id=cls.integration_id
            ).first()

            creds_raw = ""
            if obj and obj.credentials_encrypted:
                creds_raw = decrypt_value(obj.credentials_encrypted)

            result.append(
                {
                    "integration_id": cls.integration_id,
                    "integration_name": cls.integration_name,
                    "is_active": obj.is_active if obj else False,
                    "last_tested_at": obj.last_tested_at if obj else None,
                    "test_result": obj.test_result if obj else "",
                    "credentials_raw": creds_raw,
                    "is_configured": bool(creds_raw),
                }
            )
        return result

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["integrations"] = self._get_integration_list(self.request.current_store)
        return ctx

    def post(self, request, *args, **kwargs):
        """Save/update credentials for one integration."""
        from core.encryption import encrypt_value

        store = request.current_store
        integration_id = request.POST.get("integration_id", "").strip()
        credentials_json = request.POST.get("credentials_json", "").strip()
        is_active = request.POST.get("is_active") == "on"

        if not integration_id:
            messages.error(request, "شناسه یکپارچه‌سازی وارد نشده است.")
            return redirect("dashboard:integrations")

        # Validate JSON
        if credentials_json:
            try:
                json.loads(credentials_json)
            except json.JSONDecodeError:
                messages.error(request, "فرمت JSON اعتبارنامه‌ها نادرست است.")
                return redirect("dashboard:integrations")

        obj, _ = StoreIntegration.objects.get_or_create(
            store=store,
            integration_id=integration_id,
        )
        obj.credentials_encrypted = encrypt_value(credentials_json) if credentials_json else ""
        obj.is_active = is_active
        obj.save()

        messages.success(request, "تنظیمات یکپارچه‌سازی ذخیره شد.")
        return redirect("dashboard:integrations")


class IntegrationTestView(StoreAccessMixin, View):
    """POST — test connection for a specific integration; returns JSON."""

    def post(self, request, integration_id, *args, **kwargs):
        from core.integrations.registry import get_integration
        from core.encryption import decrypt_value

        store = request.current_store

        obj = StoreIntegration.objects.filter(
            store=store, integration_id=integration_id
        ).first()

        creds = {}
        if obj and obj.credentials_encrypted:
            raw = decrypt_value(obj.credentials_encrypted)
            if raw:
                try:
                    creds = json.loads(raw)
                except json.JSONDecodeError:
                    pass

        integration = get_integration(integration_id, store, creds)
        if integration is None:
            return JsonResponse(
                {"success": False, "message": "یکپارچه‌سازی ناشناخته است."}, status=404
            )

        try:
            result = integration.test_connection()
        except Exception as exc:
            _integrations_logger.exception(
                "Integration test_connection error: store=%s integration=%s",
                store.pk,
                integration_id,
            )
            result = {"success": False, "message": f"خطای سیستم: {exc}"}

        # Persist test result
        if obj:
            obj.last_tested_at = timezone.now()
            obj.test_result = result.get("message", "")[:200]
            obj.save(update_fields=["last_tested_at", "test_result"])

        return JsonResponse(result)
