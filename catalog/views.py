from django.shortcuts import redirect, get_object_or_404, render
from django.views.generic import ListView, DetailView, CreateView, UpdateView, View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy, reverse
from django.http import HttpResponseForbidden, HttpResponseBadRequest
from django.contrib import messages
from django.views.decorators.http import require_POST
from django.utils.decorators import method_decorator

from stores.models import user_can_access_store
from stores.mixins import StoreAccessMixin

from .models import Category, Product, ProductImage, ProductVariant
from .forms import CategoryForm, ProductForm, ProductVariantFormSet
from .cart import get_cart_items, add_item, remove_item, update_item_qty, cart_total


def _store_owner_required(view_func):
    """Ensure request.store is set and request.user can access it (owner or staff)."""
    def wrapped(request, *args, **kwargs):
        store = getattr(request, "store", None)
        if not store:
            return redirect("core:home")
        if not user_can_access_store(request.user, store):
            return HttpResponseForbidden()
        return view_func(request, *args, **kwargs)
    return wrapped


class StoreOwnerMixin(StoreAccessMixin):
    """Require login and that request.user can access request.store (owner or staff)."""
    pass


# ---------- Storefront (public) ----------

class CategoryListView(ListView):
    """List categories for current store."""
    model = Category
    template_name = "catalog/category_list.html"
    context_object_name = "categories"

    def get_queryset(self):
        store = getattr(self.request, "store", None)
        if not store:
            return Category.objects.none()
        return Category.objects.filter(store=store, parent__isnull=True).order_by("sort_order", "name")

    def get(self, request, *args, **kwargs):
        if not getattr(request, "store", None):
            return redirect("core:home")
        return super().get(request, *args, **kwargs)


class ProductListView(ListView):
    """List active products for current store; optional category filter."""
    model = Product
    template_name = "catalog/product_list.html"
    context_object_name = "products"
    paginate_by = 20

    def get_queryset(self):
        store = getattr(self.request, "store", None)
        if not store:
            return Product.objects.none()
        qs = Product.objects.filter(store=store, status=Product.STATUS_ACTIVE).order_by("-created_at")
        cat_slug = self.kwargs.get("category_slug")
        if cat_slug:
            qs = qs.filter(categories__slug=cat_slug)
        return qs.distinct()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["category_slug"] = self.kwargs.get("category_slug")
        return context

    def get(self, request, *args, **kwargs):
        if not getattr(request, "store", None):
            return redirect("core:home")
        return super().get(request, *args, **kwargs)


class ProductDetailView(DetailView):
    """Product detail with variants (price, stock)."""
    model = Product
    template_name = "catalog/product_detail.html"
    context_object_name = "product"
    slug_url_kwarg = "slug"

    def get_queryset(self):
        store = getattr(self.request, "store", None)
        if not store:
            return Product.objects.none()
        return Product.objects.filter(store=store, status=Product.STATUS_ACTIVE)

    def get(self, request, *args, **kwargs):
        if not getattr(request, "store", None):
            return redirect("core:home")
        return super().get(request, *args, **kwargs)


# ---------- Dashboard (store owner) ----------

class DashboardCategoryListView(StoreOwnerMixin, ListView):
    model = Category
    template_name = "catalog/dashboard/category_list.html"
    context_object_name = "categories"

    def get_queryset(self):
        store = getattr(self.request, "store", None)
        return Category.objects.filter(store=store).order_by("sort_order", "name")


class DashboardProductListView(StoreOwnerMixin, ListView):
    model = Product
    template_name = "catalog/dashboard/product_list.html"
    context_object_name = "products"

    def get_queryset(self):
        store = getattr(self.request, "store", None)
        return Product.objects.filter(store=store).order_by("-created_at")


class DashboardCategoryCreateView(StoreOwnerMixin, CreateView):
    model = Category
    form_class = CategoryForm
    template_name = "catalog/dashboard/category_form.html"

    def form_valid(self, form):
        form.instance.store = getattr(self.request, "store", None)
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy("catalog:dashboard_category_list")

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        store = getattr(self.request, "store", None)
        if store and "parent" in form.fields:
            form.fields["parent"].queryset = Category.objects.filter(store=store)
        return form


class DashboardCategoryUpdateView(StoreOwnerMixin, UpdateView):
    model = Category
    form_class = CategoryForm
    template_name = "catalog/dashboard/category_form.html"
    context_object_name = "category"
    success_url = reverse_lazy("catalog:dashboard_category_list")

    def get_queryset(self):
        store = getattr(self.request, "store", None)
        return Category.objects.filter(store=store) if store else Category.objects.none()

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        store = getattr(self.request, "store", None)
        if store and "parent" in form.fields:
            form.fields["parent"].queryset = Category.objects.filter(store=store).exclude(pk=self.object.pk)
        return form


class DashboardProductCreateView(StoreOwnerMixin, CreateView):
    model = Product
    form_class = ProductForm
    template_name = "catalog/dashboard/product_form.html"

    def form_valid(self, form):
        form.instance.store = getattr(self.request, "store", None)
        response = super().form_valid(form)
        for i, f in enumerate(self.request.FILES.getlist("extra_images", [])):
            if f and f.content_type.startswith("image/"):
                ProductImage.objects.create(product=self.object, image=f, sort_order=i)
        return response

    def get_success_url(self):
        return reverse_lazy("catalog:dashboard_product_list")

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        store = getattr(self.request, "store", None)
        if store and "categories" in form.fields:
            form.fields["categories"].queryset = Category.objects.filter(store=store)
        return form


