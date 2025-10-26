import uuid
import json
from decimal import Decimal
from django.test import TestCase
from django.urls import reverse
from django.contrib.auth.models import User
from main.models import Product, Profile
from unittest.mock import patch, MagicMock 
import re

def create_user_with_profile(username, password, role, is_superuser=False, is_staff=False):
    user = User.objects.create_user(username=username, password=password)
    user.is_superuser = is_superuser
    user.is_staff = is_staff
    user.save()
    profile, created = Profile.objects.get_or_create(user=user, defaults={'role': role, 'is_admin': (role == 'admin')})
    if not created:
        profile.role = role
        profile.is_admin = (role == 'admin')
        profile.save()
    return user, profile

class MainViewsSetup(TestCase):
    def setUp(self):
        self.buyer_user, self.buyer_profile = create_user_with_profile('testbuyer', 'password123', 'buyer')
        self.seller_user, self.seller_profile = create_user_with_profile('testseller', 'password123', 'seller')
        self.other_seller_user, self.other_seller_profile = create_user_with_profile('otherseller', 'password123', 'seller')
        self.admin_user, self.admin_profile = create_user_with_profile('testadmin', 'password123', 'admin', is_superuser=True, is_staff=True)

        self.product1_seller = Product.objects.create(
            seller=self.seller_user,
            product_name="Seller Product 1",
            old_price=Decimal('100.00'),
            special_price=Decimal('80.00'),
            category='cricket',
            description="Description for seller product 1",
            stock=10
        )
        self.product2_seller = Product.objects.create(
            seller=self.seller_user,
            product_name="Seller Product 2",
            old_price=Decimal('50.00'),
            special_price=Decimal('50.00'),
            category='football',
            description="Description for seller product 2",
            stock=5
        )
        self.product3_other = Product.objects.create(
            seller=self.other_seller_user,
            product_name="Other Seller Product",
            old_price=Decimal('120.00'),
            special_price=Decimal('110.00'),
            category='cricket',
            description="Description for other seller product",
            stock=20
        )
        self.product_no_seller = Product.objects.create(
            seller=None,
            product_name="External Product",
            old_price=Decimal('200.00'),
            special_price=Decimal('150.00'),
            category='accessory',
            description="No description for this product",
            stock=15
        )

        self.main_url = reverse('main:show_main')
        self.login_url = reverse('main:login')
        self.logout_url = reverse('main:logout')
        self.register_url = reverse('main:register')
        self.json_url = reverse('main:show_json')
        self.xml_url = reverse('main:show_xml')
        self.add_product_ajax_url = reverse('main:add_product_entry_ajax')


