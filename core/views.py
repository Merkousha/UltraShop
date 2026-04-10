from django.contrib.auth import login
from django.shortcuts import redirect, render

from .models import PlatformSettings, Store, User


def signup_view(request):
    """Email-based signup for store owners. Redirects to dashboard home on success."""
    if request.user.is_authenticated:
        return redirect("dashboard:home")

    error = None
    if request.method == "POST":
        email = (request.POST.get("email") or "").strip().lower()
        password = request.POST.get("password") or ""
        password_confirm = request.POST.get("password_confirm") or ""

        if not email:
            error = "ایمیل را وارد کنید."
        elif not password:
            error = "رمز عبور را وارد کنید."
        elif len(password) < 8:
            error = "رمز عبور باید حداقل ۸ کاراکتر باشد."
        elif password != password_confirm:
            error = "تکرار رمز عبور با رمز عبور یکسان نیست."
        elif User.objects.filter(email=email).exists():
            error = "این ایمیل قبلاً ثبت شده است."
        else:
            user = User.objects.create_user(
                username=email,
                email=email,
                password=password,
            )
            login(request, user)
            # Create a default store so new users can use the dashboard (categories, products, etc.)
            ps = PlatformSettings.load()
            reserved = set(ps.reserved_usernames or [])
            base_username = f"store-{user.pk}"
            username = base_username
            suffix = 0
            while username in reserved or Store.objects.filter(username=username).exists():
                suffix += 1
                username = f"{base_username}-{suffix}"
            store = Store.objects.create(
                owner=user,
                name="فروشگاه من",
                username=username,
                timezone=ps.default_timezone,
                currency=ps.default_currency,
                allow_guest_checkout=ps.default_guest_checkout,
            )
            request.session["current_store_id"] = store.pk
            request.session.modified = True
            # Provision tenant schema in multi-tenant mode (no-op in SQLite mode)
            try:
                from core.provisioning import provision_store_schema
                provision_store_schema(store)
            except RuntimeError as exc:
                import logging
                logging.getLogger(__name__).error(
                    "Tenant provisioning failed for store %s: %s", store.pk, exc
                )
                # Don't break signup — store still created in shared mode
            return redirect("dashboard:home")

    return render(
        request,
        "accounts/signup.html",
        {"error": error, "email": request.POST.get("email", "").strip() if request.method == "POST" else ""},
    )
