from django.db import transaction as db_transaction
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render, get_object_or_404
from django.utils.html import strip_tags
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from main.models import Product
from payment.models import Transaction
import uuid
import datetime

class FakeTransaction:
    def __init__(self, payment_status, total_price, amount_paid):
        self.id = uuid.uuid4()
        self.payment_status = payment_status
        self.total_price = total_price
        self.amount_paid = amount_paid
        self.amount_due = total_price - amount_paid
        self.date = datetime.datetime.now()
        self.updated_at = datetime.datetime.now()
        self.is_complete = self.payment_status == 'paid'


fake_transaction_data = [
    FakeTransaction("Paid", 300000, 300000),
    FakeTransaction("Paid", 300000, 300000),
    FakeTransaction("Due", 300000, 150000),
]

# Create your views here.
def show_main(request):
    context = {
        'transactions': fake_transaction_data,
    }

    return render(request, "index.html", context)

@require_POST
def pay(request, id):
    try:

        transaction = get_object_or_404(Transaction, pk=id)

        if request.user != transaction.buyer:
            return JsonResponse({
                "status": "error",
                "message": "Permission denied",
            }, status=403)

        if transaction.is_complete:
            return JsonResponse({
                "status": "error",
                "message": "Transaction is already complete.",
            }, status=403)

        if transaction.amount_paid > transaction.total_price:
            return JsonResponse({
                "status": "error",
                "message": "Transaction is already fully-paid.",
            }, status=403)

        amount = request.POST.get('pay-amount')
        if amount <= 0:
            return JsonResponse({
                "status": "error",
                "message": "Payment amount must be positive!",
            }, status=403)

        transaction.amount_paid += amount
        transaction.save()

        return JsonResponse({
            "status": "success",
            "message": "Successfully added payment.",
        }, status=200)

    except:
        return HttpResponse(status=500)

def complete_transaction(request, id):
 
    if not request.user.profile.is_admin:
        return JsonResponse({
            "status": "error",
            "message": "Permission denied",
        }, status=403)

    transaction = get_object_or_404(Transaction, pk=id)

    try:
        if transaction.payment_status == 'paid':
            return JsonResponse({
                "status": "error",
                "message": "Transaction is already complete.",
            }, status=403)

        if request.user == transaction.buyer:
            return JsonResponse({
                "status": "error",
                "message": "Cannot complete own transaction!",
            }, status=403)

        if transaction.amount_paid < transaction.total_price:
            return JsonResponse({
                "status": "error",
                "message": "Transaction must be fully paid before completion.",
            }, status=403)

        out_of_stock = [
            entry.product.name
            for entry in transaction.entries.all()
            if entry.amount > entry.product.stock
        ]

        if out_of_stock:
            return JsonResponse({
                "status": "error",
                "message": "The following product(s) are out of stock: " + ", ".join(out_of_stock)
            }, status=403)

        with db_transaction.atomic():
            for entry in transaction.entries.all():
                product = entry.product
                product.stock -= entry.amount
                product.save()

            transaction.amount_paid = transaction.total_price
            transaction.payment_status = 'paid'
            transaction.save()

        return JsonResponse({
            "status": "success",
            "message": "Successfully completed transaction.",
        }, status=200)

    except:
        return HttpResponse(status=500)

def delete_transaction_ajax(request, id):

    transaction = get_object_or_404(Transaction, pk=id)
    try:

        if request.user != transaction.buyer and not request.user.profile.is_admin:
            return JsonResponse({ 
                "status": "error",
                "message": "Permission denied",
            }, status=403)

        if transaction.is_complete:
            return JsonResponse({ 
                "status": "error",
                "message": "Cannot delete completed transaction!",
            }, status=403)

        transaction.delete()
        return JsonResponse({
            "status": "success",
            "message": "Successfully cancelled transaction.",
        }, status=200)

    except:
        return HttpResponse(status=500)

def show_json(request):

    if request.user.profile.is_admin:
        transactions = Transaction.objects.all()
    else:
        transactions = Transaction.objects.filter(buyer=request.user)

    data = [{
        "pk": str(tr.id),
        "model": "payment.transaction",
        "fields": {
            "total_price": float(tr.total_price),
            "amount_paid": float(tr.amount_paid),
            "amount_due": float(tr.amount_due),
            "payment_status": tr.payment_status,
            "date": tr.date.isoformat(),
            "updated_at": tr.updated_at.isoformat(),
            "is_complete": tr.is_complete,
            "entries": [{
                "id": e.product.id,
                "name": e.product.product_name,
                "amount": e.amount,
                "price": e.price,
            } for e in tr.entries.all()]
        }
    } for tr in transactions]

    return JsonResponse(data, safe=False)
