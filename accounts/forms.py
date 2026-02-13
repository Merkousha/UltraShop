from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth import get_user_model

User = get_user_model()


class StoreOwnerSignupForm(UserCreationForm):
    email = forms.EmailField(
        label="ایمیل",
        required=True,
        widget=forms.EmailInput(attrs={"autocomplete": "email", "dir": "ltr", "class": "input"}),
    )

    class Meta:
        model = User
        fields = ("email", "password1", "password2")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["password1"].label = "رمز عبور"
        self.fields["password2"].label = "تکرار رمز عبور"
        for name, field in self.fields.items():
            if name not in ("email",):
                field.widget.attrs.setdefault("class", "input")


class StoreOwnerLoginForm(AuthenticationForm):
    username = forms.EmailField(
        label="ایمیل",
        widget=forms.EmailInput(attrs={"autocomplete": "username", "dir": "ltr", "class": "input"}),
    )
    password = forms.CharField(
        label="رمز عبور",
        widget=forms.PasswordInput(attrs={"autocomplete": "current-password", "class": "input"}),
    )
