from django.urls import path
from . import views

app_name = "catalog"

urlpatterns = [
    # Storefront
    path("categories/", views.CategoryListView.as_view(), name="category_list"),
    path("products/", views.ProductListView.as_view(), name="product_list"),
    path("products/category/<slug:category_slug>/", views.ProductListView.as_view(), name="product_list_by_category"),
    path("products/<slug:slug>/", views.ProductDetailView.as_view(), name="product_detail"),
    path("cart/", views.CartDetailView.as_view(), name="cart_detail"),
    path("cart/add/", views.AddToCartView.as_view(), name="add_to_cart"),
    path("checkout/", views.CheckoutStartView.as_view(), name="checkout_start"),
    path("checkout/address/", views.CheckoutAddressView.as_view(), name="checkout_address"),
    path("checkout/review/", views.CheckoutReviewView.as_view(), name="checkout_review"),
    # Dashboard (store owner)
    path("dashboard/categories/", views.DashboardCategoryListView.as_view(), name="dashboard_category_list"),
    path("dashboard/categories/create/", views.DashboardCategoryCreateView.as_view(), name="dashboard_category_create"),
    path("dashboard/categories/<int:pk>/edit/", views.DashboardCategoryUpdateView.as_view(), name="dashboard_category_edit"),
    path("dashboard/products/", views.DashboardProductListView.as_view(), name="dashboard_product_list"),
    path("dashboard/products/create/", views.DashboardProductCreateView.as_view(), name="dashboard_product_create"),
    path("dashboard/products/<int:pk>/edit/", views.DashboardProductUpdateView.as_view(), name="dashboard_product_edit"),
]
