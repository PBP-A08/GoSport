import json
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from main.models import Profile


class ProfileDashboardTest(TestCase):
    """Test untuk view profile_dashboard"""
    
    def setUp(self):
        """Setup untuk setiap test"""
        self.client = Client()
        
        # Create buyer user
        self.buyer = User.objects.create_user(
            username='buyertest',
            password='testpass123'
        )
        # Get or update the profile created by signal
        self.buyer_profile, created = Profile.objects.get_or_create(
            user=self.buyer,
            defaults={'role': 'buyer', 'address': 'Jl. Test Buyer No. 123'}
        )
        if not created:
            self.buyer_profile.role = 'buyer'
            self.buyer_profile.address = 'Jl. Test Buyer No. 123'
            self.buyer_profile.save()
        
        # Create seller user
        self.seller = User.objects.create_user(
            username='sellertest',
            password='testpass123'
        )
        self.seller_profile, created = Profile.objects.get_or_create(
            user=self.seller,
            defaults={'role': 'seller', 'store_name': 'Test Store'}
        )
        if not created:
            self.seller_profile.role = 'seller'
            self.seller_profile.store_name = 'Test Store'
            self.seller_profile.save()
        
        # Create user without profile (delete profile if auto-created)
        self.user_no_profile = User.objects.create_user(
            username='noprofile',
            password='testpass123'
        )
        Profile.objects.filter(user=self.user_no_profile).delete()
    
    def test_profile_dashboard_not_logged_in(self):
        """Test akses profile dashboard tanpa login"""
        response = self.client.get(reverse('profile_dashboard:profile_dashboard'))
        self.assertEqual(response.status_code, 302)
        self.assertIn('/login', response.url)
    
    def test_profile_dashboard_buyer_logged_in(self):
        """Test profile dashboard untuk buyer yang sudah login"""
        self.client.login(username='buyertest', password='testpass123')
        response = self.client.get(reverse('profile_dashboard:profile_dashboard'))
        
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'profile_dashboard.html')
        self.assertEqual(response.context['username'], 'buyertest')
        self.assertEqual(response.context['role'], 'buyer')
        self.assertEqual(response.context['address'], 'Jl. Test Buyer No. 123')
        self.assertEqual(response.context['masked_password'], '••••••••')
    
    def test_profile_dashboard_seller_logged_in(self):
        """Test profile dashboard untuk seller yang sudah login"""
        self.client.login(username='sellertest', password='testpass123')
        response = self.client.get(reverse('profile_dashboard:profile_dashboard'))
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['username'], 'sellertest')
        self.assertEqual(response.context['role'], 'seller')
        self.assertEqual(response.context['store_name'], 'Test Store')
    
    def test_profile_dashboard_no_profile(self):
        """Test profile dashboard untuk user tanpa profile"""
        self.client.login(username='noprofile', password='testpass123')
        response = self.client.get(reverse('profile_dashboard:profile_dashboard'))
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['store_name'], '-')
        self.assertEqual(response.context['address'], '-')


