from django.urls import path, include
from main.views import (
    delete_product_ajax, edit_product_ajax, show_main, show_product, show_xml, show_json,
    show_xml_by_id, show_json_by_id, register, login_user,
    logout_user, add_product_entry_ajax
)

app_name = 'main'

urlpatterns = [
    path('', show_main, name='show_main'),
    path('product/<str:id>/', show_product, name='show_product'),
    path('xml/', show_xml, name='show_xml'),
    path('json/', show_json, name='show_json'),
    path('xml/<str:product_id>/', show_xml_by_id, name='show_xml_by_id'),
    path('json/<str:product_id>/', show_json_by_id, name='show_json_by_id'),
    path('register/', register, name='register'),
    path('login/', login_user, name='login'),
    path('logout/', logout_user, name='logout'),
    path('delete-product-ajax/<uuid:id>/', delete_product_ajax, name='delete_product_ajax'),
    path('create-product-ajax/', add_product_entry_ajax, name='add_product_entry_ajax'),
    path('edit-product-ajax/<uuid:id>/', edit_product_ajax, name='edit_product_ajax'),
]
