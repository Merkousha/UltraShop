from django.contrib import admin
from .models import Order, OrderLine


class OrderLineInline(admin.TabularInline):
    model = OrderLine
    extra = 0


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ("id", "store", "display_customer", "status", "total", "created_at")
    list_filter = ("store", "status")
    inlines = [OrderLineInline]
