"""Mixins for store-scoped dashboard access: owner or staff vs owner-only."""
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect
from django.http import HttpResponseForbidden

from .models import user_can_access_store, user_is_store_owner


class StoreAccessMixin(LoginRequiredMixin):
    """Allow access if user is store owner or store staff (any role)."""
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        store = getattr(request, "store", None)
        if not store:
            return redirect("core:home")
        if not user_can_access_store(request.user, store):
            return HttpResponseForbidden()
        return super().dispatch(request, *args, **kwargs)


class StoreOwnerOnlyMixin(LoginRequiredMixin):
    """Allow access only for store owner (not staff). Use for accounting and sensitive sections."""
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        store = getattr(request, "store", None)
        if not store:
            return redirect("core:home")
        if not user_is_store_owner(request.user, store):
            return HttpResponseForbidden()
        return super().dispatch(request, *args, **kwargs)
