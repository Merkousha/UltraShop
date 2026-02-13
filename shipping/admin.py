from django.contrib import admin
from .models import Shipment, ShippingCarrier


@admin.register(ShippingCarrier)
class ShippingCarrierAdmin(admin.ModelAdmin):
    list_display = ("name", "code", "is_active")
    list_filter = ("is_active",)


@admin.register(Shipment)
class ShipmentAdmin(admin.ModelAdmin):
    list_display = ("id", "store", "order", "tracking_number", "status", "created_at")
    list_filter = ("store", "status")
