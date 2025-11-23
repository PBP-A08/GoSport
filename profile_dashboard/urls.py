from django.urls import path
from profile_dashboard import views

app_name = 'profile_dashboard'

urlpatterns = [
    path('', views.profile_dashboard, name='profile_dashboard'),
    path('edit/', views.edit_profile, name='edit_profile'),
    path('edit/password/', views.edit_password, name='edit_password'),
    path('delete/', views.delete_account, name='delete_account'),
    path('json/', views.profile_json, name='profile_json'),
    path('edit-json/', views.edit_profile_json, name='edit_profile_json'), 
    path('change-password/', views.change_password, name='change_password'), 
    path('delete-json/', views.delete_account_json, name='delete_account_json'),
]