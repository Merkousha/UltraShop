from django import forms


class PhoneEntryForm(forms.Form):
    phone = forms.CharField(
        label="شماره موبایل",
        max_length=20,
        widget=forms.TextInput(
            attrs={
                "class": "input",
                "dir": "ltr",
                "placeholder": "۰۹۱۲۳۴۵۶۷۸۹",
                "autocomplete": "tel",
            }
        ),
    )

    def clean_phone(self):
        from .models import normalize_phone
        value = self.cleaned_data.get("phone", "").strip()
        normalized = normalize_phone(value)
        if len(normalized) < 10:
            raise forms.ValidationError("شماره موبایل معتبر نیست.")
        return normalized


class OTPVerifyForm(forms.Form):
    code = forms.CharField(
        label="کد ورود",
        max_length=10,
        widget=forms.TextInput(
            attrs={
                "class": "input",
                "dir": "ltr",
                "placeholder": "۱۲۳۴۵۶",
                "autocomplete": "one-time-code",
            }
        ),
    )

    def clean_code(self):
        return self.cleaned_data.get("code", "").strip()
