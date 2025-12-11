from django.db import models
from django.contrib.auth.models import User
from main.models import Product
from django.db.models import Avg
# Create your models here.

class ProductReview(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='reviews')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reviews')
    rating = models.PositiveSmallIntegerField()
    review = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('product', 'user')  # 1 user hanya bisa 1 review per product

    def __str__(self):
        return f"{self.product.name} - {self.user.username} ({self.rating})"
    
    def update_avg_rating(product):
        avg = ProductReview.objects.filter(product=product).aggregate(avg=Avg('rating'))['avg'] or 0.0
        product.avg_rating = round(avg, 1)
        product.save()