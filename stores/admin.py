from django.contrib import admin
from .models import Store, StoreDomain, StoreStaff


@admin.register(Store)
class StoreAdmin(admin.ModelAdmin):
    list_display = ("name", "username", "owner", "is_active", "created_at")
    list_filter = ("is_active",)
    search_fields = ("name", "username", "owner__email")


@admin.register(StoreDomain)
class StoreDomainAdmin(admin.ModelAdmin):
    list_display = ("domain", "store", "domain_type", "verified", "ssl_status", "is_primary")
    list_filter = ("verified", "domain_type")
    search_fields = ("domain", "store__name")


@admin.register(StoreStaff)
class StoreStaffAdmin(admin.ModelAdmin):
    list_display = ("user", "store", "role", "created_at")
    list_filter = ("store", "role")
    search_fields = ("user__email", "store__name")
