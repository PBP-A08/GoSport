from django.urls import path
from payment.views import (
    show_main,
    pay,
    complete_transaction,
    delete_transaction_ajax,
    show_json,
)

app_name = 'payment'

urlpatterns = [
    path('', show_main, name='show_main'),
    path('pay/<uuid:id>/', pay, name='pay_ajax'),
    path('complete/<uuid:id>/', complete_transaction, name='complete_transaction_ajax'),
    path('delete/<uuid:id>/', delete_transaction_ajax, name='delete_transaction_ajax'),
    path('json/', show_json, name='show_json')
]