class DashboardProductUpdateView(StoreOwnerMixin, UpdateView):
    model = Product
    form_class = ProductForm
    template_name = "catalog/dashboard/product_form.html"
    context_object_name = "product"
    success_url = reverse_lazy("catalog:dashboard_product_list")

    def get_queryset(self):
        store = getattr(self.request, "store", None)
        return Product.objects.filter(store=store) if store else Product.objects.none()

    def form_valid(self, form):
        response = super().form_valid(form)
        start = self.object.images.count()
        for i, f in enumerate(self.request.FILES.getlist("extra_images", [])):
            if f and f.content_type.startswith("image/"):
                ProductImage.objects.create(product=self.object, image=f, sort_order=start + i)
        return response

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        store = getattr(self.request, "store", None)
        if store and "categories" in form.fields:
            form.fields["categories"].queryset = Category.objects.filter(store=store)
        return form


# ---------- Cart (storefront) ----------

def _cart_context(request):
    store = getattr(request, "store", None)
    if not store:
        return {"cart_items": [], "cart_total": 0, "store": None}
    items = get_cart_items(request.session, store.pk)
    variants = ProductVariant.objects.filter(pk__in=[x.get("variant_id") for x in items], product__store=store).select_related("product")
    variant_map = {v.pk: v for v in variants}
    cart_items = []
    for item in items:
        v = variant_map.get(item.get("variant_id"))
        if v:
            cart_items.append((item, v))
    total = cart_total(cart_items)
    return {"cart_items": cart_items, "cart_total": total, "store": store}


class CartDetailView(View):
    def get(self, request):
        store = getattr(request, "store", None)
        if not store:
            return redirect("core:home")
        context = _cart_context(request)
        return render(request, "catalog/cart_detail.html", context)

    def post(self, request):
        store = getattr(request, "store", None)
        if not store:
            return redirect("core:home")
        action = request.POST.get("action")
        variant_id = request.POST.get("variant_id")
        if action == "remove" and variant_id:
            try:
                remove_item(request.session, store.pk, int(variant_id))
                messages.success(request, "از سبد حذف شد.")
            except (TypeError, ValueError):
                pass
        elif action == "update_qty" and variant_id:
            try:
                qty = int(request.POST.get("qty", 0))
                update_item_qty(request.session, store.pk, int(variant_id), qty)
                messages.success(request, "سبد به‌روز شد.")
            except (TypeError, ValueError):
                pass
        return redirect("catalog:cart_detail")


class AddToCartView(View):
    def post(self, request):
        store = getattr(request, "store", None)
        if not store:
            return redirect("core:home")
        variant_id = request.POST.get("variant_id")
        qty = request.POST.get("qty", 1)
        try:
            variant_id = int(variant_id)
            qty = max(1, int(qty))
        except (TypeError, ValueError):
            return HttpResponseBadRequest()
        variant = get_object_or_404(ProductVariant, pk=variant_id, product__store=store)
        if variant.stock < qty:
            messages.error(request, "موجودی کافی نیست.")
            return redirect("catalog:product_detail", slug=variant.product.slug)
        add_item(request.session, store.pk, variant_id, qty, variant.price)
        messages.success(request, "به سبد اضافه شد.")
        next_url = request.POST.get("next") or request.META.get("HTTP_REFERER") or reverse_lazy("catalog:product_detail", kwargs={"slug": variant.product.slug})
        return redirect(next_url)


class CheckoutStartView(View):
    def get(self, request):
        from django.urls import reverse
        store = getattr(request, "store", None)
        if not store:
            return redirect("core:home")
        if not get_cart_items(request.session, store.pk):
            messages.info(request, "سبد خرید خالی است.")
            return redirect("catalog:cart_detail")
        if not getattr(store, "allow_guest_checkout", True) and not getattr(request, "customer", None):
            messages.info(request, "برای ادامه وارد شوید.")
            next_url = request.build_absolute_uri(reverse("catalog:checkout_address"))
            return redirect("customers:login_phone" + "?next=" + next_url)
        return redirect("catalog:checkout_address")


class CheckoutAddressView(View):
    """Collect shipping address (skeleton); save to session."""
    def get(self, request):
        store = getattr(request, "store", None)
        if not store:
            return redirect("core:home")
        if not get_cart_items(request.session, store.pk):
            return redirect("catalog:cart_detail")
        context = _cart_context(request)
        context["checkout_address"] = request.session.get("checkout_address") or {}
        return render(request, "catalog/checkout_address.html", context)

    def post(self, request):
        store = getattr(request, "store", None)
        if not store:
            return redirect("core:home")
        request.session["checkout_address"] = {
            "full_name": request.POST.get("full_name", "").strip(),
            "phone": request.POST.get("phone", "").strip(),
            "email": request.POST.get("email", "").strip().lower(),
            "address": request.POST.get("address", "").strip(),
            "city": request.POST.get("city", "").strip(),
        }
        request.session.modified = True
        return redirect("catalog:checkout_review")


class CheckoutReviewView(View):
    """Review cart + address; placeholder for payment."""
    def get(self, request):
        store = getattr(request, "store", None)
        if not store:
            return redirect("core:home")
        if not get_cart_items(request.session, store.pk):
            return redirect("catalog:cart_detail")
        context = _cart_context(request)
        context["checkout_address"] = request.session.get("checkout_address") or {}
        return render(request, "catalog/checkout_review.html", context)
