import json

from django.contrib import messages
from django.contrib.auth import views as auth_views
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.db.models import Count, Sum, Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect
from django.utils import timezone
from django.views import View
from django.views.generic import ListView, DetailView, TemplateView

from accounting.models import PayoutRequest, PlatformCommission, StoreTransaction
from core.encryption import encrypt_value, decrypt_value
from core.models import AuditLog, PlatformSettings, Store, ThemePreset
from core.services import log_action
from orders.models import Order
from shipping.models import Shipment, ShippingCarrier


class PlatformAdminMixin(LoginRequiredMixin, UserPassesTestMixin):
    login_url = "/platform/login/"

    def test_func(self):
        return self.request.user.groups.filter(name="PlatformAdmin").exists() or self.request.user.is_superuser


class PlatformLoginView(auth_views.LoginView):
    template_name = "platform_admin/login.html"
    redirect_authenticated_user = True

    def get_success_url(self):
        return "/platform/"


# ─── PA-35: KPI Dashboard ─────────────────────────────────
class DashboardView(PlatformAdminMixin, TemplateView):
    template_name = "platform_admin/dashboard.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        now = timezone.now()
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        week_start = today_start - timezone.timedelta(days=now.weekday())
        month_start = today_start.replace(day=1)

        ctx["active_stores"] = Store.objects.filter(is_active=True).count()
        ctx["total_stores"] = Store.objects.count()

        ctx["orders_today"] = Order.objects.filter(created_at__gte=today_start).count()
        ctx["orders_week"] = Order.objects.filter(created_at__gte=week_start).count()
        ctx["orders_month"] = Order.objects.filter(created_at__gte=month_start).count()

        commission_qs = PlatformCommission.objects.all()
        ctx["commission_total"] = commission_qs.aggregate(t=Sum("amount"))["t"] or 0
        ctx["commission_month"] = commission_qs.filter(
            created_at__gte=month_start
        ).aggregate(t=Sum("amount"))["t"] or 0

        ctx["pending_payouts"] = PayoutRequest.objects.filter(
            status=PayoutRequest.Status.PENDING
        ).count()
        ctx["pending_payouts_amount"] = PayoutRequest.objects.filter(
            status=PayoutRequest.Status.PENDING
        ).aggregate(t=Sum("amount"))["t"] or 0

        ctx["active_shipments"] = Shipment.objects.exclude(
            status__in=["delivered", "exception"]
        ).count()

        ctx["settings"] = PlatformSettings.load()
        return ctx


# ─── PA-10: Platform Settings ─────────────────────────────
class PlatformSettingsView(PlatformAdminMixin, TemplateView):
    template_name = "platform_admin/settings.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["settings"] = PlatformSettings.load()
        return ctx

    def post(self, request, *args, **kwargs):
        ps = PlatformSettings.load()
        ps.name = request.POST.get("name", ps.name)
        ps.support_email = request.POST.get("support_email", ps.support_email)
        ps.terms_url = request.POST.get("terms_url", ps.terms_url)
        ps.privacy_url = request.POST.get("privacy_url", ps.privacy_url)
        if request.FILES.get("logo"):
            ps.logo = request.FILES["logo"]
        if request.FILES.get("favicon"):
            ps.favicon = request.FILES["favicon"]
        ps.save()
        log_action(actor=request.user, action="platform_settings_updated", resource_type="PlatformSettings")
        return redirect("platform_admin:settings")


# ─── PA-11: Default Store Settings ────────────────────────
class DefaultStoreSettingsView(PlatformAdminMixin, TemplateView):
    template_name = "platform_admin/default_settings.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["settings"] = PlatformSettings.load()
        return ctx

    def post(self, request, *args, **kwargs):
        ps = PlatformSettings.load()
        ps.default_timezone = request.POST.get("default_timezone", ps.default_timezone)
        ps.default_currency = request.POST.get("default_currency", ps.default_currency)
        ps.default_guest_checkout = request.POST.get("default_guest_checkout") == "on"
        ps.save()
        log_action(
            actor=request.user,
            action="default_store_settings_updated",
            resource_type="PlatformSettings",
            details={
                "timezone": ps.default_timezone,
                "currency": ps.default_currency,
                "guest_checkout": ps.default_guest_checkout,
            },
        )
        return redirect("platform_admin:default-settings")


