from decimal import Decimal
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from django.contrib.messages import get_messages
from unittest.mock import patch
from main.models import Product
from cart.models import Cart, CartItem
from payment.models import Transaction, TransactionProduct


# ===============================
# TESTING MODELS
# ===============================

class CartModelTests(TestCase):

    def setUp(self):
        # Buat user
        self.user = User.objects.create_user(username='testuser', password='password123')

        # Buat cart
        self.cart = Cart.objects.create(user=self.user)

        # Buat produk
        self.product1 = Product.objects.create(
            seller=None,
            product_name="Test Product 1",
            old_price=Decimal('100.00'),
            special_price=Decimal('80.00'),
            category='football',
            description="Desc 1",
            stock=10
        )
        self.product2 = Product.objects.create(
            seller=None,
            product_name="Test Product 2",
            old_price=Decimal('200.00'),
            special_price=Decimal('150.00'),
            category='cricket',
            description="Desc 2",
            stock=5
        )

        # Buat CartItem
        self.item1 = CartItem.objects.create(
            cart=self.cart,
            product=self.product1,
            quantity=2,
            price=self.product1.special_price
        )
        self.item2 = CartItem.objects.create(
            cart=self.cart,
            product=self.product2,
            quantity=1,
            price=self.product2.special_price
        )

    def test_cart_str_method(self):
        self.assertEqual(str(self.cart), f"Keranjang {self.user.username}")

    def test_cartitem_str_method(self):
        self.assertEqual(str(self.item1), f"{self.product1.product_name} x {self.item1.quantity}")

    def test_cartitem_subtotal(self):
        expected = self.item1.quantity * self.item1.price
        self.assertEqual(self.item1.subtotal(), expected)

    def test_cart_total_items(self):
        """Should sum all quantities (not number of distinct products)."""
        self.assertEqual(self.cart.total_items, 3)

    def test_cart_total_price(self):
        """Should calculate total correctly."""
        expected_total = (
            self.item1.quantity * self.item1.price +
            self.item2.quantity * self.item2.price
        )
        self.assertEqual(self.cart.total_price, expected_total)

    def test_unique_together_constraint(self):
        """Cannot add same product twice to same cart."""
        with self.assertRaises(Exception):
            CartItem.objects.create(
                cart=self.cart,
                product=self.product1,
                quantity=1,
                price=self.product1.special_price
            )

    def test_cartitem_foreign_keys(self):
        """Ensure relations to cart and product are correct."""
        self.assertEqual(self.item1.cart, self.cart)
        self.assertEqual(self.item1.product, self.product1)

    def test_cart_deleted_cascades_to_items(self):
        """Deleting cart should delete related items."""
        self.cart.delete()
        self.assertFalse(CartItem.objects.filter(pk=self.item1.pk).exists())
        self.assertFalse(CartItem.objects.filter(pk=self.item2.pk).exists())

    def test_cart_properties_empty_cart(self):
        """If no items exist, totals should be zero."""
        empty_cart = Cart.objects.create(user=User.objects.create_user('emptyuser', password='pass'))
        self.assertEqual(empty_cart.total_items, 0)
        self.assertEqual(empty_cart.total_price, Decimal('0.00'))


# ===============================
# TESTING VIEWS
# ===============================

