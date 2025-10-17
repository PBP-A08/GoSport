from django import forms
from django.forms import ModelForm
from django.utils.html import strip_tags
from django.contrib.auth.models import User
from main.models import Product, Profile
from django.db.models.signals import post_save

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
    password = forms.CharField(widget=forms.PasswordInput, label='Password')
    password2 = forms.CharField(widget=forms.PasswordInput, label='Confirm Password')

    ROLE_CHOICES_WITH_ADMIN = Profile.ROLE_CHOICES + [('admin', 'Admin')]
    role = forms.ChoiceField(choices=ROLE_CHOICES_WITH_ADMIN)
    
    class Meta:
        model = User
        fields = ['username', 'password'] 

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get("password")
        password2 = cleaned_data.get("password2")

        if password and password2 and password != password2:
            raise forms.ValidationError(
                "Passwords don't match."
            )
        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data['password']) 
        role = self.cleaned_data['role']
        is_admin_user = (role == 'admin') 
        
        if commit:
            from django.db.models.signals import post_save
            post_save.disconnect(sender=User, dispatch_uid="create_user_profile")
            
            user.save() 
            
            Profile.objects.create(
                user=user, 
                role=role, 
                is_admin=is_admin_user 
            )
            
            from main.signals import create_user_profile 
            post_save.connect(
                receiver=create_user_profile, 
                sender=User, 
                dispatch_uid="create_user_profile"
            )

        return user
    
class UserEditForm(forms.ModelForm):
    old_password = forms.CharField(widget=forms.PasswordInput, required=True, label="Current Password")
    
    class Meta:
        model = User
        fields = ['username']

class ProfileEditForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ['role']