# ─── PA-12: Reserved Usernames ─────────────────────────────
class ReservedUsernamesView(PlatformAdminMixin, TemplateView):
    template_name = "platform_admin/reserved_usernames.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ps = PlatformSettings.load()
        ctx["reserved"] = ps.reserved_usernames or []
        return ctx

    def post(self, request, *args, **kwargs):
        ps = PlatformSettings.load()
        action = request.POST.get("action")

        if action == "add":
            username = request.POST.get("username", "").strip().lower()
            if username and username not in (ps.reserved_usernames or []):
                reserved = list(ps.reserved_usernames or [])
                reserved.append(username)
                ps.reserved_usernames = reserved
                ps.save()
                log_action(
                    actor=request.user,
                    action="reserved_username_added",
                    resource_type="PlatformSettings",
                    details={"username": username},
                )

        elif action == "remove":
            username = request.POST.get("username", "").strip().lower()
            reserved = list(ps.reserved_usernames or [])
            if username in reserved:
                reserved.remove(username)
                ps.reserved_usernames = reserved
                ps.save()
                log_action(
                    actor=request.user,
                    action="reserved_username_removed",
                    resource_type="PlatformSettings",
                    details={"username": username},
                )

        elif action == "seed":
            defaults = ["api", "admin", "www", "mail", "ftp", "platform", "static", "media"]
            reserved = list(ps.reserved_usernames or [])
            for name in defaults:
                if name not in reserved:
                    reserved.append(name)
            ps.reserved_usernames = reserved
            ps.save()
            log_action(
                actor=request.user,
                action="reserved_usernames_seeded",
                resource_type="PlatformSettings",
            )

        return redirect("platform_admin:reserved-usernames")


# ─── PA-15: SMS/Email Provider Config ──────────────────────
class ProviderConfigView(PlatformAdminMixin, TemplateView):
    template_name = "platform_admin/provider_config.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ps = PlatformSettings.load()
        ctx["settings"] = ps
        ctx["sms_api_key_set"] = bool(ps.sms_api_key_encrypted)
        ctx["email_password_set"] = bool(ps.email_password_encrypted)
        return ctx

    def post(self, request, *args, **kwargs):
        ps = PlatformSettings.load()
        ps.sms_provider = request.POST.get("sms_provider", "")
        ps.sms_sender = request.POST.get("sms_sender", "")
        sms_key = request.POST.get("sms_api_key", "")
        if sms_key:
            ps.sms_api_key_encrypted = encrypt_value(sms_key)

        ps.email_host = request.POST.get("email_host", "")
        ps.email_port = int(request.POST.get("email_port", 587) or 587)
        ps.email_username = request.POST.get("email_username", "")
        email_pass = request.POST.get("email_password", "")
        if email_pass:
            ps.email_password_encrypted = encrypt_value(email_pass)
        ps.email_use_tls = request.POST.get("email_use_tls") == "on"
        ps.email_from = request.POST.get("email_from", "")

        ps.save()
        log_action(
            actor=request.user,
            action="provider_config_updated",
            resource_type="PlatformSettings",
            details={"sms_provider": ps.sms_provider, "email_host": ps.email_host},
        )
        return redirect("platform_admin:provider-config")


class TestSMSView(PlatformAdminMixin, View):
    def post(self, request, *args, **kwargs):
        # Placeholder: send test SMS via configured provider
        return JsonResponse({"status": "ok", "message": "پیامک تست ارسال شد (mock)"})


class TestEmailView(PlatformAdminMixin, View):
    def post(self, request, *args, **kwargs):
        from django.core.mail import send_mail
        try:
            send_mail(
                subject="تست ایمیل UltraShop",
                message="این یک ایمیل تست از پلتفرم UltraShop است.",
                from_email=None,
                recipient_list=[request.user.email],
            )
            return JsonResponse({"status": "ok", "message": "ایمیل تست ارسال شد"})
        except Exception as e:
            return JsonResponse({"status": "error", "message": str(e)}, status=400)


