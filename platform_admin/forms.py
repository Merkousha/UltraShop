"""Forms for platform admin (e.g. strict password change)."""
import re
from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password

from core.models import PlatformSettings
from shipping.models import ShippingCarrier

User = get_user_model()


class PlatformAdminPasswordChangeForm(forms.Form):
    """PA-04: Strict password policy for platform admins (min 10, letter, digit, special)."""
    current_password = forms.CharField(
        label="Current password",
        widget=forms.PasswordInput(attrs={"class": "input", "autocomplete": "current-password"}),
    )
    new_password1 = forms.CharField(
        label="New password",
        widget=forms.PasswordInput(attrs={"class": "input", "autocomplete": "new-password"}),
    )
    new_password2 = forms.CharField(
        label="Confirm new password",
        widget=forms.PasswordInput(attrs={"class": "input", "autocomplete": "new-password"}),
    )

    MIN_LENGTH = 10
    COMPLEXITY = re.compile(r"^(?=.*[A-Za-z])(?=.*\d)(?=.*[!@#$%^&*()_+\-=\[\]{};':\"\\|,.<>\/?])")

    def __init__(self, user, *args, **kwargs):
        self.user = user
        super().__init__(*args, **kwargs)

    def clean_current_password(self):
        raw = self.cleaned_data.get("current_password")
        if not self.user.check_password(raw):
            raise forms.ValidationError("Current password is incorrect.")
        return raw

    def clean_new_password1(self):
        raw = self.cleaned_data.get("new_password1")
        if len(raw) < self.MIN_LENGTH:
            raise forms.ValidationError(f"Password must be at least {self.MIN_LENGTH} characters.")
        if not self.COMPLEXITY.search(raw):
            raise forms.ValidationError(
                "Password must contain at least one letter, one digit, and one special character."
            )
        validate_password(raw, self.user)
        return raw

    def clean(self):
        data = super().clean()
        if data.get("new_password1") and data.get("new_password2"):
            if data["new_password1"] != data["new_password2"]:
                self.add_error("new_password2", "Passwords do not match.")
        return data


class PlatformSettingsForm(forms.ModelForm):
    class Meta:
        model = PlatformSettings
        fields = ("name", "support_email", "terms_url", "privacy_url", "logo", "favicon")
        labels = {
            "name": "Platform name",
            "support_email": "Support email",
            "terms_url": "Terms of service URL",
            "privacy_url": "Privacy policy URL",
            "logo": "Logo",
            "favicon": "Favicon",
        }
        widgets = {
            "name": forms.TextInput(attrs={"class": "input"}),
            "support_email": forms.EmailInput(attrs={"class": "input"}),
            "terms_url": forms.URLInput(attrs={"class": "input"}),
            "privacy_url": forms.URLInput(attrs={"class": "input"}),
        }


class ShippingCarrierForm(forms.ModelForm):
    class Meta:
        model = ShippingCarrier
        fields = ("name", "code", "is_active", "api_credentials")
        widgets = {
            "name": forms.TextInput(attrs={"class": "input"}),
            "code": forms.TextInput(attrs={"class": "input", "placeholder": "e.g. post, tipax"}),
            "api_credentials": forms.Textarea(attrs={"class": "input", "rows": 3, "placeholder": "Optional: key=value per line"}),
        }
