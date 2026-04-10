from django.db.models import Q
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect
from django.views import View
from django.views.generic import DetailView, ListView, TemplateView

from catalog.models import Category, Product, ProductVariant
from core.models import PlatformSettings, Store
from orders.models import Order, OrderLine


class StoreMixin:
    """Resolve store from URL slug."""

    def dispatch(self, request, *args, **kwargs):
        self.store = get_object_or_404(Store, username=kwargs["store_username"], is_active=True)
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["store"] = self.store
        from core.models import StoreTheme
        theme, _ = StoreTheme.objects.get_or_create(store=self.store)
        ctx["store_theme"] = theme
        return ctx


class StoreHomeView(StoreMixin, TemplateView):
    template_name = "storefront/home.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        from core.layout_service import get_layout_blocks
        ctx["layout_blocks"] = get_layout_blocks(self.store, "home")
        ctx["categories"] = Category.objects.filter(store=self.store, parent__isnull=True)
        ctx["featured_products"] = Product.objects.filter(
            store=self.store, status="active"
        ).prefetch_related("images", "variants")[:12]
        return ctx


class CategoryListView(StoreMixin, ListView):
    template_name = "storefront/category_list.html"
    context_object_name = "categories"

    def get_queryset(self):
        return Category.objects.filter(store=self.store, parent__isnull=True)


class CategoryDetailView(StoreMixin, TemplateView):
    template_name = "storefront/category_detail.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["category"] = get_object_or_404(
            Category, store=self.store, slug=self.kwargs["slug"]
        )
        ctx["products"] = Product.objects.filter(
            store=self.store, status="active", categories=ctx["category"]
        ).prefetch_related("images", "variants")
        return ctx


class ProductDetailView(StoreMixin, TemplateView):
    template_name = "storefront/product_detail.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["product"] = get_object_or_404(
            Product, store=self.store, slug=self.kwargs["slug"], status="active"
        )
        return ctx


# ─── C-04: Product Search ─────────────────────────────────
class ProductSearchView(StoreMixin, ListView):
    template_name = "storefront/search_results.html"
    context_object_name = "products"
    paginate_by = 20

    def get_queryset(self):
        q = self.request.GET.get("q", "").strip()
        if not q:
            return Product.objects.none()
        return Product.objects.filter(
            store=self.store,
            status="active",
        ).filter(
            Q(name__icontains=q) | Q(description__icontains=q) | Q(sku__icontains=q)
        ).prefetch_related("images", "variants")

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["query"] = self.request.GET.get("q", "")
        return ctx


# ─── Cart (session-based) ────────────────────────────────
def _get_cart(request):
    """Return cart dict: {str(variant_pk): quantity}."""
    return request.session.get("cart", {})


def _save_cart(request, cart):
    request.session["cart"] = cart
    request.session.modified = True


def _cart_items(store, cart):
    """Resolve cart dict to list of dicts with variant & product info."""
    items = []
    total = 0
    for variant_pk_str, qty in cart.items():
        try:
            variant = ProductVariant.objects.select_related("product").get(
                pk=int(variant_pk_str), product__store=store
            )
            line_total = variant.price * qty
            total += line_total
            items.append({
                "variant": variant,
                "product": variant.product,
                "quantity": qty,
                "line_total": line_total,
            })
        except (ProductVariant.DoesNotExist, ValueError):
            pass
    return items, total


class CartView(StoreMixin, TemplateView):
    """Show cart contents."""
    template_name = "storefront/cart.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        cart = _get_cart(self.request)
        items, total = _cart_items(self.store, cart)
        ctx["cart_items"] = items
        ctx["cart_total"] = total
        return ctx


class CartAddView(StoreMixin, View):
    """POST: add a product variant to the session cart."""

    def post(self, request, *args, **kwargs):
        variant_id = request.POST.get("variant_id")
        try:
            quantity = max(1, int(request.POST.get("quantity", 1)))
        except (ValueError, TypeError):
            quantity = 1

        try:
            variant = ProductVariant.objects.get(
                pk=int(variant_id), product__store=self.store, product__status="active"
            )
        except (ProductVariant.DoesNotExist, ValueError, TypeError):
            return redirect("storefront:cart", store_username=self.store.username)

        cart = _get_cart(request)
        key = str(variant.pk)
        cart[key] = cart.get(key, 0) + quantity
        _save_cart(request, cart)
        return redirect("storefront:cart", store_username=self.store.username)


class CartRemoveView(StoreMixin, View):
    """POST: remove an item from the session cart."""

    def post(self, request, *args, **kwargs):
        variant_id = request.POST.get("variant_id")
        cart = _get_cart(request)
        key = str(variant_id)
        if key in cart:
            del cart[key]
            _save_cart(request, cart)
        return redirect("storefront:cart", store_username=self.store.username)


class CheckoutView(StoreMixin, TemplateView):
    """GET: show checkout form. POST: place order."""
    template_name = "storefront/checkout.html"

    def _needs_shipping(self, cart):
        """Return True if any cart product requires shipping AND platform shipping is enabled."""
        ps = PlatformSettings.load()
        if not ps.shipping_enabled:
            return False
        for variant_pk_str in cart:
            try:
                variant = ProductVariant.objects.select_related("product").get(
                    pk=int(variant_pk_str), product__store=self.store
                )
                if variant.product.requires_shipping:
                    return True
            except (ProductVariant.DoesNotExist, ValueError):
                pass
        return False

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        cart = _get_cart(self.request)
        items, total = _cart_items(self.store, cart)
        ctx["cart_items"] = items
        ctx["cart_total"] = total
        ctx["needs_shipping"] = self._needs_shipping(cart)
        return ctx

    def post(self, request, *args, **kwargs):
        cart = _get_cart(request)
        if not cart:
            return redirect("storefront:cart", store_username=self.store.username)

        items, total = _cart_items(self.store, cart)
        if not items:
            return redirect("storefront:cart", store_username=self.store.username)

        needs_shipping = self._needs_shipping(cart)
        guest_name = request.POST.get("name", "").strip()
        guest_phone = request.POST.get("phone", "").strip()

        order = Order.objects.create(
            store=self.store,
            guest_name=guest_name,
            guest_phone=guest_phone,
            shipping_address=request.POST.get("address", "").strip() if needs_shipping else "",
            shipping_city=request.POST.get("city", "").strip() if needs_shipping else "",
            shipping_province=request.POST.get("province", "").strip() if needs_shipping else "",
            shipping_postal_code=request.POST.get("postal_code", "").strip() if needs_shipping else "",
            status=Order.Status.PENDING,
        )

        for item in items:
            OrderLine.objects.create(
                order=order,
                product=item["product"],
                variant=item["variant"],
                product_name=item["product"].name,
                variant_name=item["variant"].name,
                sku=item["variant"].sku,
                quantity=item["quantity"],
                unit_price=item["variant"].price,
            )

        # Clear cart
        _save_cart(request, {})

        return redirect("storefront:order-confirm", store_username=self.store.username, pk=order.pk)


class OrderConfirmView(StoreMixin, TemplateView):
    """Show order confirmation page."""
    template_name = "storefront/order_confirm.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["order"] = get_object_or_404(Order, pk=self.kwargs["pk"], store=self.store)
        return ctx