# ─── PA-13: AI Service Config (Sprint 5) ─────────────────
class AISettingsView(PlatformAdminMixin, TemplateView):
    template_name = "platform_admin/ai_settings.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["settings"] = PlatformSettings.load()
        ps = ctx["settings"]
        ctx["openai_key_set"] = bool(ps.openai_api_key_encrypted)
        ctx["anthropic_key_set"] = bool(ps.anthropic_api_key_encrypted)
        return ctx

    def post(self, request, *args, **kwargs):
        ps = PlatformSettings.load()
        openai_key = request.POST.get("openai_api_key", "")
        if openai_key:
            ps.openai_api_key_encrypted = encrypt_value(openai_key)
        anthropic_key = request.POST.get("anthropic_api_key", "")
        if anthropic_key:
            ps.anthropic_api_key_encrypted = encrypt_value(anthropic_key)
        ps.vision_model = request.POST.get("vision_model", "gpt-4o") or "gpt-4o"
        ps.text_model = request.POST.get("text_model", "gpt-4o-mini") or "gpt-4o-mini"
        ps.image_gen_model = request.POST.get("image_gen_model", "flux") or "flux"
        ps.ai_enabled = request.POST.get("ai_enabled") == "on"
        try:
            ps.rate_limit_per_store_daily = int(request.POST.get("rate_limit_per_store_daily", 50) or 50)
        except ValueError:
            ps.rate_limit_per_store_daily = 50
        ps.save()
        log_action(
            actor=request.user,
            action="ai_settings_updated",
            resource_type="PlatformSettings",
            details={"ai_enabled": ps.ai_enabled, "vision_model": ps.vision_model},
        )
        messages.success(request, "تنظیمات AI ذخیره شد.")
        return redirect("platform_admin:ai-settings")


class TestAIView(PlatformAdminMixin, View):
    """Test OpenAI connection with a minimal chat call."""
    def post(self, request, *args, **kwargs):
        try:
            from core.ai_service import AIError, _get_client
            client = _get_client()
            client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": "Say OK in one word."}],
                max_tokens=5,
            )
            return JsonResponse({"status": "ok", "message": "اتصال به OpenAI برقرار شد."})
        except Exception as e:
            from core.ai_service import AIError
            msg = e.user_message if isinstance(e, AIError) else str(e)
            return JsonResponse({"status": "error", "message": msg}, status=400)


# ─── PA-20: Shipping Toggle ───────────────────────────────
class ShippingToggleView(PlatformAdminMixin, View):
    def post(self, request, *args, **kwargs):
        ps = PlatformSettings.load()
        ps.shipping_enabled = not ps.shipping_enabled
        ps.save()
        log_action(
            actor=request.user,
            action="shipping_toggled",
            resource_type="PlatformSettings",
            details={"shipping_enabled": ps.shipping_enabled},
        )
        return redirect("platform_admin:dashboard")


# ─── PA-22: All Shipments List ─────────────────────────────
class ShipmentListView(PlatformAdminMixin, ListView):
    template_name = "platform_admin/shipment_list.html"
    context_object_name = "shipments"
    paginate_by = 25

    def get_queryset(self):
        qs = Shipment.objects.select_related("store", "order", "carrier").all()

        store_id = self.request.GET.get("store")
        if store_id:
            qs = qs.filter(store_id=store_id)

        status = self.request.GET.get("status")
        if status:
            qs = qs.filter(status=status)

        date_from = self.request.GET.get("date_from")
        if date_from:
            qs = qs.filter(created_at__date__gte=date_from)

        date_to = self.request.GET.get("date_to")
        if date_to:
            qs = qs.filter(created_at__date__lte=date_to)

        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["stores"] = Store.objects.filter(is_active=True).order_by("name")
        ctx["statuses"] = Shipment.Status.choices
        ctx["current_filters"] = {
            "store": self.request.GET.get("store", ""),
            "status": self.request.GET.get("status", ""),
            "date_from": self.request.GET.get("date_from", ""),
            "date_to": self.request.GET.get("date_to", ""),
        }
        return ctx


