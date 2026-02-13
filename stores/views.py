from django.shortcuts import redirect, get_object_or_404, render
from django.views.generic import CreateView, TemplateView, ListView, FormView, View
from django.contrib.auth import get_user_model
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.contrib import messages
from django.http import HttpResponseForbidden
from django.utils import timezone
from django.conf import settings as django_settings

from .models import Store, StoreDomain, StoreStaff, user_can_access_store, user_is_store_owner
from .forms import CreateStoreForm, StoreDomainForm, StoreBrandingForm, AddStaffForm
from .mixins import StoreAccessMixin, StoreOwnerOnlyMixin

User = get_user_model()


class CreateStoreView(LoginRequiredMixin, CreateView):
    """Create a new store (after signup or from dashboard)."""
    model = Store
    form_class = CreateStoreForm
    template_name = "stores/store_form.html"
    success_url = reverse_lazy("stores:dashboard")

    def form_valid(self, form):
        form.instance.owner = self.request.user
        return super().form_valid(form)

    def get_success_url(self):
        if getattr(django_settings, "PLATFORM_USE_PATH_BASED_STORE_URLS", False):
            return f"/store/{self.object.username}/dashboard/"
        return reverse_lazy("stores:dashboard") + f"?store={self.object.username}"


class DashboardView(LoginRequiredMixin, TemplateView):
    """Store dashboard: show stores user can access (owner or staff); if request.store set, show that store's dashboard."""
    template_name = "stores/dashboard.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Stores where user is owner or staff
        from django.db.models import Q
        context["owned_stores"] = Store.objects.filter(
            Q(owner=self.request.user) | Q(staff_members__user=self.request.user)
        ).distinct().order_by("name")
        context["staff_stores"] = set(
            StoreStaff.objects.filter(user=self.request.user).values_list("store_id", flat=True)
        )
        return context

    def get(self, request, *args, **kwargs):
        # Redirect to store (path-based or subdomain) if user selected a store and we're on root
        store_slug = request.GET.get("store")
        if store_slug and not getattr(request, "store", None):
            store = Store.objects.filter(username=store_slug).first()
            if store and user_can_access_store(request.user, store):
                if getattr(django_settings, "PLATFORM_USE_PATH_BASED_STORE_URLS", False):
                    return redirect(f"/store/{store.username}/dashboard/")
                root = getattr(django_settings, "PLATFORM_ROOT_DOMAIN", "ultrashop.local")
                scheme = "https" if request.is_secure() else "http"
                port = request.get_port()
                port_suffix = f":{port}" if port not in ("80", "443") else ""
                return redirect(f"{scheme}://{store.username}.{root}{port_suffix}/dashboard/")
        return super().get(request, *args, **kwargs)

    def dispatch(self, request, *args, **kwargs):
        # If on subdomain, only allow access if user is owner or staff
        store = getattr(request, "store", None)
        if store and not user_can_access_store(request.user, store):
            return HttpResponseForbidden()
        return super().dispatch(request, *args, **kwargs)


# ---------- Settings: domains, branding, staff (owner only or view for staff) ----------

class SettingsView(StoreAccessMixin, TemplateView):
    """Settings hub: links to domain, branding, staff. All roles can view; owner can edit."""
    template_name = "stores/settings.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["is_owner"] = user_is_store_owner(self.request.user, getattr(self.request, "store", None))
        return context


class DomainSettingsView(StoreAccessMixin, FormView):
    """Show subdomain URL, list custom domains, add custom domain (owner only)."""
    template_name = "stores/domain_settings.html"
    form_class = StoreDomainForm
    success_url = reverse_lazy("stores:domain_settings")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        store = getattr(self.request, "store", None)
        root = getattr(django_settings, "PLATFORM_ROOT_DOMAIN", "ultrashop.local")
        context["subdomain_url"] = f"https://{store.username}.{root}" if store else ""
        context["custom_domains"] = StoreDomain.objects.filter(store=store, domain_type=StoreDomain.TYPE_CUSTOM) if store else []
        context["is_owner"] = user_is_store_owner(self.request.user, store)
        return context

    def form_valid(self, form):
        store = getattr(self.request, "store", None)
        if not store or not user_is_store_owner(self.request.user, store):
            return HttpResponseForbidden()
        domain_name = form.cleaned_data["domain"]
        if StoreDomain.objects.filter(store=store, domain=domain_name).exists():
            messages.warning(self.request, "این دامنه قبلاً اضافه شده است.")
            return redirect("stores:domain_settings")
        root = getattr(django_settings, "PLATFORM_ROOT_DOMAIN", "ultrashop.local")
        StoreDomain.objects.create(
            store=store,
            domain=domain_name,
            domain_type=StoreDomain.TYPE_CUSTOM,
            verified=False,
        )
        messages.success(
            self.request,
            f"دامنه {domain_name} اضافه شد. رکورد CNAME را به {store.username}.{root} تنظیم کنید، سپس تأیید را بزنید.",
        )
        return redirect("stores:domain_settings")


