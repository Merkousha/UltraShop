from django.shortcuts import redirect, get_object_or_404, render
from django.views.generic import TemplateView, ListView, DetailView, View, FormView, UpdateView, CreateView, DeleteView
from django.contrib.auth import authenticate, login
from django.contrib import messages
from django.urls import reverse, reverse_lazy

from django.db.models import Sum
from django.utils import timezone
from datetime import timedelta

from stores.models import Store
from accounting.models import PayoutRequest, StoreTransaction, PlatformCommission
from core.models import AuditLog, PlatformSettings
from shipping.models import ShippingCarrier
from accounting.services import get_store_balance, post_payout_approved

from .mixins import PlatformAdminRequiredMixin, is_platform_admin
from .forms import PlatformAdminPasswordChangeForm, PlatformSettingsForm, ShippingCarrierForm


class PlatformLoginView(TemplateView):
    """Login for platform admins only; redirect to dashboard if already platform admin."""
    template_name = "platform_admin/login.html"

    def get(self, request, *args, **kwargs):
        if request.user.is_authenticated and is_platform_admin(request.user):
            return redirect(request.GET.get("next", reverse("platform_admin:dashboard")))
        return super().get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["next"] = self.request.GET.get("next", reverse("platform_admin:dashboard"))
        return context

    def post(self, request, *args, **kwargs):
        next_url = request.POST.get("next") or request.GET.get("next") or reverse("platform_admin:dashboard")
        if request.user.is_authenticated and is_platform_admin(request.user):
            return redirect(next_url)
        email = request.POST.get("email", "").strip().lower()
        password = request.POST.get("password", "")
        user = authenticate(request, username=email, password=password)
        if user is None:
            from django.contrib.auth import get_user_model
            User = get_user_model()
            if User.USERNAME_FIELD == "email":
                user = authenticate(request, username=email, password=password)
        if user is None:
            messages.error(request, "Invalid email or password.")
            return render(request, self.template_name, {"next": next_url})
        if not is_platform_admin(user):
            messages.error(request, "You do not have platform admin access.")
            return render(request, self.template_name, {"next": next_url})
        login(request, user)
        return redirect(next_url)


class PlatformDashboardView(PlatformAdminRequiredMixin, TemplateView):
    template_name = "platform_admin/dashboard.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["store_count"] = Store.objects.filter(is_active=True).count()
        context["pending_payouts"] = PayoutRequest.objects.filter(status=PayoutRequest.STATUS_PENDING).count()
        return context


class PlatformPasswordChangeView(PlatformAdminRequiredMixin, View):
    """PA-04: Change password with strict policy (min 10, letter, digit, special)."""
    def get(self, request):
        form = PlatformAdminPasswordChangeForm(user=request.user)
        return render(request, "platform_admin/password_change.html", {"form": form})

    def post(self, request):
        form = PlatformAdminPasswordChangeForm(user=request.user, data=request.POST)
        if form.is_valid():
            request.user.set_password(form.cleaned_data["new_password1"])
            request.user.save(update_fields=["password"])
            from django.contrib.auth import update_session_auth_hash
            update_session_auth_hash(request, request.user)
            messages.success(request, "Your password has been changed.")
            return redirect("platform_admin:dashboard")
        return render(request, "platform_admin/password_change.html", {"form": form})


class CommissionReportView(PlatformAdminRequiredMixin, TemplateView):
    """PA-34: Platform commission summary by date range, optional per-store breakdown."""
    template_name = "platform_admin/commission_report.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        date_from = self.request.GET.get("date_from", "").strip()
        date_to = self.request.GET.get("date_to", "").strip()
        now = timezone.now()
        if not date_from:
            date_from = (now - timedelta(days=30)).strftime("%Y-%m-%d")
        if not date_to:
            date_to = now.strftime("%Y-%m-%d")
        try:
            from datetime import datetime as dt
            start = timezone.make_aware(dt.strptime(date_from, "%Y-%m-%d"))
            end = timezone.make_aware(dt.strptime(date_to, "%Y-%m-%d") + timedelta(days=1))
        except (ValueError, TypeError):
            start = now - timedelta(days=30)
            end = now + timedelta(days=1)
        qs = PlatformCommission.objects.filter(created_at__gte=start, created_at__lt=end)
        total = qs.aggregate(s=Sum("amount"))["s"] or 0
        per_store = list(
            qs.values("store__name", "store__username")
            .annotate(total=Sum("amount"))
            .order_by("-total")
        )
        context["total_commission"] = total
        context["per_store"] = per_store
        context["date_from"] = date_from
        context["date_to"] = date_to
        return context


class AuditLogListView(PlatformAdminRequiredMixin, ListView):
    """PA-03: List audit log entries with optional filters."""
    model = AuditLog
    template_name = "platform_admin/audit_log.html"
    context_object_name = "entries"
    paginate_by = 50

    def get_queryset(self):
        qs = AuditLog.objects.select_related("actor", "store").order_by("-created_at")
        action = self.request.GET.get("action", "").strip()
        if action:
            qs = qs.filter(action=action)
        store_id = self.request.GET.get("store", "").strip()
        if store_id:
            qs = qs.filter(store_id=store_id)
        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["action_choices"] = AuditLog.ACTION_CHOICES
        return context