class AuthViewsTests(MainViewsSetup):
    databases = {'default', 'product_data'}
    
    def test_register_view_get(self):
        response = self.client.get(self.register_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'register.html')
        self.assertContains(response, 'Register', status_code=200)

    def test_register_view_post_success(self):
        user_count = User.objects.count()
        profile_count = Profile.objects.count()
        response = self.client.post(self.register_url, {
            'username': 'newuser',
            'password': 'password123',
            'password2': 'password123',
            'role': 'buyer'
        })
        self.assertEqual(User.objects.count(), user_count + 1)
        self.assertEqual(Profile.objects.count(), profile_count + 1)
        new_user = User.objects.get(username='newuser')
        self.assertEqual(new_user.profile.role, 'buyer')
        self.assertRedirects(response, self.login_url, status_code=302, target_status_code=200)

    def test_register_view_post_password_mismatch(self):
        response = self.client.post(self.register_url, {
            'username': 'newuser',
            'password': 'password123',
            'password2': 'password456',
            'role': 'buyer'
        })
        self.assertEqual(response.status_code, 200)
        self.assertIn('form', response.context)
        form = response.context['form']
        self.assertIn('__all__', form.errors)
        self.assertIn("Passwords don't match.", form.errors['__all__'])

    def test_register_view_post_username_exists(self):
        response = self.client.post(self.register_url, {
            'username': 'testbuyer', 
            'password': 'password123',
            'password2': 'password123',
            'role': 'buyer'
        })
        self.assertEqual(response.status_code, 200)
        self.assertIn('form', response.context)
        form = response.context['form']
        self.assertIn('username', form.errors)
        self.assertIn("Username sudah terpakai. Silakan pilih username lain.", form.errors['username'])

    def test_login_view_get(self):
        response = self.client.get(self.login_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'login.html')
        self.assertContains(response, 'Login', status_code=200)

    def test_login_view_post_wrong_password(self):
        response = self.client.post(self.login_url, {'username': self.buyer_user.username, 'password': 'wrongpassword'})
        self.assertRedirects(response, self.login_url, status_code=302, fetch_redirect_response=False)
        self.assertFalse('_auth_user_id' in self.client.session)
        response_after_redirect = self.client.get(self.login_url)
        messages = list(response_after_redirect.context['messages'])
        self.assertEqual(len(messages), 1)
        self.assertEqual(str(messages[0]), 'Wrong password. Please try again.')

    def test_login_view_post_nonexistent_user(self):
        response = self.client.post(self.login_url, {'username': 'nonexistent', 'password': 'password123'})
        self.assertRedirects(response, self.login_url, status_code=302, fetch_redirect_response=False)
        self.assertFalse('_auth_user_id' in self.client.session)
        response_after_redirect = self.client.get(self.login_url)
        messages = list(response_after_redirect.context['messages'])
        self.assertEqual(len(messages), 1)
        self.assertEqual(str(messages[0]), 'Account not found. Please register first.')

    def test_logout_view(self):
        self.client.login(username=self.buyer_user.username, password='password123')
        response = self.client.get(self.logout_url)
        self.assertRedirects(response, self.login_url, status_code=302, fetch_redirect_response=False)
        self.assertFalse('_auth_user_id' in self.client.session)
        self.assertTrue(response.cookies['last_login']['expires'].startswith('Thu, 01 Jan 1970'))

    def test_register_ajax_success(self):
        user_count_before = User.objects.count()
        response = self.client.post(self.register_url, {
            'username': 'ajaxuser',
            'password': 'password123',
            'password2': 'password123',
            'role': 'seller'
        }, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(User.objects.count(), user_count_before + 1)
        self.assertJSONEqual(str(response.content, encoding='utf8'), {'status': 'success', 'redirect_url': self.login_url})

    def test_register_ajax_fail(self):
        response = self.client.post(self.register_url, {
            'username': self.buyer_user.username,
            'password': 'password123',
            'password2': 'password456',
            'role': 'seller'
        }, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(data['status'], 'error')
        self.assertIn('errors', data)
        errors_dict = json.loads(data['errors'])
        self.assertIn('username', errors_dict)
        self.assertIn('__all__', errors_dict)

    def test_login_ajax_success(self):
        response = self.client.post(self.login_url, {'username': self.seller_user.username, 'password': 'password123'},
                                   HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(str(response.content, encoding='utf8'), {'status': 'success', 'redirect_url': self.main_url})
        self.assertTrue('_auth_user_id' in self.client.session)

    def test_login_ajax_fail_password(self):
        response = self.client.post(self.login_url, {'username': self.seller_user.username, 'password': 'wrong'},
                                   HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(str(response.content, encoding='utf8'), {'status': 'error', 'message': 'Wrong password. Please try again.'})
        self.assertFalse('_auth_user_id' in self.client.session)

    def test_login_ajax_fail_username(self):
        response = self.client.post(self.login_url, {'username': 'nonexistent', 'password': 'password123'},
                                   HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(str(response.content, encoding='utf8'), {'status': 'error', 'message': 'Account not found. Please register first.'})
        self.assertFalse('_auth_user_id' in self.client.session)

    # NEW: Test admin login flow
    @patch.dict('os.environ', {'ADMIN_PASSWORD': 'testadminpass'})
    def test_login_admin_creates_superuser(self):
        # Delete admin if exists
        User.objects.filter(username='admin').delete()
        
        response = self.client.post(self.login_url, {
            'username': 'admin',
            'password': 'testadminpass'
        })
        
        self.assertRedirects(response, self.main_url, status_code=302, fetch_redirect_response=False)
        admin_user = User.objects.get(username='admin')
        self.assertTrue(admin_user.is_superuser)
        self.assertTrue(admin_user.is_staff)

    @patch.dict('os.environ', {'ADMIN_PASSWORD': 'testadminpass'})
    def test_login_admin_ajax(self):
        User.objects.filter(username='admin').delete()
        
        response = self.client.post(self.login_url, {
            'username': 'admin',
            'password': 'testadminpass'
        }, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(data['status'], 'success')
        self.assertEqual(data['redirect_url'], self.main_url)


class MainPageViewTests(MainViewsSetup):
    databases = {'default', 'product_data'}

    # NEW: Test show_main with mocked external database
    @patch('main.views.ProductsData.objects')
    def test_show_main_view_logged_in_buyer(self, mock_products_data):
        mock_db = MagicMock()
        mock_db.all.return_value = []
        mock_products_data.using.return_value = mock_db
        
        self.client.login(username=self.buyer_user.username, password='password123')
        response = self.client.get(self.main_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'main.html')
        self.assertIn(self.product1_seller, response.context['product_list'])
        self.assertEqual(response.context['role'], 'buyer')

    @patch('main.views.ProductsData.objects')
    def test_show_main_view_logged_in_seller(self, mock_products_data):
        mock_db = MagicMock()
        mock_db.all.return_value = []
        mock_products_data.using.return_value = mock_db
        
        self.client.login(username=self.seller_user.username, password='password123')
        response = self.client.get(self.main_url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['role'], 'seller')
        self.assertIn(self.product1_seller, response.context['product_list'])

    @patch('main.views.ProductsData.objects')
    def test_show_main_view_seller_my_products_filter(self, mock_products_data):
        mock_db = MagicMock()
        mock_db.all.return_value = []
        mock_products_data.using.return_value = mock_db
        
        self.client.login(username=self.seller_user.username, password='password123')
        response = self.client.get(self.main_url + '?filter=my')
        self.assertEqual(response.status_code, 200)
        product_list_context = response.context['product_list']
        self.assertIn(self.product1_seller, product_list_context)
        self.assertIn(self.product2_seller, product_list_context)
        self.assertNotIn(self.product3_other, product_list_context)

    @patch('main.views.ProductsData.objects')
    def test_show_main_view_category_filter(self, mock_products_data):
        mock_db = MagicMock()
        mock_db.all.return_value = []
        mock_products_data.using.return_value = mock_db
        
        self.client.login(username=self.buyer_user.username, password='password123')
        response = self.client.get(self.main_url + '?category=cricket')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['selected_category'], 'cricket')
        product_list_context = response.context['product_list']
        self.assertIn(self.product1_seller, product_list_context)
        self.assertIn(self.product3_other, product_list_context)
        self.assertNotIn(self.product2_seller, product_list_context)

    @patch('main.views.ProductsData.objects')
    def test_show_main_view_admin(self, mock_products_data):
        mock_db = MagicMock()
        mock_db.all.return_value = []
        mock_products_data.using.return_value = mock_db
        
        self.client.login(username=self.admin_user.username, password='password123')
        response = self.client.get(self.main_url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['role'], 'admin')
        self.assertTrue(response.context['is_admin'])

    # NEW: Test user without profile
    @patch('main.views.ProductsData.objects')
    def test_show_main_user_without_profile_defaults_to_buyer(self, mock_products_data):
        mock_db = MagicMock()
        mock_db.all.return_value = []
        mock_products_data.using.return_value = mock_db
        
        # Create user without profile
        user_no_profile = User.objects.create_user(username='noprofile', password='pass123')
        Profile.objects.filter(user=user_no_profile).delete()
        
        self.client.login(username='noprofile', password='pass123')
        response = self.client.get(self.main_url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['role'], 'buyer')


class ProductDetailViewTests(MainViewsSetup):
    def test_show_product_view_context(self):
        self.client.login(username=self.buyer_user.username, password='password123')
        detail_url = reverse('main:show_product', args=[self.product1_seller.id])
        response = self.client.get(detail_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'product_detail.html')
        self.assertEqual(response.context['product'], self.product1_seller)
        self.assertEqual(str(response.context['product_id']), str(self.product1_seller.id))

    def test_show_product_view_404_for_invalid_id(self):
        self.client.login(username=self.buyer_user.username, password='password123')
        invalid_uuid = uuid.uuid4()
        detail_url = reverse('main:show_product', args=[invalid_uuid])
        response = self.client.get(detail_url)
        self.assertEqual(response.status_code, 404)

    def test_show_product_can_modify_owner(self):
        self.client.login(username=self.seller_user.username, password='password123')
        detail_url = reverse('main:show_product', args=[self.product1_seller.id])
        response = self.client.get(detail_url)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context['can_modify'])

    def test_show_product_can_modify_admin(self):
        self.client.login(username=self.admin_user.username, password='password123')
        detail_url = reverse('main:show_product', args=[self.product1_seller.id])
        response = self.client.get(detail_url)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context['can_modify'])

    def test_show_product_cannot_modify_other_user(self):
        self.client.login(username=self.buyer_user.username, password='password123')
        detail_url = reverse('main:show_product', args=[self.product1_seller.id])
        response = self.client.get(detail_url)
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.context['can_modify'])

        self.client.logout()
        self.client.login(username=self.other_seller_user.username, password='password123')
        response = self.client.get(detail_url)
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.context['can_modify'])


@patch('main.views.ProductsData.objects')
@patch('django.conf.settings')
class SerializationViewsTests(MainViewsSetup):
    def test_show_json(self, mock_settings, mock_products_data_manager):
        mock_settings.DATABASES = {'default': {}, 'product_data': {}}
        mock_db = MagicMock()
        mock_db.all.return_value = []
        mock_products_data_manager.using.return_value = mock_db

        self.client.login(username=self.buyer_user.username, password='password123')
        response = self.client.get(self.json_url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['content-type'], 'application/json')
        data = json.loads(response.content)
        self.assertEqual(len(data), 4)
        product_names = [item['fields']['product_name'] for item in data]
        self.assertIn(self.product1_seller.product_name, product_names)

    def test_show_xml(self, mock_settings, mock_products_data_manager):
        self.client.login(username=self.buyer_user.username, password='password123')
        response = self.client.get(self.xml_url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['content-type'], 'application/xml')
        content = response.content.decode('utf-8')
        self.assertIn('<django-objects version="1.0">', content)
        self.assertIn('</django-objects>', content)

    def test_show_json_by_id_success(self, mock_settings, mock_products_data_manager):
        self.client.login(username=self.buyer_user.username, password='password123')
        detail_url = reverse('main:show_json_by_id', args=[self.product1_seller.id])
        response = self.client.get(detail_url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['content-type'], 'application/json')
        data = json.loads(response.content)
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]['pk'], str(self.product1_seller.id))
        self.assertEqual(data[0]['fields']['product_name'], self.product1_seller.product_name)

    def test_show_json_by_id_success_with_store_name(self, mock_settings, mock_products_data_manager):
        self.seller_profile.store_name = "Seller Store"
        self.seller_profile.save()
        self.client.login(username=self.buyer_user.username, password='password123')
        detail_url = reverse('main:show_json_by_id', args=[self.product1_seller.id])
        response = self.client.get(detail_url)
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(data[0]['fields']['seller_display'], "Seller Store")

    def test_show_json_by_id_no_seller(self, mock_settings, mock_products_data_manager):
        self.client.login(username=self.buyer_user.username, password='password123')
        detail_url = reverse('main:show_json_by_id', args=[self.product_no_seller.id])
        response = self.client.get(detail_url)
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertIsNone(data[0]['fields']['seller'])
        self.assertEqual(data[0]['fields']['seller_username'], "N/A")

    def test_show_json_by_id_not_found(self, mock_settings, mock_products_data_manager):
        self.client.login(username=self.buyer_user.username, password='password123')
        invalid_uuid = uuid.uuid4()
        detail_url = reverse('main:show_json_by_id', args=[invalid_uuid])
        response = self.client.get(detail_url)
        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(str(response.content, encoding='utf8'), [])

    def test_show_xml_by_id_success(self, mock_settings, mock_products_data_manager):
        self.client.login(username=self.buyer_user.username, password='password123')
        detail_url = reverse('main:show_xml_by_id', args=[self.product1_seller.id])
        response = self.client.get(detail_url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['content-type'], 'application/xml')
        content = response.content.decode('utf-8')
        self.assertIn('</django-objects>', content)


