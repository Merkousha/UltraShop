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
        context["store"] = getattr(self.request, "store", None)
        return context


def handler404(request, exception):
    return render(request, "core/404.html", status=404)


def handler500(request):
    return render(request, "core/500.html", status=500)
