"""Expense OCR extraction and creation service — SO-34."""

import json
import datetime


def extract_expense_from_image(store, image_file):
    """
    Use Vision AI to extract expense info from a receipt image.
    Returns dict: {amount, date, vendor, category, description}
    On failure returns empty dict.
    """
    from core.ai_service import call_vision_ai

    prompt = """این تصویر یک فاکتور/رسید است. اطلاعات زیر را استخراج کن و به صورت JSON برگردان:
{
  "amount": عدد مبلغ به ریال (فقط عدد صحیح بدون جداکننده هزارگان),
  "date": "YYYY-MM-DD",
  "vendor": "نام فروشنده یا فروشگاه",
  "category": یکی از: goods/packaging/shipping/marketing/rent/other,
  "description": "توضیح مختصر"
}
اگر اطلاعاتی پیدا نشد، null برگردان. فقط JSON خالص بدون توضیح اضافه برگردان."""

    try:
        result = call_vision_ai(store=store, image_file=image_file, prompt=prompt)
        if result is None or result.strip().lower() == "null":
            return {}
        data = json.loads(result)
        if not isinstance(data, dict):
            return {}
        # Sanitise amount: must be positive integer
        raw_amount = data.get("amount")
        if raw_amount is not None:
            try:
                data["amount"] = int(str(raw_amount).replace(",", "").replace("،", "").strip())
            except (ValueError, TypeError):
                data.pop("amount", None)
        # Sanitise date: must be YYYY-MM-DD
        raw_date = data.get("date")
        if raw_date:
            try:
                datetime.date.fromisoformat(str(raw_date))
                data["date"] = str(raw_date)
            except ValueError:
                data.pop("date", None)
        # Sanitise category
        from accounting.models import Expense
        valid_cats = {c[0] for c in Expense.Category.choices}
        if data.get("category") not in valid_cats:
            data["category"] = Expense.Category.OTHER
        return data
    except Exception:
        return {}


def create_expense_with_transaction(
    store,
    amount,
    date,
    vendor,
    category,
    description,
    receipt_image=None,
    is_ai_extracted=False,
):
    """Create an Expense record and a corresponding StoreTransaction (debit)."""
    from accounting.models import Expense, StoreTransaction

    transaction = StoreTransaction.objects.create(
        store=store,
        amount=-int(amount),  # negative = debit
        type=StoreTransaction.Type.EXPENSE,
        description=f"هزینه: {vendor or description or category}",
    )

    expense = Expense.objects.create(
        store=store,
        amount=int(amount),
        date=date,
        vendor=vendor or "",
        category=category or Expense.Category.OTHER,
        description=description or "",
        receipt_image=receipt_image,
        is_ai_extracted=is_ai_extracted,
        transaction=transaction,
    )
    return expense