class AjaxCRUDTests(MainViewsSetup):
    def test_add_product_ajax_success(self):
        self.client.login(username=self.seller_user.username, password='password123')
        product_count_before = Product.objects.count()
        response = self.client.post(self.add_product_ajax_url, {
            'product_name': 'New AJAX Product',
            'old_price': '150.00',
            'special_price': '125.50',
            'category': 'accessory',
            'description': 'AJAX Description',
            'stock': '5'
        })
        self.assertEqual(response.status_code, 201)
        self.assertEqual(Product.objects.count(), product_count_before + 1)
        new_product = Product.objects.latest('created_at')
        self.assertEqual(new_product.product_name, 'New AJAX Product')
        self.assertEqual(new_product.seller, self.seller_user)

    def test_add_product_ajax_invalid_data(self):
        self.client.login(username=self.seller_user.username, password='password123')
        response = self.client.post(self.add_product_ajax_url, {
            'product_name': 'Invalid Price Product',
            'old_price': 'abc',
            'special_price': '100.00',
            'stock': '10',
            'category': 'football',
        })
        self.assertEqual(response.status_code, 400)
        self.assertIn(b"Invalid input", response.content)

    def test_add_product_ajax_missing_name(self):
        self.client.login(username=self.seller_user.username, password='password123')
        response = self.client.post(self.add_product_ajax_url, {
            'product_name': '',
            'description': 'No name product',
            'old_price': '10.00',
            'special_price': '5.00',
            'stock': '5',
        })
        self.assertEqual(response.status_code, 400)

    def test_edit_product_ajax_success_owner(self):
        self.client.login(username=self.seller_user.username, password='password123')
        edit_url = reverse('main:edit_product_ajax', args=[self.product1_seller.id])
        response = self.client.post(edit_url, {
            'product_name': 'Updated Seller Product 1',
            'old_price': '110.00',
            'special_price': '90.00',
            'category': 'football',
            'description': 'Updated Description',
            'stock': '15',
            'discount_percent': '18'
        })
        self.assertEqual(response.status_code, 200)
        self.product1_seller.refresh_from_db()
        self.assertEqual(self.product1_seller.product_name, 'Updated Seller Product 1')
        self.assertEqual(self.product1_seller.stock, 15)

    def test_edit_product_ajax_success_admin(self):
        self.client.login(username=self.admin_user.username, password='password123')
        edit_url = reverse('main:edit_product_ajax', args=[self.product1_seller.id])
        response = self.client.post(edit_url, {
            'product_name': 'Admin Updated Product 1',
            'stock': '99',
            'old_price': self.product1_seller.old_price,
            'special_price': self.product1_seller.special_price,
            'category': self.product1_seller.category,
            'discount_percent': '0',
        })
        self.assertEqual(response.status_code, 200)
        self.product1_seller.refresh_from_db()
        self.assertEqual(self.product1_seller.stock, 99)

    def test_edit_product_ajax_unauthorized(self):
        self.client.login(username=self.buyer_user.username, password='password123')
        edit_url = reverse('main:edit_product_ajax', args=[self.product1_seller.id])
        response = self.client.post(edit_url, {
            'product_name': 'Attempted Update',
            'old_price': '100', 'special_price': '80', 'category': 'cricket', 'stock': '1', 'discount_percent': '0'
        })
        self.assertEqual(response.status_code, 403)

    def test_edit_product_ajax_not_found(self):
        self.client.login(username=self.seller_user.username, password='password123')
        invalid_uuid = uuid.uuid4()
        edit_url = reverse('main:edit_product_ajax', args=[invalid_uuid])
        response = self.client.post(edit_url, {
            'product_name': 'Attempted Update',
            'old_price': '100', 'special_price': '80', 'category': 'cricket', 'stock': '1', 'discount_percent': '0'
        })
        self.assertEqual(response.status_code, 404)
    def test_edit_product_ajax_invalid_numeric(self):
        self.client.login(username=self.seller_user.username, password='password123')
        edit_url = reverse('main:edit_product_ajax', args=[self.product1_seller.id])
        response = self.client.post(edit_url, {
            'product_name': 'Bad Price',
            'old_price': 'abc',
            'special_price': '90.00',
            'category': 'football',
            'stock': '15',
            'discount_percent': '18'
        })
        self.assertEqual(response.status_code, 400)
        self.assertJSONEqual(str(response.content, encoding='utf8'), {"status": "error", "message": "Invalid numeric input."})

    def test_delete_product_ajax_success_owner(self):
        product_to_delete = Product.objects.create(
            seller=self.seller_user, product_name="To Be Deleted", old_price=10, special_price=8, category='hockey', stock=1
        )
        self.client.login(username=self.seller_user.username, password='password123')
        delete_url = reverse('main:delete_product_ajax', args=[product_to_delete.id])
        product_count_before = Product.objects.count()
        response = self.client.post(delete_url)
        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(str(response.content, encoding='utf8'), {"status": "success", "message": "Product deleted successfully"})
        self.assertEqual(Product.objects.count(), product_count_before - 1)
        with self.assertRaises(Product.DoesNotExist):
            Product.objects.get(pk=product_to_delete.id)

    def test_delete_product_ajax_success_admin(self):
        product_to_delete = Product.objects.create(
            seller=self.seller_user, product_name="Admin Delete Me", old_price=10, special_price=8, category='hockey', stock=1
        )
        self.client.login(username=self.admin_user.username, password='password123')
        delete_url = reverse('main:delete_product_ajax', args=[product_to_delete.id])
        product_count_before = Product.objects.count()
        response = self.client.post(delete_url)
        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(str(response.content, encoding='utf8'), {"status": "success", "message": "Product deleted successfully"})
        self.assertEqual(Product.objects.count(), product_count_before - 1)
        with self.assertRaises(Product.DoesNotExist):
            Product.objects.get(pk=product_to_delete.id)

    def test_delete_product_ajax_unauthorized(self):
        self.client.login(username=self.buyer_user.username, password='password123')
        delete_url = reverse('main:delete_product_ajax', args=[self.product1_seller.id])
        response = self.client.post(delete_url)
        self.assertEqual(response.status_code, 403)
        self.assertJSONEqual(str(response.content, encoding='utf8'), {
            "status": "error",
            "message": "You are not authorized to delete this product."
        })
        self.assertTrue(Product.objects.filter(pk=self.product1_seller.id).exists())

        self.client.logout()
        self.client.login(username=self.other_seller_user.username, password='password123')
        response = self.client.post(delete_url)
        self.assertEqual(response.status_code, 403)
        self.assertTrue(Product.objects.filter(pk=self.product1_seller.id).exists())

    def test_delete_product_ajax_requires_post(self):
        self.client.login(username=self.seller_user.username, password='password123')
        delete_url = reverse('main:delete_product_ajax', args=[self.product1_seller.id])
        response = self.client.get(delete_url)
        self.assertEqual(response.status_code, 405)


class HelperFunctionTests(TestCase):

    def test_infer_category(self):
        from main.views import infer_category
        self.assertEqual(infer_category("Yonex Badminton Racket"), "Badminton")
        self.assertEqual(infer_category("SG Cricket Bat"), "Cricket")
        self.assertEqual(infer_category("NIVIA Volleyball PU 5000"), "Volleyball")
        self.assertEqual(infer_category("Swimming Goggles"), "Accessory")
        self.assertEqual(infer_category("A generic item"), "Accessory")
        self.assertEqual(infer_category(None), "Accessory")
        self.assertEqual(infer_category(""), "Accessory")