class ShipmentDetailView(PlatformAdminMixin, DetailView):
    template_name = "platform_admin/shipment_detail.html"
    model = Shipment
    context_object_name = "shipment"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        shipment = self.object
        ctx["allowed_next"] = Shipment.ALLOWED_TRANSITIONS.get(shipment.status, [])
        return ctx


# ─── PA-23: Update Shipment Status ─────────────────────────
class ShipmentUpdateStatusView(PlatformAdminMixin, View):
    def post(self, request, pk):
        shipment = get_object_or_404(Shipment, pk=pk)
        new_status = request.POST.get("status")
        note = request.POST.get("note", "")

        if not shipment.can_transition_to(new_status):
            from django.contrib import messages
            messages.error(request, f"تغییر وضعیت از {shipment.status} به {new_status} مجاز نیست.")
            return redirect("platform_admin:shipment-detail", pk=pk)

        old_status = shipment.status
        shipment.status = new_status
        shipment.note = note
        shipment.save()

        # Update order status if needed
        if new_status == "delivered":
            shipment.order.status = "delivered"
            shipment.order.save(update_fields=["status", "updated_at"])

        log_action(
            actor=request.user,
            store=shipment.store,
            action="shipment_status_updated",
            resource_type="Shipment",
            resource_id=shipment.pk,
            details={"old_status": old_status, "new_status": new_status, "note": note},
        )

        return redirect("platform_admin:shipment-detail", pk=pk)


# ─── PA-30: Stores ─────────────────────────────────────────
class StoreListView(PlatformAdminMixin, ListView):
    template_name = "platform_admin/store_list.html"
    context_object_name = "stores"
    paginate_by = 25

    def get_queryset(self):
        qs = Store.objects.annotate(
            order_count=Count("orders"),
        ).all()
        q = self.request.GET.get("q")
        if q:
            qs = qs.filter(Q(name__icontains=q) | Q(username__icontains=q))
        status = self.request.GET.get("status")
        if status == "active":
            qs = qs.filter(is_active=True)
        elif status == "suspended":
            qs = qs.filter(is_active=False)
        return qs.order_by("-created_at")


class StoreDetailView(PlatformAdminMixin, DetailView):
    template_name = "platform_admin/store_detail.html"
    model = Store
    context_object_name = "store"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        from accounting.services import get_store_balance
        ctx["balance"] = get_store_balance(self.object)
        ctx["order_count"] = self.object.orders.count()
        ctx["shipment_count"] = self.object.shipments.count()
        return ctx


# ─── PA-33: Payouts ────────────────────────────────────────
class PayoutListView(PlatformAdminMixin, ListView):
    template_name = "platform_admin/payout_list.html"
    context_object_name = "payouts"
    paginate_by = 25

    def get_queryset(self):
        return PayoutRequest.objects.select_related("store").all()


# ─── PA-34: Commission Report ──────────────────────────────
class CommissionReportView(PlatformAdminMixin, TemplateView):
    template_name = "platform_admin/commission_report.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        qs = PlatformCommission.objects.select_related("store")

        date_from = self.request.GET.get("date_from")
        date_to = self.request.GET.get("date_to")
        if date_from:
            qs = qs.filter(created_at__date__gte=date_from)
        if date_to:
            qs = qs.filter(created_at__date__lte=date_to)

        ctx["total"] = qs.aggregate(t=Sum("amount"))["t"] or 0
        ctx["by_store"] = qs.values("store__name").annotate(total=Sum("amount")).order_by("-total")
        return ctx


# ─── PA-03: Audit Log ──────────────────────────────────────
class AuditLogView(PlatformAdminMixin, ListView):
    template_name = "platform_admin/audit_log.html"
    context_object_name = "logs"
    paginate_by = 50

    def get_queryset(self):
        qs = AuditLog.objects.select_related("actor", "store").all()
        action = self.request.GET.get("action")
        if action:
            qs = qs.filter(action=action)
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["actions"] = AuditLog.objects.values_list("action", flat=True).distinct()
        return ctx


