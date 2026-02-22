from django.urls import path, re_path
from storefront import views

app_name = "storefront"

# Slug that allows Unicode (e.g. Persian) for category/product URLs
slug_unicode = r"[^/]+"

urlpatterns = [
    path("", views.StoreHomeView.as_view(), name="home"),
    path("categories/", views.CategoryListView.as_view(), name="category-list"),
    re_path(r"categories/(?P<slug>" + slug_unicode + ")/", views.CategoryDetailView.as_view(), name="category-detail"),
    re_path(r"products/(?P<slug>" + slug_unicode + ")/", views.ProductDetailView.as_view(), name="product-detail"),

    # C-04: Product search
    path("search/", views.ProductSearchView.as_view(), name="product-search"),
]
