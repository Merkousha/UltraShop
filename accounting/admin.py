from django.contrib import admin
from .models import StoreTransaction, PayoutRequest, PlatformCommission


@admin.register(StoreTransaction)
class StoreTransactionAdmin(admin.ModelAdmin):
    list_display = ("store", "amount", "description", "created_at")
    list_filter = ("store",)


@admin.register(PayoutRequest)
class PayoutRequestAdmin(admin.ModelAdmin):
    list_display = ("store", "amount", "status", "created_at")
    list_filter = ("store", "status")

    def save_model(self, request, obj, form, change):
        if change and obj.pk:
            old = PayoutRequest.objects.get(pk=obj.pk)
            if old.status != PayoutRequest.STATUS_APPROVED and obj.status == PayoutRequest.STATUS_APPROVED:
                from .services import post_payout_approved
                post_payout_approved(obj)
        super().save_model(request, obj, form, change)


@admin.register(PlatformCommission)
class PlatformCommissionAdmin(admin.ModelAdmin):
    list_display = ("store", "order", "amount", "created_at")
    list_filter = ("store",)
    search_fields = ("store__name",)
