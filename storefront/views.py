from django.db.models import Q
from django.http import Http404
from django.shortcuts import get_object_or_404
from django.views.generic import DetailView, ListView, TemplateView

from catalog.models import Category, Product
from core.models import Store


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
