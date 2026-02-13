from django import forms
from .models import Category, Product, ProductVariant


class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ("name", "parent", "description", "sort_order", "meta_title", "meta_description")
        labels = {"name": "نام", "parent": "دسته والد", "description": "توضیح", "sort_order": "ترتیب", "meta_title": "عنوان متا", "meta_description": "توضیح متا"}
        widgets = {
            "name": forms.TextInput(attrs={"class": "input"}),
            "parent": forms.Select(attrs={"class": "input"}),
            "description": forms.Textarea(attrs={"class": "input", "rows": 3}),
            "sort_order": forms.NumberInput(attrs={"class": "input"}),
            "meta_title": forms.TextInput(attrs={"class": "input"}),
            "meta_description": forms.Textarea(attrs={"class": "input", "rows": 2}),
        }


class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = ("name", "description", "status", "categories", "meta_title", "meta_description")
        labels = {"name": "نام", "description": "توضیح", "status": "وضعیت", "categories": "دسته‌ها", "meta_title": "عنوان متا", "meta_description": "توضیح متا"}
        widgets = {
            "name": forms.TextInput(attrs={"class": "input"}),
            "description": forms.Textarea(attrs={"class": "input", "rows": 4}),
            "status": forms.Select(attrs={"class": "input"}),
            "categories": forms.SelectMultiple(attrs={"class": "input"}),
            "meta_title": forms.TextInput(attrs={"class": "input"}),
            "meta_description": forms.Textarea(attrs={"class": "input", "rows": 2}),
        }


class ProductVariantForm(forms.ModelForm):
    class Meta:
        model = ProductVariant
        fields = ("sku", "price", "compare_at_price", "stock")
        labels = {"sku": "کد کالا", "price": "قیمت", "compare_at_price": "قیمت مقایسه", "stock": "موجودی"}
        widgets = {
            "sku": forms.TextInput(attrs={"class": "input"}),
            "price": forms.NumberInput(attrs={"class": "input"}),
            "compare_at_price": forms.NumberInput(attrs={"class": "input"}),
            "stock": forms.NumberInput(attrs={"class": "input"}),
        }


ProductVariantFormSet = forms.inlineformset_factory(Product, ProductVariant, form=ProductVariantForm, extra=1, min_num=1)
