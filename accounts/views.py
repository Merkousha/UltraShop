from django.shortcuts import redirect
from django.views.generic import CreateView, FormView
from django.contrib.auth import login
from django.urls import reverse_lazy
from django.views.decorators.csrf import ensure_csrf_cookie
from django.utils.decorators import method_decorator

from .forms import StoreOwnerSignupForm, StoreOwnerLoginForm


@method_decorator(ensure_csrf_cookie, name="get")
class SignupView(CreateView):
    """Store owner signup. Only shown on platform root (no store subdomain)."""
    form_class = StoreOwnerSignupForm
    template_name = "accounts/signup.html"
    success_url = reverse_lazy("stores:create")
    model = form_class.Meta.model

    def form_valid(self, form):
        self.object = form.save()
        login(self.request, self.object)
        return redirect(self.get_success_url())


class LoginView(FormView):
    """Store owner login."""
    form_class = StoreOwnerLoginForm
    template_name = "accounts/login.html"
    success_url = reverse_lazy("stores:dashboard")

    def form_valid(self, form):
        login(self.request, form.get_user())
        return redirect(self.get_success_url())
