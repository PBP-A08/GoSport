from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from main.models import Profile
from django.conf import settings

class AuthProfileTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.register_url = reverse('main:register')
        self.login_url = reverse('main:login')
        self.profile_url = reverse('profile_dashboard:profile_dashboard')
        self.edit_profile_url = reverse('profile_dashboard:edit_profile')
        self.delete_account_url = reverse('profile_dashboard:delete_account')

        self.user = User.objects.create_user(username='testuser', password='password123')
        self.profile, _ = Profile.objects.get_or_create(user=self.user, defaults={'role': 'buyer'})

    def test_user_registration_creates_profile(self):
        response = self.client.post(self.register_url, {
            'username': 'newuser',
            'password': 'newpass123',
            'password2': 'newpass123',
            'role': 'buyer'
        })
        self.assertEqual(response.status_code, 302)  # Redirect ke login
        self.assertTrue(User.objects.filter(username='newuser').exists())

        new_user = User.objects.get(username='newuser')
        self.assertTrue(Profile.objects.filter(user=new_user).exists())
        self.assertEqual(new_user.profile.role, 'buyer')

    def test_login_valid_user(self):
        response = self.client.post(self.login_url, {
            'username': 'testuser',
            'password': 'password123'
        })
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('main:show_main'))

    def test_login_invalid_user(self):
        response = self.client.post(self.login_url, {
            'username': 'wronguser',
            'password': 'password123'
        })
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, self.login_url)
        messages = list(response.wsgi_request._messages)
        self.assertTrue(any("Account not found" in str(m) for m in messages))

    def test_view_profile_dashboard_authenticated(self):
        self.client.login(username='testuser', password='password123')
        response = self.client.get(self.profile_url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'testuser')
        self.assertContains(response, 'Buyer')

    def test_view_profile_dashboard_unauthenticated(self):
        response = self.client.get(self.profile_url)
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse('main:login').rstrip('/'), response.url)

    def test_edit_profile_updates_data(self):
        self.client.login(username='testuser', password='password123')
        response = self.client.post(self.edit_profile_url, {
            'username': 'updateduser',
            'address': 'Depok',
            'store_name': ''
        }, follow=True)
        self.assertEqual(response.status_code, 200)
        self.user.refresh_from_db()
        self.profile.refresh_from_db()
        self.assertEqual(self.user.username, 'updateduser')
        self.assertEqual(self.profile.address, 'Depok')

    def test_delete_account_removes_user(self):
        self.client.login(username='testuser', password='password123')
        response = self.client.post(self.delete_account_url, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertFalse(User.objects.filter(username='testuser').exists())
        self.assertFalse(Profile.objects.filter(user=self.user).exists())
