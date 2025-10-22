from django.contrib import admin
from .models import Profile, Product, ProductsData

@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'role', 'is_admin')
    list_filter = ('role',)
    search_fields = ('user__username',)

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('product_name', 'category', 'special_price', 'seller', 'stock')
    list_filter = ('category',)
    search_fields = ('product_name', 'seller__username')

@admin.register(ProductsData)
class ProductsDataAdmin(admin.ModelAdmin):
    list_display = ('data_id', 'product_name', 'old_price', 'special_price', 'discount_field', 'product')
    search_fields = ('product_name',)