class PlatformSettingsUpdateView(PlatformAdminRequiredMixin, UpdateView):
    """PA-10: Edit global platform settings."""
    model = PlatformSettings
    form_class = PlatformSettingsForm
    template_name = "platform_admin/platform_settings.html"
    success_url = reverse_lazy("platform_admin:platform_settings")
    context_object_name = "settings"

    def get_object(self, queryset=None):
        return PlatformSettings.get_settings()

    def form_valid(self, form):
        messages.success(self.request, "Platform settings saved.")
        return super().form_valid(form)


class ShippingCarrierListView(PlatformAdminRequiredMixin, ListView):
    """PA-21: List shipping carriers."""
    model = ShippingCarrier
    template_name = "platform_admin/carrier_list.html"
    context_object_name = "carriers"


class ShippingCarrierCreateView(PlatformAdminRequiredMixin, CreateView):
    model = ShippingCarrier
    form_class = ShippingCarrierForm
    template_name = "platform_admin/carrier_form.html"
    success_url = reverse_lazy("platform_admin:carrier_list")

    def form_valid(self, form):
        messages.success(self.request, "Carrier created.")
        return super().form_valid(form)


class ShippingCarrierUpdateView(PlatformAdminRequiredMixin, UpdateView):
    model = ShippingCarrier
    form_class = ShippingCarrierForm
    template_name = "platform_admin/carrier_form.html"
    context_object_name = "carrier"
    success_url = reverse_lazy("platform_admin:carrier_list")

    def form_valid(self, form):
        messages.success(self.request, "Carrier updated.")
        return super().form_valid(form)


class ShippingCarrierDeleteView(PlatformAdminRequiredMixin, DeleteView):
    model = ShippingCarrier
    success_url = reverse_lazy("platform_admin:carrier_list")

    def delete(self, request, *args, **kwargs):
        messages.success(request, "Carrier deleted.")
        return super().delete(request, *args, **kwargs)


class StoreListView(PlatformAdminRequiredMixin, ListView):
    model = Store
    template_name = "platform_admin/store_list.html"
    context_object_name = "stores"
    paginate_by = 20

    def get_queryset(self):
        qs = Store.objects.select_related("owner").order_by("-created_at")
        q = self.request.GET.get("q", "").strip()
        if q:
            qs = qs.filter(name__icontains=q) | qs.filter(username__icontains=q) | qs.filter(owner__email__icontains=q)
        status = self.request.GET.get("status")
        if status == "active":
            qs = qs.filter(is_active=True)
        elif status == "suspended":
            qs = qs.filter(is_active=False)
        return qs.distinct()


class StoreDetailView(PlatformAdminRequiredMixin, DetailView):
    model = Store
    template_name = "platform_admin/store_detail.html"
    context_object_name = "store"
    slug_field = "username"
    slug_url_kwarg = "username"

    def get_queryset(self):
        return Store.objects.select_related("owner")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        store = self.object
        context["balance"] = get_store_balance(store)
        context["order_count"] = store.orders.count()
        context["shipment_count"] = store.shipments.count() if hasattr(store, "shipments") else 0
        return context


class StoreSuspendView(PlatformAdminRequiredMixin, View):
    def post(self, request, username):
        store = get_object_or_404(Store, username=username)
        store.is_active = False
        store.save(update_fields=["is_active"])
        from core.models import log_audit
        log_audit(request.user, "store_suspended", "store", store.pk, request.POST.get("reason", ""), store=store)
        messages.success(request, f"Store {store.name} has been suspended.")
        return redirect("platform_admin:store_detail", username=username)


class StoreReactivateView(PlatformAdminRequiredMixin, View):
    def post(self, request, username):
        store = get_object_or_404(Store, username=username)
        store.is_active = True
        store.save(update_fields=["is_active"])
        from core.models import log_audit
        log_audit(request.user, "store_reactivated", "store", store.pk, request.POST.get("reason", ""), store=store)
        messages.success(request, f"Store {store.name} has been reactivated.")
        return redirect("platform_admin:store_detail", username=username)


class PayoutRequestListView(PlatformAdminRequiredMixin, ListView):
    model = PayoutRequest
    template_name = "platform_admin/payout_list.html"
    context_object_name = "payouts"
    paginate_by = 30

    def get_queryset(self):
        return PayoutRequest.objects.select_related("store", "store__owner").order_by("-created_at")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["pending_count"] = PayoutRequest.objects.filter(status=PayoutRequest.STATUS_PENDING).count()
        return context


class PayoutApproveView(PlatformAdminRequiredMixin, View):
    def post(self, request, pk):
        payout = get_object_or_404(PayoutRequest, pk=pk, status=PayoutRequest.STATUS_PENDING)
        post_payout_approved(payout)
        payout.status = PayoutRequest.STATUS_APPROVED
        payout.save(update_fields=["status", "updated_at"])
        from core.models import log_audit
        log_audit(request.user, "payout_approved", "payout_request", payout.pk, f"amount={payout.amount}", store=payout.store)
        messages.success(request, f"Payout {payout.amount} for {payout.store.name} approved.")
        return redirect("platform_admin:payout_list")


class PayoutRejectView(PlatformAdminRequiredMixin, View):
    def post(self, request, pk):
        payout = get_object_or_404(PayoutRequest, pk=pk, status=PayoutRequest.STATUS_PENDING)
        payout.status = PayoutRequest.STATUS_REJECTED
        payout.save(update_fields=["status", "updated_at"])
        from core.models import log_audit
        log_audit(request.user, "payout_rejected", "payout_request", payout.pk, "", store=payout.store)
        messages.success(request, f"Payout for {payout.store.name} rejected.")
        return redirect("platform_admin:payout_list")
