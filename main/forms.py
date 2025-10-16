from django import forms
from django.forms import ModelForm
from django.utils.html import strip_tags
from django.contrib.auth.models import User
from main.models import Product, Profile


class ProductForm(ModelForm):
    class Meta:
        model = Product
        fields = [
            "product_name",
            "old_price",
            "special_price",
            "discount_percent",
            "category",
            "description",
            "thumbnail",
            "stock",
        ]

    def clean_product_name(self):
        product_name = self.cleaned_data["product_name"]
        return strip_tags(product_name)

    def clean_description(self):
        description = self.cleaned_data.get("description", "")
        return strip_tags(description)


class RegisterForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput)

    ROLE_CHOICES_WITH_ADMIN = Profile.ROLE_CHOICES + [('admin', 'Admin')]
    role = forms.ChoiceField(choices=ROLE_CHOICES_WITH_ADMIN)
    
    class Meta:
        model = User
        fields = ['username', 'password']

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data['password']) 
        if commit:
            user.save()
            Profile.objects.create(user=user, role=self.cleaned_data['role'])
        return user
