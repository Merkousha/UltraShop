from django.urls import path
from . import views

app_name = "orders"

urlpatterns = [
    path("checkout/place-order/", views.PlaceOrderView.as_view(), name="place_order"),
    path("order/<int:order_id>/confirmation/", views.OrderConfirmationView.as_view(), name="confirmation"),
    path("dashboard/orders/", views.DashboardOrderListView.as_view(), name="dashboard_order_list"),
    path("dashboard/orders/<int:order_id>/", views.DashboardOrderDetailView.as_view(), name="dashboard_order_detail"),
    path("my-orders/", views.MyOrdersView.as_view(), name="my_orders"),
    path("my-orders/<int:order_id>/", views.CustomerOrderDetailView.as_view(), name="customer_order_detail"),
]
