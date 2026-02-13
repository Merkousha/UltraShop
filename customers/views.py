from django.shortcuts import redirect, render
from django.views.generic import FormView, View
from django.contrib import messages
from django.utils.http import url_has_allowed_host_and_scheme

from .forms import PhoneEntryForm, OTPVerifyForm
from .services import create_and_send_login_otp, verify_login_otp

SESSION_CUSTOMER_KEY_PREFIX = "customer_id_"


def _customer_session_key(store_id):
    return f"{SESSION_CUSTOMER_KEY_PREFIX}{store_id}"


class CustomerLoginPhoneView(FormView):
    """Step 1: Enter phone; send OTP."""
    form_class = PhoneEntryForm
    template_name = "customers/login_phone.html"

    def get(self, request, *args, **kwargs):
        store = getattr(request, "store", None)
        if not store:
            messages.error(request, "فروشگاه یافت نشد.")
            return redirect("core:home")
        return super().get(request, *args, **kwargs)

    def form_valid(self, form):
        store = getattr(self.request, "store", None)
        if not store:
            return redirect("core:home")
        phone = form.cleaned_data["phone"]
        success, msg = create_and_send_login_otp(store, phone, request=self.request)
        if success:
            messages.success(self.request, msg)
            self.request.session["otp_phone"] = phone
            self.request.session["otp_store_id"] = store.pk
            return redirect("customers:verify_otp")
        messages.error(self.request, msg)
        return redirect("customers:login_phone")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["store"] = getattr(self.request, "store", None)
        return context


class CustomerVerifyOTPView(FormView):
    """Step 2: Enter OTP code; verify and log customer in."""
    form_class = OTPVerifyForm
    template_name = "customers/verify_otp.html"

    def get(self, request, *args, **kwargs):
        store = getattr(request, "store", None)
        if not store or request.session.get("otp_store_id") != store.pk:
            messages.error(request, "لطفاً ابتدا شماره موبایل را وارد کنید.")
            return redirect("customers:login_phone")
        return super().get(request, *args, **kwargs)

    def form_valid(self, form):
        store = getattr(self.request, "store", None)
        if not store:
            return redirect("core:home")
        phone = self.request.session.get("otp_phone")
        if not phone or self.request.session.get("otp_store_id") != store.pk:
            messages.error(self.request, "نشست منقضی شده. دوباره شماره را وارد کنید.")
            return redirect("customers:login_phone")
        code = form.cleaned_data["code"]
        customer, err = verify_login_otp(store, phone, code)
        if err:
            messages.error(self.request, err)
            return redirect("customers:verify_otp")
        # Log customer in: set session for this store
        self.request.session[_customer_session_key(store.pk)] = customer.pk
        # Clear OTP temp data
        self.request.session.pop("otp_phone", None)
        self.request.session.pop("otp_store_id", None)
        messages.success(self.request, "ورود با موفقیت انجام شد.")
        next_url = self.request.GET.get("next") or self.request.POST.get("next")
        if next_url and url_has_allowed_host_and_scheme(next_url, allowed_hosts=None):
            return redirect(next_url)
        return redirect("core:home")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["store"] = getattr(self.request, "store", None)
        context["masked_phone"] = ""
        phone = self.request.session.get("otp_phone", "")
        if len(phone) >= 4:
            context["masked_phone"] = "****" + phone[-4:]
        return context


class CustomerLogoutView(View):
    """Log out customer for current store only."""

    def post(self, request):
        store = getattr(request, "store", None)
        if store:
            key = _customer_session_key(store.pk)
            request.session.pop(key, None)
        next_url = request.GET.get("next") or request.POST.get("next") or request.META.get("HTTP_REFERER")
        if next_url and url_has_allowed_host_and_scheme(next_url, allowed_hosts=None):
            return redirect(next_url)
        return redirect("core:home")
