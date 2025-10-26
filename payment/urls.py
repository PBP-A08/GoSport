from django.urls import path
from payment.views import (
    show_main,
    view_transaction,
    pay,
    complete_transaction,
    delete_transaction_ajax,
    show_json,
    show_json_by_id,
    show_transactions_json
)

app_name = 'payment'

urlpatterns = [
    path('', show_main, name='show_main'),
    path('transaction/<uuid:id>/', view_transaction, name='view_transaction'),
    path('pay/<uuid:id>/', pay, name='pay_ajax'),
    path('complete/<uuid:id>/', complete_transaction, name='complete_transaction_ajax'),
    path('delete/<uuid:id>/', delete_transaction_ajax, name='delete_transaction_ajax'),
    path('json/', show_json, name='show_json'),
    path('json/<uuid:id>/', show_json_by_id, name='show_json_by_id'),
    path('transactions/json/', show_transactions_json, name='show_transactions_json'),
]
