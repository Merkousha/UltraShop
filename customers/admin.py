from django.contrib import admin
from .models import Customer, LoginOTP


@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ("phone", "store", "name", "last_login_at", "created_at")
    list_filter = ("store",)
    search_fields = ("phone", "name", "email")


@admin.register(LoginOTP)
class LoginOTPAdmin(admin.ModelAdmin):
    list_display = ("phone", "store", "purpose", "is_used", "expires_at", "created_at")
    list_filter = ("purpose", "is_used")
