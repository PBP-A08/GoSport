from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from main.models import Product
from rating.models import ProductReview

class ProductReviewAjaxTests(TestCase):
    def setUp(self):
        # Buat user
        self.user = User.objects.create_user(username='tester', password='12345')
        self.client = Client()
        self.client.login(username='tester', password='12345')

        # Buat product
        self.product = Product.objects.create(
            product_name="Test Product",
            description="Desc",
            category="Category",
            old_price=100,
            special_price=80,
            discount_percent=20,
            stock=10
        )
    
    def test_add_review_ajax_success(self):
        url = reverse('rating:add_review_ajax', args=[self.product.id])
        data = {'rating': 4, 'review': 'Good product'}
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 201)
        self.assertTrue(ProductReview.objects.filter(product=self.product, user=self.user).exists())

    def test_add_review_ajax_invalid_rating(self):
        url = reverse('rating:add_review_ajax', args=[self.product.id])
        data = {'rating': 10, 'review': 'Bad rating'}
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 400)
        self.assertIn("error", response.json())

    def test_edit_review_ajax_success(self):
        # buat review dulu
        review = ProductReview.objects.create(product=self.product, user=self.user, rating=3, review='Old review')
        url = reverse('rating:edit_review_ajax', args=[self.product.id])
        data = {'rating': 5, 'review': 'Updated review'}
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 200)
        review.refresh_from_db()
        self.assertEqual(review.rating, 5)
        self.assertEqual(review.review, 'Updated review')

    def test_edit_review_ajax_not_found(self):
        url = reverse('rating:edit_review_ajax', args=[self.product.id])
        data = {'rating': 5, 'review': 'Updated review'}
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 404)

    def test_delete_review_ajax_success(self):
        review = ProductReview.objects.create(product=self.product, user=self.user, rating=3, review='To delete')
        url = reverse('rating:delete_review_ajax', args=[self.product.id])
        response = self.client.delete(url)
        self.assertEqual(response.status_code, 200)
        self.assertFalse(ProductReview.objects.filter(id=review.id).exists())

    def test_delete_review_ajax_not_found(self):
        url = reverse('rating:delete_review_ajax', args=[self.product.id])
        response = self.client.delete(url)
        self.assertEqual(response.status_code, 404)

    def test_show_rating_review_ajax(self):
        # buat beberapa review
        other_user = User.objects.create_user(username='other', password='123')
        ProductReview.objects.create(product=self.product, user=self.user, rating=4, review='Mine')
        ProductReview.objects.create(product=self.product, user=other_user, rating=5, review='Other')

        url = reverse('rating:show_rating_review_ajax', args=[self.product.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(len(data['reviews']), 2)
        # cek is_owner
        mine_review = next(r for r in data['reviews'] if r['user']=='tester')
        self.assertTrue(mine_review['is_owner'])

    def test_helper_function_has_review(self):
        ProductReview.objects.create(product=self.product, user=self.user, rating=5, review='Check')
        url = reverse('rating:helper_function', args=[self.product.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()['has_review'])
        self.assertEqual(response.json()['rating'], 5)

    def test_helper_function_no_review(self):
        url = reverse('rating:helper_function', args=[self.product.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.json()['has_review'])

# Create your tests here.