class EditProfileTest(TestCase):
    """Test untuk view edit_profile"""
    
    def setUp(self):
        """Setup untuk setiap test"""
        self.client = Client()
        
        # Create buyer user
        self.buyer = User.objects.create_user(
            username='buyertest',
            password='testpass123'
        )
        self.buyer_profile, created = Profile.objects.get_or_create(
            user=self.buyer,
            defaults={'role': 'buyer', 'address': 'Old Address'}
        )
        if not created:
            self.buyer_profile.role = 'buyer'
            self.buyer_profile.address = 'Old Address'
            self.buyer_profile.save()
        
        # Create seller user
        self.seller = User.objects.create_user(
            username='sellertest',
            password='testpass123'
        )
        self.seller_profile, created = Profile.objects.get_or_create(
            user=self.seller,
            defaults={'role': 'seller', 'store_name': 'Old Store'}
        )
        if not created:
            self.seller_profile.role = 'seller'
            self.seller_profile.store_name = 'Old Store'
            self.seller_profile.save()
    
    def test_edit_profile_not_logged_in(self):
        """Test akses edit profile tanpa login"""
        response = self.client.get(reverse('profile_dashboard:edit_profile'))
        self.assertEqual(response.status_code, 302)
    
    def test_edit_profile_get_request(self):
        """Test GET request untuk edit profile"""
        self.client.login(username='buyertest', password='testpass123')
        response = self.client.get(reverse('profile_dashboard:edit_profile'))
        
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'edit_profile.html')
        self.assertEqual(response.context['role'], 'buyer')
    
    def test_edit_profile_buyer_json(self):
        """Test edit profile buyer dengan JSON request"""
        self.client.login(username='buyertest', password='testpass123')
        
        data = {
            'username': 'newbuyer',
            'address': 'New Address 456'
        }
        
        response = self.client.post(
            reverse('profile_dashboard:edit_profile'),
            data=json.dumps(data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.content)
        self.assertTrue(response_data['success'])
        
        # Verify changes
        self.buyer.refresh_from_db()
        self.buyer_profile.refresh_from_db()
        self.assertEqual(self.buyer.username, 'newbuyer')
        self.assertEqual(self.buyer_profile.address, 'New Address 456')
    
    def test_edit_profile_seller_json(self):
        """Test edit profile seller dengan JSON request"""
        self.client.login(username='sellertest', password='testpass123')
        
        data = {
            'username': 'newseller',
            'store_name': 'New Store Name'
        }
        
        response = self.client.post(
            reverse('profile_dashboard:edit_profile'),
            data=json.dumps(data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.content)
        self.assertTrue(response_data['success'])
        
        # Verify changes
        self.seller.refresh_from_db()
        self.seller_profile.refresh_from_db()
        self.assertEqual(self.seller.username, 'newseller')
        self.assertEqual(self.seller_profile.store_name, 'New Store Name')
    
    def test_edit_profile_json_error(self):
        """Test edit profile dengan invalid JSON"""
        self.client.login(username='buyertest', password='testpass123')
        
        response = self.client.post(
            reverse('profile_dashboard:edit_profile'),
            data='invalid json',
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 400)
        response_data = json.loads(response.content)
        self.assertFalse(response_data['success'])
    
    def test_edit_profile_form_post(self):
        """Test edit profile dengan form POST (non-JSON)"""
        self.client.login(username='buyertest', password='testpass123')
        
        response = self.client.post(
            reverse('profile_dashboard:edit_profile'),
            data={
                'username': 'formbuyer',
                'address': 'Form Address'
            }
        )
        
        # Should handle form submission (may redirect or render)
        self.assertIn(response.status_code, [200, 302])


class EditPasswordTest(TestCase):
    """Test untuk view edit_password"""
    
    def setUp(self):
        """Setup untuk setiap test"""
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            password='oldpass123'
        )
        Profile.objects.get_or_create(user=self.user, defaults={'role': 'buyer'})
    
    def test_edit_password_not_logged_in(self):
        """Test akses edit password tanpa login"""
        response = self.client.get(reverse('profile_dashboard:edit_password'))
        self.assertEqual(response.status_code, 302)
        self.assertIn('/login', response.url)
    
    def test_edit_password_get_request(self):
        """Test GET request untuk edit password"""
        self.client.login(username='testuser', password='oldpass123')
        response = self.client.get(reverse('profile_dashboard:edit_password'))
        
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'edit_password.html')
        self.assertIn('form', response.context)
    
    def test_edit_password_valid(self):
        """Test edit password dengan data valid"""
        self.client.login(username='testuser', password='oldpass123')
        
        response = self.client.post(
            reverse('profile_dashboard:edit_password'),
            data={
                'old_password': 'oldpass123',
                'new_password1': 'newpass456!@#',
                'new_password2': 'newpass456!@#'
            }
        )
        
        # Should redirect on success
        self.assertEqual(response.status_code, 302)
        
        # Verify password changed
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password('newpass456!@#'))
    
    def test_edit_password_wrong_old_password(self):
        """Test edit password dengan old password salah"""
        self.client.login(username='testuser', password='oldpass123')
        
        response = self.client.post(
            reverse('profile_dashboard:edit_password'),
            data={
                'old_password': 'wrongpass',
                'new_password1': 'newpass456!@#',
                'new_password2': 'newpass456!@#'
            }
        )
        
        self.assertEqual(response.status_code, 200)
        # Check that form has errors
        self.assertIn('form', response.context)
        self.assertTrue(response.context['form'].errors)
    
    def test_edit_password_mismatch(self):
        """Test edit password dengan konfirmasi tidak cocok"""
        self.client.login(username='testuser', password='oldpass123')
        
        response = self.client.post(
            reverse('profile_dashboard:edit_password'),
            data={
                'old_password': 'oldpass123',
                'new_password1': 'newpass456!@#',
                'new_password2': 'differentpass789'
            }
        )
        
        self.assertEqual(response.status_code, 200)
        # Check that form has errors
        self.assertIn('form', response.context)
        self.assertTrue(response.context['form'].errors)
    
    def test_edit_password_too_short(self):
        """Test edit password dengan password terlalu pendek"""
        self.client.login(username='testuser', password='oldpass123')
        
        response = self.client.post(
            reverse('profile_dashboard:edit_password'),
            data={
                'old_password': 'oldpass123',
                'new_password1': 'short',
                'new_password2': 'short'
            }
        )
        
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context['form'].errors)


