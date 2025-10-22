from django.db import models
from django.contrib.auth.models import User
from main.models import Product
import uuid

# Create your models here.
class Transaction(models.Model):

    PAYMENT_STATUSES = [
        ('due', 'Belum Lunas'),
        ('paid', 'Lunas'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    buyer = models.ForeignKey(User, on_delete=models.CASCADE)
    amount_paid = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    payment_status = models.CharField(max_length=40, choices=PAYMENT_STATUSES, default='due')
    date = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    @property
    def is_complete(self):
        return self.payment_status == 'paid'

    @property
    def total_price(self):
        return sum(p.amount * p.price for p in self.entries.all())

    @property
    def amount_due(self):
        return self.total_price - self.amount_paid

    class Meta:
        constraints = [
        ]

class TransactionProduct(models.Model):

    transaction = models.ForeignKey(Transaction, on_delete=models.CASCADE, related_name='entries')
    product = models.ForeignKey(Product, on_delete=models.RESTRICT)
    amount = models.PositiveIntegerField()
    price = models.DecimalField(max_digits=12, decimal_places=2) # Note that there is no default price
