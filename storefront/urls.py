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

    # Cart & Checkout
    path("cart/", views.CartView.as_view(), name="cart"),
    path("cart/add/", views.CartAddView.as_view(), name="cart-add"),
    path("cart/remove/", views.CartRemoveView.as_view(), name="cart-remove"),
    path("cart/recover/<uuid:token>/", views.CartRecoverView.as_view(), name="cart-recover"),
    path("checkout/", views.CheckoutView.as_view(), name="checkout"),
    path("order/<int:pk>/confirm/", views.OrderConfirmView.as_view(), name="order-confirm"),
    path("chat/", views.ChatView.as_view(), name="chat"),
    path("contact/", views.ContactView.as_view(), name="contact"),
]
