from django.test import TestCase
from django.urls import reverse
from main.models import User, Product
from payment.models import Transaction, TransactionProduct
import uuid

# Create your tests here.
class PaymentViewsTestCase(TestCase):

    def setUp(self):
        self.buyer = User.objects.create_user(username='Korbaniklan', password='qwerty')
        self.seller = User.objects.create_user(username='PT_HiperBola', password='pthiperbola')
        self.product1 = Product.objects.create(
            seller=self.seller,
            product_name="Gawang Lipat",
            old_price=1000000,
            special_price=999999,
            category='football',
            description="Gawang yang dapat dilipat agar mudah dibawa-bawa, terbuat dari titanium.",
            stock=10000,
        )
        self.product2 = Product.objects.create(
            seller=self.seller,
            product_name="Bola Homing",
            old_price=30000,
            special_price=29999,
            category='football',
            description="Bola ini dapat mendeteksi gawang di sekitarnya dengan teknologi sonar, lalu berbelok di udara ke arah gawang melalui motor internal dengan memanfaatkan efek Magnus.",
            stock=300,
        )

        self.due_transaction = Transaction.objects.create(
            buyer=self.buyer,
            amount_paid=0,
            payment_status='due',
        )

        self.transaction_product1 = TransactionProduct.objects.create(
            transaction = self.due_transaction,
            product = self.product1,
            amount = 200,
            price = 30000,
        )

        self.transaction_product2 = TransactionProduct.objects.create(
            transaction = self.due_transaction,
            product = self.product1,
            amount = 100,
            price = 50000,
        )

        self.completed_transaction = Transaction.objects.create(
            buyer=self.buyer,
            amount_paid=10000,
            payment_status='paid',
        )

        self.transaction_product3 = TransactionProduct.objects.create(
            transaction=self.completed_transaction,
            product=self.product1,
            amount=100,
            price=100,
        )

        self.fully_paid_transaction = Transaction.objects.create(
            buyer=self.buyer,
            amount_paid=10000,
            payment_status='due',
        )

        self.transaction_product4 = TransactionProduct.objects.create(
            transaction=self.fully_paid_transaction,
            product=self.product1,
            amount=100,
            price=100,
        )

    def test_pay_ajax_not_buyer(self):

        transaction = self.due_transaction

        url = reverse('payment:pay_ajax', args=[transaction.id])
        body = { 'pay-amount': 3000000 }
        self.client.force_login(self.seller)
        amount_paid_before = transaction.amount_paid

        response = self.client.post(url, body)
        data = response.json()

        self.assertEqual(403, response.status_code)
        self.assertEqual("error", data["status"])
        self.assertEqual("You can only pay for your own transactions!", data["message"])

        updated = Transaction.objects.get(pk=transaction.id)
        amount_paid_after = updated.amount_paid
        self.assertEqual(amount_paid_before, amount_paid_after)

    def test_pay_ajax_already_complete(self):

        transaction = self.completed_transaction

        url = reverse('payment:pay_ajax', args=[transaction.id])
        body = { 'pay-amount': 3000000 }
        self.client.force_login(self.buyer)
        amount_paid_before = transaction.amount_paid

        response = self.client.post(url, body)
        data = response.json()

        self.assertEqual(403, response.status_code)
        self.assertEqual("error", data["status"])
        self.assertEqual("Transaction is already complete.", data["message"])

        updated = Transaction.objects.get(pk=transaction.id)
        amount_paid_after = updated.amount_paid
        self.assertEqual(amount_paid_before, amount_paid_after)

    def test_pay_ajax_already_paid(self):

        transaction = self.fully_paid_transaction

        url = reverse('payment:pay_ajax', args=[transaction.id])
        body = { 'pay-amount': 3000000 }
        self.client.force_login(self.buyer)
        amount_paid_before = transaction.amount_paid

        response = self.client.post(url, body)
        data = response.json()

        self.assertEqual(403, response.status_code)
        self.assertEqual("error", data["status"])
        self.assertEqual("Transaction is already fully paid.", data["message"])

        updated = Transaction.objects.get(pk=transaction.id)
        amount_paid_after = updated.amount_paid
        self.assertEqual(amount_paid_before, amount_paid_after)

    def test_pay_ajax_negative_amount(self):

        transaction = self.due_transaction

        url = reverse('payment:pay_ajax', args=[transaction.id])
        body = { 'pay-amount': -3000000 }
        self.client.force_login(self.buyer)
        amount_paid_before = transaction.amount_paid

        response = self.client.post(url, body)
        data = response.json()

        self.assertEqual(403, response.status_code)
        self.assertEqual("error", data["status"])
        self.assertEqual("Payment amount must be positive!", data["message"])

        updated = Transaction.objects.get(pk=transaction.id)
        amount_paid_after = updated.amount_paid
        self.assertEqual(amount_paid_before, amount_paid_after)

    def test_pay_ajax_success(self):

        transaction = self.due_transaction

        url = reverse('payment:pay_ajax', args=[transaction.id])
        body = { 'pay-amount': 3000000 }
        self.client.force_login(self.buyer)
        amount_paid_before = transaction.amount_paid

        response = self.client.post(url, body)
        data = response.json()

        self.assertEqual(200, response.status_code)
        self.assertEqual("success", data["status"])
        self.assertEqual("Successfully added payment.", data["message"])

        updated = Transaction.objects.get(pk=transaction.id)
        amount_paid_after = updated.amount_paid
        self.assertEqual(amount_paid_before + 3000000, amount_paid_after)
