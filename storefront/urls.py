from django.urls import path
from storefront import views

app_name = "storefront"

urlpatterns = [
    path("", views.StoreHomeView.as_view(), name="home"),
    path("categories/", views.CategoryListView.as_view(), name="category-list"),
    path("categories/<slug:slug>/", views.CategoryDetailView.as_view(), name="category-detail"),
    path("products/<slug:slug>/", views.ProductDetailView.as_view(), name="product-detail"),

    # C-04: Product search
    path("search/", views.ProductSearchView.as_view(), name="product-search"),
]