# ─── PA-14: Theme Preset Management ─────────────────────────
class ThemePresetListView(PlatformAdminMixin, ListView):
    template_name = "platform_admin/theme_preset_list.html"
    context_object_name = "presets"
    paginate_by = 25

    def get_queryset(self):
        qs = ThemePreset.objects.annotate(store_count=Count("stores"))
        status = self.request.GET.get("status")
        if status:
            qs = qs.filter(status=status)
        return qs.order_by("name")

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["status_choices"] = ThemePreset.Status.choices
        ctx["current_status"] = self.request.GET.get("status", "")
        return ctx


class ThemePresetCreateView(PlatformAdminMixin, TemplateView):
    template_name = "platform_admin/theme_preset_form.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["action"] = "create"
        return ctx

    def post(self, request, *args, **kwargs):
        name = request.POST.get("name", "").strip()
        slug = request.POST.get("slug", "").strip()
        description = request.POST.get("description", "")
        version = request.POST.get("version", "1.0.0")
        status = request.POST.get("status", ThemePreset.Status.ACTIVE)
        tokens_raw = request.POST.get("tokens", "{}")
        try:
            import json as _json
            tokens = _json.loads(tokens_raw)
        except Exception:
            tokens = {}
        preset = ThemePreset.objects.create(
            name=name,
            slug=slug,
            description=description,
            version=version,
            status=status,
            tokens=tokens,
        )
        log_action(
            actor=request.user,
            action="theme_preset_created",
            resource_type="ThemePreset",
            resource_id=str(preset.pk),
            details={"name": name, "slug": slug},
        )
        messages.success(request, f"پوسته «{preset.name}» ایجاد شد.")
        return redirect("platform_admin:theme-preset-list")


class ThemePresetEditView(PlatformAdminMixin, TemplateView):
    template_name = "platform_admin/theme_preset_form.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        preset = get_object_or_404(ThemePreset, pk=self.kwargs["pk"])
        ctx["preset"] = preset
        ctx["action"] = "edit"
        ctx["store_count"] = preset.stores.count()
        import json as _json
        ctx["tokens_json"] = _json.dumps(preset.tokens, ensure_ascii=False, indent=2)
        return ctx

    def post(self, request, pk, *args, **kwargs):
        preset = get_object_or_404(ThemePreset, pk=pk)
        old_status = preset.status
        preset.name = request.POST.get("name", preset.name)
        preset.description = request.POST.get("description", preset.description)
        preset.version = request.POST.get("version", preset.version)
        preset.status = request.POST.get("status", preset.status)
        tokens_raw = request.POST.get("tokens", "{}")
        try:
            import json as _json
            preset.tokens = _json.loads(tokens_raw)
        except Exception:
            pass
        preset.save()
        store_count = preset.stores.count()
        log_action(
            actor=request.user,
            action="theme_preset_updated",
            resource_type="ThemePreset",
            resource_id=str(preset.pk),
            details={"name": preset.name, "old_status": old_status, "new_status": preset.status, "affected_stores": store_count},
        )
        messages.success(request, f"پوسته «{preset.name}» ویرایش شد.")
        return redirect("platform_admin:theme-preset-list")


class ThemePresetDeprecateView(PlatformAdminMixin, View):
    def post(self, request, pk):
        preset = get_object_or_404(ThemePreset, pk=pk)
        store_count = preset.stores.count()
        preset.status = ThemePreset.Status.DEPRECATED
        preset.save()
        log_action(
            actor=request.user,
            action="theme_preset_deprecated",
            resource_type="ThemePreset",
            resource_id=str(preset.pk),
            details={"name": preset.name, "affected_stores": store_count},
        )
        messages.success(request, f"پوسته «{preset.name}» منسوخ شد. {store_count} فروشگاه تحت‌تأثیر.")
        return redirect("platform_admin:theme-preset-list")
