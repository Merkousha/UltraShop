"""
سرویس کمکی برای ثبت تغییرات موجودی انبار (SS-13).
هر بار که موجودی تغییر می‌کند، این تابع فراخوانی می‌شود.
"""

from catalog.models import InventoryLog


def log_inventory_change(
    warehouse,
    variant,
    action: str,
    quantity_before: int,
    quantity_change: int,
    note: str = "",
    actor=None,
) -> InventoryLog:
    """یک رکورد InventoryLog برای تغییر موجودی ایجاد و برگشت می‌دهد.

    Args:
        warehouse: شیء Warehouse
        variant: شیء ProductVariant
        action: یکی از مقادیر InventoryLog.Action (مثل "transfer", "adjust")
        quantity_before: موجودی پیش از تغییر
        quantity_change: مقدار تغییر (مثبت = افزایش، منفی = کاهش)
        note: توضیح اختیاری
        actor: کاربر عامل (می‌تواند None باشد)
    """
    return InventoryLog.objects.create(
        warehouse=warehouse,
        variant=variant,
        action=action,
        quantity_before=quantity_before,
        quantity_change=quantity_change,
        quantity_after=quantity_before + quantity_change,
        note=note,
        actor=actor,
    )
