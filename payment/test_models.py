from django.test import TestCase
from main.models import User, Product
from payment.models import Transaction, TransactionProduct
import uuid

# Create your tests here.
class TransactionTestCase(TestCase):

    def setUp(self):
        self.buyer = User.objects.create_user(username='Korbaniklan', password='qwerty')
        self.seller = User.objects.create_user(username='PT_HiperBola', password='pthiperbola')
        self.product = Product.objects.create(
            seller=self.seller,
            product_name="Gawang Lipat",
            old_price=1000000,
            special_price=999999,
            category='football',
            description="Gawang yang dapat dilipat agar mudah dibawa-bawa, terbuat dari titanium.",
            stock=10000,
        )

        self.transaction = Transaction.objects.create(
            buyer=self.buyer,
            amount_paid=0,
            payment_status='due',
        )

        self.transaction_product1 = TransactionProduct.objects.create(
            transaction = self.transaction,
            product = self.product,
            amount = 200,
            price = 30000,
        )

        self.transaction_product2 = TransactionProduct.objects.create(
            transaction = self.transaction,
            product = self.product,
            amount = 100,
            price = 50000,
        )

    def test_transaction_is_complete(self):
        self.assertFalse(self.transaction.is_complete)
        self.transaction.payment_status = 'paid'
        self.assertTrue(self.transaction.is_complete)

    def test_transaction_total_price(self):
        self.assertEqual(11000000, self.transaction.total_price)

    def test_transaction_amount_due(self):
        self.assertEqual(11000000, self.transaction.amount_due)
        self.transaction.amount_paid += 1000000
        self.assertEqual(10000000, self.transaction.amount_due)
