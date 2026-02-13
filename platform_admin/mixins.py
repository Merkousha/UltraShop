"""Require user to be in PlatformAdmin group."""
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect
from django.http import HttpResponseForbidden
from django.urls import reverse


PLATFORM_ADMIN_GROUP_NAME = "PlatformAdmin"


def is_platform_admin(user):
    return user.is_authenticated and user.groups.filter(name=PLATFORM_ADMIN_GROUP_NAME).exists()


class PlatformAdminRequiredMixin(LoginRequiredMixin):
    """Allow access only for users in PlatformAdmin group."""
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        if not is_platform_admin(request.user):
            if request.path.startswith("/platform/") and not request.path.startswith("/platform/admin/"):
                return redirect(reverse("platform_admin:login") + "?next=" + request.get_full_path())
            return HttpResponseForbidden()
        return super().dispatch(request, *args, **kwargs)
