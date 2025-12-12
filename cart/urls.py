from django.urls import path
from . import views

app_name = 'cart'

urlpatterns = [
    # Web views 
    path('', views.view_cart, name='view_cart'),
    path('add/<uuid:product_id>/', views.add_to_cart, name='add_to_cart'),
    path('update/<int:item_id>/', views.update_cart_item, name='update_cart_item'),
    path('remove/<int:item_id>/', views.remove_from_cart, name='remove_from_cart'),
    path('checkout/review/', views.checkout_review, name='checkout_review'),
    path('checkout/', views.checkout_cart, name='checkout_cart'),

    # API endpoints untuk Flutter
    path('api/cart/', views.api_get_cart, name='api_get_cart'),
    path('api/cart/add/<uuid:product_id>/', views.api_add_to_cart, name='api_add_to_cart'),
    path('api/cart/update/<int:item_id>/', views.api_update_cart_item, name='api_update_cart_item'),
    path('api/cart/remove/<int:item_id>/', views.api_remove_from_cart, name='api_remove_from_cart'),
    path('api/cart/checkout/', views.api_checkout_cart, name='api_checkout_cart'),
]
