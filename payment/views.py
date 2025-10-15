from django.shortcuts import render

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
