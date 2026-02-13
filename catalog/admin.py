from django.contrib import admin
from .models import Category, Product, ProductVariant


class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "store", "parent", "sort_order")
    list_filter = ("store",)


class ProductVariantInline(admin.TabularInline):
    model = ProductVariant
    extra = 1


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ("name", "store", "status", "created_at")
    list_filter = ("store", "status")
    inlines = [ProductVariantInline]


admin.site.register(Category, CategoryAdmin)
