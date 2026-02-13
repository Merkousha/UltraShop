from django.urls import path
from . import views

app_name = "payments"

urlpatterns = [
    path("pay/", views.StartPaymentView.as_view(), name="start"),
    path("callback/", views.PaymentCallbackView.as_view(), name="callback"),
]