class DeleteAccountTest(TestCase):
    """Test untuk view delete_account"""
    
    def setUp(self):
        """Setup untuk setiap test"""
        self.client = Client()
        self.user = User.objects.create_user(
            username='deletetest',
            password='testpass123'
        )
        Profile.objects.get_or_create(user=self.user, defaults={'role': 'buyer'})
    
    def test_delete_account_not_logged_in(self):
        """Test akses delete account tanpa login"""
        response = self.client.get(reverse('profile_dashboard:delete_account'))
        self.assertEqual(response.status_code, 302)
        self.assertIn('/login', response.url)
    
    def test_delete_account_get_request(self):
        """Test GET request untuk delete account (konfirmasi)"""
        self.client.login(username='deletetest', password='testpass123')
        response = self.client.get(reverse('profile_dashboard:delete_account'))
        
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'delete_account_confirm.html')
    
    def test_delete_account_post_success(self):
        """Test POST untuk delete account"""
        self.client.login(username='deletetest', password='testpass123')
        
        response = self.client.post(reverse('profile_dashboard:delete_account'))
        
        # Should redirect after deletion
        self.assertEqual(response.status_code, 302)
        
        # Verify user is deleted
        self.assertFalse(User.objects.filter(username='deletetest').exists())
    
    def test_delete_account_user_logged_out(self):
        """Test bahwa user logout setelah delete account"""
        self.client.login(username='deletetest', password='testpass123')
        
        response = self.client.post(reverse('profile_dashboard:delete_account'))
        
        # Check user is logged out
        response = self.client.get(reverse('profile_dashboard:profile_dashboard'))
        self.assertEqual(response.status_code, 302)  # Should redirect to login


class IntegrationTest(TestCase):
    """Integration test untuk flow lengkap"""
    
    def setUp(self):
        """Setup untuk integration test"""
        self.client = Client()
        self.user = User.objects.create_user(
            username='integrationtest',
            password='testpass123'
        )
        self.profile, created = Profile.objects.get_or_create(
            user=self.user,
            defaults={'role': 'buyer', 'address': 'Integration Address'}
        )
        if not created:
            self.profile.role = 'buyer'
            self.profile.address = 'Integration Address'
            self.profile.save()
    
    def test_full_profile_workflow(self):
        """Test complete workflow: view -> edit -> change password"""
        # Login
        login_success = self.client.login(
            username='integrationtest',
            password='testpass123'
        )
        self.assertTrue(login_success)
        
        # View profile dashboard
        response = self.client.get(reverse('profile_dashboard:profile_dashboard'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['username'], 'integrationtest')
        
        # Edit profile
        edit_data = {
            'username': 'updated_integration',
            'address': 'Updated Address'
        }
        response = self.client.post(
            reverse('profile_dashboard:edit_profile'),
            data=json.dumps(edit_data),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        
        # Verify edit
        self.user.refresh_from_db()
        self.assertEqual(self.user.username, 'updated_integration')
        
        # Change password
        response = self.client.post(
            reverse('profile_dashboard:edit_password'),
            data={
                'old_password': 'testpass123',
                'new_password1': 'newpassword456!@#',
                'new_password2': 'newpassword456!@#'
            }
        )
        self.assertEqual(response.status_code, 302)
        
        # Verify new password works
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password('newpassword456!@#'))
    
    def test_edit_then_delete_workflow(self):
        """Test workflow: edit profile -> delete account"""
        # Login
        self.client.login(username='integrationtest', password='testpass123')
        
        # Edit profile
        edit_data = {'username': 'todelete', 'address': 'Delete Address'}
        response = self.client.post(
            reverse('profile_dashboard:edit_profile'),
            data=json.dumps(edit_data),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        
        # Delete account
        response = self.client.post(reverse('profile_dashboard:delete_account'))
        self.assertEqual(response.status_code, 302)
        
        # Verify user is deleted
        self.assertFalse(User.objects.filter(username='todelete').exists())


class ProfileModelTest(TestCase):
    """Test untuk interaksi dengan Profile model"""
    
    def test_profile_str_method(self):
        """Test __str__ method dari Profile"""
        user = User.objects.create_user(username='teststr', password='pass123')
        profile, _ = Profile.objects.get_or_create(
            user=user,
            defaults={'role': 'buyer'}
        )
        self.assertEqual(str(profile), 'teststr - buyer')
    
    def test_profile_role_choices(self):
        """Test role choices pada Profile"""
        user = User.objects.create_user(username='roletest', password='pass123')
        profile, _ = Profile.objects.get_or_create(user=user)
        
        # Test buyer role
        profile.role = 'buyer'
        profile.save()
        self.assertEqual(profile.role, 'buyer')
        
        # Test seller role
        profile.role = 'seller'
        profile.save()
        self.assertEqual(profile.role, 'seller')