class CartViewsTest(TestCase):
    def setUp(self):
        self.client = Client()

        # Create user & buyer profile mock
        self.user = User.objects.create_user(username='buyer', password='test123')
        self.user.profile.role = 'buyer'
        self.user.profile.address = 'Test Address'
        self.user.profile.save()

        # Another non-buyer user
        self.other_user = User.objects.create_user(username='seller', password='test123')
        self.other_user.profile.role = 'seller'
        self.other_user.profile.save()

        # Create product
        self.product = Product.objects.create(
            product_name='Test Product',
            old_price=100,
            special_price=80,
            stock=5
        )

        # Create cart for buyer
        self.cart = Cart.objects.create(user=self.user)

    def test_view_cart_requires_login(self):
        response = self.client.get(reverse('cart:view_cart'))
        self.assertEqual(response.status_code, 302)  # redirect to login

    def test_view_cart_for_buyer(self):
        self.client.login(username='buyer', password='test123')
        response = self.client.get(reverse('cart:view_cart'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'view_cart.html')
        self.assertIn('cart', response.context)

    def test_view_cart_forbidden_for_non_buyer(self):
        self.client.login(username='seller', password='test123')
        response = self.client.get(reverse('cart:view_cart'))
        self.assertEqual(response.status_code, 403)

    def test_add_to_cart_success(self):
        self.client.login(username='buyer', password='test123')
        response = self.client.get(reverse('cart:add_to_cart', args=[self.product.id]))
        self.assertEqual(response.status_code, 200)
        self.assertTrue(CartItem.objects.filter(cart__user=self.user, product=self.product).exists())

    def test_add_to_cart_forbidden_for_non_buyer(self):
        self.client.login(username='seller', password='test123')
        response = self.client.get(reverse('cart:add_to_cart', args=[self.product.id]))
        self.assertEqual(response.status_code, 403)

    def test_update_cart_item_success(self):
        self.client.login(username='buyer', password='test123')
        item = CartItem.objects.create(cart=self.cart, product=self.product, price=80, quantity=1)
        response = self.client.post(reverse('cart:update_cart_item', args=[item.id]), {'quantity': 3})
        self.assertEqual(response.status_code, 200)
        item.refresh_from_db()
        self.assertEqual(item.quantity, 3)

    def test_update_cart_item_invalid_quantity(self):
        self.client.login(username='buyer', password='test123')
        item = CartItem.objects.create(cart=self.cart, product=self.product, price=80, quantity=1)
        response = self.client.post(reverse('cart:update_cart_item', args=[item.id]), {'quantity': 0})
        self.assertJSONEqual(
            str(response.content, encoding='utf8'),
            {'success': False, 'error': 'Quantity must be at least 1.'}
        )

    def test_remove_from_cart_success(self):
        self.client.login(username='buyer', password='test123')
        item = CartItem.objects.create(cart=self.cart, product=self.product, price=80, quantity=1)
        response = self.client.get(reverse('cart:remove_from_cart', args=[item.id]))
        self.assertEqual(response.status_code, 200)
        self.assertFalse(CartItem.objects.filter(id=item.id).exists())

    def test_checkout_cart_post_success(self):
        self.client.login(username='buyer', password='test123')
        CartItem.objects.create(cart=self.cart, product=self.product, price=80, quantity=2)

        response = self.client.post(reverse('cart:checkout_cart'))
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('main:show_main'))
        self.assertFalse(self.cart.items.exists())
        self.assertTrue(Transaction.objects.filter(buyer=self.user).exists())

    def test_checkout_cart_get_redirect(self):
        """GET request to checkout_cart should redirect to checkout_review page."""
        product = Product.objects.create(
            product_name="Prod 1",
            old_price=100,
            special_price=80,
            category="football",
            description="desc",
            stock=10
        )
        CartItem.objects.create(cart=self.cart, product=product, price=product.special_price, quantity=1)
    
        response = self.client.get(reverse('cart:checkout_cart'))
        self.assertRedirects(response, reverse('cart:checkout_review'))

    def test_checkout_review_get_success(self):
        self.client.login(username='buyer', password='test123')
        CartItem.objects.create(cart=self.cart, product=self.product, price=80, quantity=2)

        response = self.client.get(reverse('cart:checkout_review'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'checkout_review.html')

    def test_checkout_review_post_clears_cart_and_redirects(self):
        self.client.login(username='buyer', password='test123')
        CartItem.objects.create(cart=self.cart, product=self.product, price=80, quantity=2)

        response = self.client.post(reverse('cart:checkout_review'))
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('payment:show_main'))

        # Check that cart is cleared
        self.assertFalse(self.cart.items.exists())

        # Check session data
        session = self.client.session
        self.assertIn('order_total', session)
        self.assertIn('order_items', session)

    def test_checkout_review_forbidden_for_non_buyer(self):
        self.client.login(username='seller', password='test123')
        response = self.client.get(reverse('cart:checkout_review'))
        self.assertEqual(response.status_code, 403)

class CartExtraTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='no_profile_user', password='12345')
        self.buyer = User.objects.create_user(username='buyer', password='12345')
        self.client.login(username='buyer', password='12345')
        self.cart = Cart.objects.create(user=self.buyer)
        self.product = Product.objects.create(
            product_name='Ball', old_price=100, special_price=90,
            category='football', description='desc', stock=5
        )

    def test_is_buyer_handles_missing_profile(self):
        from cart.views import is_buyer
        result = is_buyer(self.user)
        self.assertFalse(result)

    def test_add_to_cart_forbidden_for_non_buyer(self):
        from cart.views import add_to_cart
        self.client.logout()
        self.client.login(username='no_profile_user', password='12345')
        response = self.client.post(reverse('cart:add_to_cart', args=[self.product.id]))
        self.assertEqual(response.status_code, 403)

    def test_update_cart_item_invalid_quantity_value(self):
        item = CartItem.objects.create(cart=self.cart, product=self.product, price=90, quantity=1)
        response = self.client.post(reverse('cart:update_cart_item', args=[item.id]), {'quantity': 'abc'})
        self.assertEqual(response.status_code, 200)
        self.assertIn('Input quantity is not valid', response.json()['error'])

    def test_update_cart_item_invalid_method(self):
        item = CartItem.objects.create(cart=self.cart, product=self.product, price=90, quantity=1)
        response = self.client.get(reverse('cart:update_cart_item', args=[item.id]))
        self.assertEqual(response.status_code, 405)

    def test_remove_from_cart_forbidden(self):
        item = CartItem.objects.create(cart=self.cart, product=self.product, price=90, quantity=1)
        self.client.logout()
        self.client.login(username='no_profile_user', password='12345')
        response = self.client.post(reverse('cart:remove_from_cart', args=[item.id]))
        self.assertEqual(response.status_code, 403)

    def test_checkout_review_cart_empty_redirect(self):
        # Kosongkan cart
        response = self.client.get(reverse('cart:checkout_review'))
        self.assertEqual(response.status_code, 302)