from django.urls import path
from profile.views import (
    profile_dashboard, edit_profile, edit_password, delete_account
)

app_name = 'profile'

urlpatterns = [
    path('', profile_dashboard, name='profile_dashboard'),
    path('edit/', edit_profile, name='edit_profile'),
    path('edit/password/', edit_password, name='edit_password'),
    path('delete/', delete_account, name='delete_account'),
]
