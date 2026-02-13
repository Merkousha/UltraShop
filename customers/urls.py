from django.urls import path
from . import views

app_name = "customers"

urlpatterns = [
    path("login/", views.CustomerLoginPhoneView.as_view(), name="login_phone"),
    path("verify/", views.CustomerVerifyOTPView.as_view(), name="verify_otp"),
    path("logout/", views.CustomerLogoutView.as_view(), name="logout"),
]
