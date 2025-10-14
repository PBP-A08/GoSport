from django.urls import path
from payment.views import show_main

app_name = 'payment'

urlpatterns = [
    path('', show_main, name='show_main'),
]
