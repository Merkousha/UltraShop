from django.contrib import admin

from core.models import AuditLog, PlatformSettings, Store, StoreDomain, StoreStaff, User


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ("email", "username", "is_staff", "is_active")
    search_fields = ("email", "username")


@admin.register(Store)
class StoreAdmin(admin.ModelAdmin):
    list_display = ("name", "username", "owner", "is_active", "created_at")
    list_filter = ("is_active",)
    search_fields = ("name", "username")


admin.site.register(StoreDomain)
admin.site.register(PlatformSettings)
admin.site.register(AuditLog)
admin.site.register(StoreStaff)
