from django.shortcuts import render
from django.views.generic import TemplateView


class HomeView(TemplateView):
    """Landing on root; storefront when request.store is set (subdomain)."""
    template_name = "core/home.html"

    def get_template_names(self):
        if getattr(self.request, "store", None):
            return ["stores/storefront_home.html"]
        return [self.template_name]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        store = getattr(self.request, "store", None)
        context["store"] = store
        if store:
            from catalog.models import Category, Product
            context["store_categories"] = Category.objects.filter(
                store=store, parent__isnull=True
            ).order_by("sort_order", "name")
            context["store_products"] = Product.objects.filter(
                store=store, status=Product.STATUS_ACTIVE
            ).order_by("-created_at")[:24]
        return context


def handler404(request, exception):
    return render(request, "core/404.html", status=404)


def handler500(request):
    return render(request, "core/500.html", status=500)
