import csv
from decimal import Decimal
from django.shortcuts import redirect, get_object_or_404, render
from django.views.generic import ListView, View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponse, HttpResponseForbidden
from django.contrib import messages
from django.db.models import Sum
from django.utils import timezone
from datetime import timedelta

from stores.mixins import StoreOwnerOnlyMixin

from .models import StoreTransaction, PayoutRequest
from .services import get_store_balance


class StoreOwnerAccountingMixin(StoreOwnerOnlyMixin):
    """Only store owner can access accounting (not staff)."""
    pass


class LedgerView(StoreOwnerAccountingMixin, ListView):
    model = StoreTransaction
    template_name = "accounting/ledger.html"
    context_object_name = "transactions"
    paginate_by = 30

    def get_queryset(self):
        store = getattr(self.request, "store", None)
        if not store:
            return StoreTransaction.objects.none()
        return StoreTransaction.objects.filter(store=store).select_related("order").order_by("-created_at")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        store = getattr(self.request, "store", None)
        context["balance"] = get_store_balance(store) if store else Decimal("0")
        return context


class LedgerExportView(StoreOwnerAccountingMixin, View):
    """Export ledger as CSV for date range."""
    def get(self, request):
        store = getattr(request, "store", None)
        if not store:
            return redirect("accounting:ledger")
        date_from = request.GET.get("date_from", "").strip()
        date_to = request.GET.get("date_to", "").strip()
        qs = StoreTransaction.objects.filter(store=store).select_related("order").order_by("created_at")
        try:
            from datetime import datetime as dt
            if date_from:
                qs = qs.filter(created_at__date__gte=dt.strptime(date_from, "%Y-%m-%d").date())
            if date_to:
                qs = qs.filter(created_at__date__lte=dt.strptime(date_to, "%Y-%m-%d").date())
        except ValueError:
            pass
        response = HttpResponse(content_type="text/csv")
        response["Content-Disposition"] = 'attachment; filename="ledger.csv"'
        response.write("\ufeff")  # BOM for Excel UTF-8
        writer = csv.writer(response)
        writer.writerow(["تاریخ", "شرح", "مبلغ"])
        for t in qs:
            writer.writerow([
                t.created_at.strftime("%Y-%m-%d %H:%M"),
                t.description,
                str(t.amount),
            ])
        return response


class AccountingSummaryView(StoreOwnerAccountingMixin, View):
    """Revenue and expense summary for a period."""
    def get(self, request):
        store = getattr(request, "store", None)
        if not store:
            return redirect("core:home")
        period = request.GET.get("period", "month")  # today, week, month
        now = timezone.now()
        if period == "today":
            start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        elif period == "week":
            start = now - timedelta(days=7)
        else:
            start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        qs = StoreTransaction.objects.filter(store=store, created_at__gte=start)
        revenue = qs.filter(amount__gt=0).aggregate(s=Sum("amount"))["s"] or Decimal("0")
        expenses = qs.filter(amount__lt=0).aggregate(s=Sum("amount"))["s"] or Decimal("0")
        balance = get_store_balance(store)
        return render(request, "accounting/summary.html", {
            "revenue": revenue,
            "expenses": abs(expenses),
            "net": revenue + expenses,
            "balance": balance,
            "period": period,
        })


class PayoutRequestView(StoreOwnerAccountingMixin, View):
    """List payout requests and create new one."""
    def get(self, request):
        store = getattr(request, "store", None)
        if not store:
            return redirect("core:home")
        balance = get_store_balance(store)
        requests = PayoutRequest.objects.filter(store=store).order_by("-created_at")
        return render(request, "accounting/payouts.html", {
            "balance": balance,
            "payout_requests": requests,
        })

    def post(self, request):
        store = getattr(request, "store", None)
        if not store:
            return redirect("core:home")
        balance = get_store_balance(store)
        try:
            amount = Decimal(request.POST.get("amount", "0"))
        except Exception:
            amount = Decimal("0")
        details = request.POST.get("payment_details", "").strip()
        if amount <= 0:
            messages.error(request, "مبلغ باید بیشتر از صفر باشد.")
            return redirect("accounting:payouts")
        if amount > balance:
            messages.error(request, "مبلغ بیشتر از موجودی است.")
            return redirect("accounting:payouts")
        PayoutRequest.objects.create(
            store=store,
            amount=amount,
            payment_details=details,
        )
        messages.success(request, "درخواست تسویه ثبت شد و پس از تأیید پرداخت می‌شود.")
        return redirect("accounting:payouts")