class VerifyDomainView(StoreOwnerOnlyMixin, View):
    """Mark custom domain as verified (v1: simple button; real DNS check optional)."""
    def post(self, request, domain_id):
        store = getattr(request, "store", None)
        domain = get_object_or_404(StoreDomain, pk=domain_id, store=store, domain_type=StoreDomain.TYPE_CUSTOM)
        domain.verified = True
        domain.save(update_fields=["verified"])
        messages.success(request, f"دامنه {domain.domain} تأیید شد.")
        return redirect("stores:domain_settings")


class SetPrimaryDomainView(StoreOwnerOnlyMixin, View):
    def post(self, request, domain_id):
        store = getattr(request, "store", None)
        domain = get_object_or_404(StoreDomain, pk=domain_id, store=store)
        domain.is_primary = True
        domain.save(update_fields=["is_primary"])
        messages.success(request, f"{domain.domain} به عنوان دامنه اصلی تنظیم شد.")
        return redirect("stores:domain_settings")


class BrandingSettingsView(StoreAccessMixin, FormView):
    template_name = "stores/branding_settings.html"
    form_class = StoreBrandingForm
    success_url = reverse_lazy("stores:branding_settings")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["is_owner"] = user_is_store_owner(self.request.user, getattr(self.request, "store", None))
        return context

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["instance"] = getattr(self.request, "store", None)
        return kwargs

    def form_valid(self, form):
        store = getattr(self.request, "store", None)
        if not store or not user_is_store_owner(self.request.user, store):
            return HttpResponseForbidden()
        form.save()
        messages.success(self.request, "تنظیمات ظاهری ذخیره شد.")
        return redirect("stores:branding_settings")


class StaffListView(StoreAccessMixin, ListView):
    """List staff; owner can add/remove."""
    model = StoreStaff
    template_name = "stores/staff_list.html"
    context_object_name = "staff_list"

    def get_queryset(self):
        store = getattr(self.request, "store", None)
        if not store:
            return StoreStaff.objects.none()
        return StoreStaff.objects.filter(store=store).select_related("user").order_by("user__email")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["is_owner"] = user_is_store_owner(self.request.user, getattr(self.request, "store", None))
        context["add_form"] = AddStaffForm(store=getattr(self.request, "store")) if context["is_owner"] else None
        return context


class AddStaffView(StoreOwnerOnlyMixin, FormView):
    form_class = AddStaffForm
    success_url = reverse_lazy("stores:staff_list")

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["store"] = getattr(self.request, "store")
        return kwargs

    def form_valid(self, form):
        store = getattr(self.request, "store", None)
        user = User.objects.get(email=form.cleaned_data["email"].strip().lower())
        StoreStaff.objects.get_or_create(store=store, user=user, defaults={"role": form.cleaned_data["role"]})
        messages.success(self.request, f"{user.email} به فروشگاه اضافه شد.")
        return redirect("stores:staff_list")

    def form_invalid(self, form):
        for _list in form.errors.values():
            for msg in _list:
                messages.error(self.request, msg)
        return redirect("stores:staff_list")


class RemoveStaffView(StoreOwnerOnlyMixin, View):
    def post(self, request, user_id):
        store = getattr(request, "store", None)
        staff = get_object_or_404(StoreStaff, store=store, user_id=user_id)
        staff.delete()
        messages.success(request, "کاربر از فروشگاه حذف شد.")
        return redirect("stores:staff_list")
