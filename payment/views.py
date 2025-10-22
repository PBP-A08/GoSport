from django.shortcuts import render
from django.http import HttpResponse, JsonResponse

import uuid

class FakeTransaction:
    def __init__(self, payment_status, shipping_status, amount, amount_paid):
        self.id = uuid.uuid4()
        self.payment_status = payment_status
        self.shipping_status = shipping_status
        self.amount = amount
        self.amount_paid = amount_paid

# Create your views here.
def show_main(request):

    fake_transaction_data = [
        FakeTransaction("Lunas", "Menunggu Pengantar", 300000, 300000),
        FakeTransaction("Lunas", "Menunggu Pengantar", 300000, 300000),
        FakeTransaction("Lunas", "Menunggu Pengantar", 300000, 300000),
        FakeTransaction("Lunas", "Menunggu Pengantar", 300000, 300000),
        FakeTransaction("Lunas", "Menunggu Pengantar", 300000, 300000),
        FakeTransaction("Lunas", "Menunggu Pengantar", 300000, 300000),
        FakeTransaction("Lunas", "Menunggu Pengantar", 300000, 300000),
        FakeTransaction("Lunas", "Menunggu Pengantar", 300000, 300000),
        FakeTransaction("Lunas", "Menunggu Pengantar", 300000, 300000),
        FakeTransaction("Lunas", "Menunggu Pengantar", 300000, 300000),
        FakeTransaction("Lunas", "Menunggu Pengantar", 300000, 300000),
        FakeTransaction("Lunas", "Menunggu Pengantar", 300000, 300000),
        FakeTransaction("Lunas", "Menunggu Pengantar", 300000, 300000),
        FakeTransaction("Lunas", "Menunggu Pengantar", 300000, 300000),
        FakeTransaction("Lunas", "Menunggu Pengantar", 300000, 300000),
        FakeTransaction("Lunas", "Menunggu Pengantar", 300000, 300000),
        FakeTransaction("Lunas", "Menunggu Pengantar", 300000, 300000),
        FakeTransaction("Lunas", "Menunggu Pengantar", 300000, 300000),
        FakeTransaction("Lunas", "Menunggu Pengantar", 300000, 300000),
        FakeTransaction("Lunas", "Menunggu Pengantar", 300000, 300000),
        FakeTransaction("Lunas", "Menunggu Pengantar", 300000, 300000),
        FakeTransaction("Lunas", "Menunggu Pengantar", 300000, 300000),
        FakeTransaction("Lunas", "Menunggu Pengantar", 300000, 300000),
        FakeTransaction("Lunas", "Menunggu Pengantar", 300000, 300000),
        FakeTransaction("Lunas", "Menunggu Pengantar", 300000, 300000),
        FakeTransaction("Lunas", "Menunggu Pengantar", 300000, 300000),
        FakeTransaction("Lunas", "Menunggu Pengantar", 300000, 300000),
        FakeTransaction("Lunas", "Menunggu Pengantar", 300000, 300000),
        FakeTransaction("Lunas", "Menunggu Pengantar", 300000, 300000),
        FakeTransaction("Lunas", "Menunggu Pengantar", 300000, 300000),
    ]

    context = {
        'transactions': fake_transaction_data,
    }

    return render(request, "index.html", context)

def delete_transaction_ajax(request, id):
    try:

        transaction = get_object_or_404(Product, pk=id)

        if request.user != transaction.buyer:
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
