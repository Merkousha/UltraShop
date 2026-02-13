from django import forms
from django.contrib.auth import get_user_model

from .models import Store, StoreDomain, StoreStaff

User = get_user_model()


class CreateStoreForm(forms.ModelForm):
    class Meta:
        model = Store
        fields = ("name", "username", "description")
        labels = {
            "name": "نام فروشگاه",
            "username": "نام کاربری (زیردامنه)",
            "description": "توضیح کوتاه (اختیاری)",
        }
        help_texts = {
            "username": "فروشگاه شما در آدرس username.ultrashop.local در دسترس خواهد بود. فقط حروف کوچک انگلیسی، عدد و خط تیره.",
        }
        widgets = {
            "name": forms.TextInput(attrs={"class": "input", "placeholder": "مثال: فروشگاه من"}),
            "username": forms.TextInput(attrs={"class": "input", "dir": "ltr", "placeholder": "mystore"}),
            "description": forms.Textarea(attrs={"class": "input", "rows": 2}),
        }

    def clean_username(self):
        value = self.cleaned_data.get("username", "").lower().strip()
        if value:
            return value
        return self.cleaned_data.get("username")


class StoreDomainForm(forms.Form):
    """Add a custom domain."""
    domain = forms.CharField(
        max_length=253,
        label="دامنه",
        widget=forms.TextInput(attrs={"class": "input", "dir": "ltr", "placeholder": "www.mystore.com"}),
    )

    def clean_domain(self):
        value = self.cleaned_data.get("domain", "").strip().lower()
        if not value or " " in value or "/" in value:
            raise forms.ValidationError("دامنه معتبر نیست.")
        return value


class StoreBrandingForm(forms.ModelForm):
    class Meta:
        model = Store
        fields = ("logo", "favicon", "primary_color", "theme_preset")
        labels = {"logo": "لوگو", "favicon": "فاویکون", "primary_color": "رنگ اصلی", "theme_preset": "قالب"}
        widgets = {
            "primary_color": forms.TextInput(attrs={"class": "input", "type": "color", "style": "height:2.5rem"}),
            "theme_preset": forms.Select(attrs={"class": "input"}),
        }


class AddStaffForm(forms.Form):
    email = forms.EmailField(label="ایمیل کاربر", widget=forms.EmailInput(attrs={"class": "input"}))
    role = forms.ChoiceField(choices=StoreStaff.ROLE_CHOICES, label="نقش", widget=forms.Select(attrs={"class": "input"}))

    def __init__(self, store, *args, **kwargs):
        self.store = store
        super().__init__(*args, **kwargs)

    def clean_email(self):
        email = self.cleaned_data.get("email", "").strip().lower()
        user = User.objects.filter(email=email).first()
        if not user:
            raise forms.ValidationError("کاربری با این ایمیل یافت نشد. کاربر باید قبلاً ثبت‌نام کرده باشد.")
        if self.store.owner_id == user.pk:
            raise forms.ValidationError("مالک فروشگاه قبلاً دسترسی دارد.")
        if StoreStaff.objects.filter(store=self.store, user=user).exists():
            raise forms.ValidationError("این کاربر قبلاً به فروشگاه اضافه شده است.")
        return email
