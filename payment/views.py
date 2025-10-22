from django.shortcuts import render
from django.http import HttpResponse, JsonResponse

import uuid

class FakeTransaction:
    def __init__(self, payment_status, total_price, amount_paid):
        self.id = uuid.uuid4()
        self.payment_status = payment_status
        self.total_price = total_price
        self.amount_paid = amount_paid
        self.amount_due = total_price - amount_paid


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
