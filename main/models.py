import uuid
from django.db import models
from django.contrib.auth.models import User

class Profile(models.Model):
    ROLE_CHOICES = [
        ('pembeli', 'Pembeli'),
        ('penjual', 'Penjual'),
    ]
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='pembeli')
    is_admin = models.BooleanField(default=False)
    
    def __str__(self):
        return f"{self.user.username} - {self.role}"

class Product(models.Model):
    CATEGORY_CHOICES = [
        ('shoes', 'Shoes'),
        ('racket', 'Racket'),
        ('ball', 'Ball'),
        ('gym', 'Gym Equipment'),
        ('apparel', 'Sports Apparel'),
        ('accessory', 'Accessory'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    seller = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    product_name = models.CharField(max_length=255)
    old_price = models.DecimalField(max_digits=12, decimal_places=2)
    special_price = models.DecimalField(max_digits=12, decimal_places=2)
    discount_percent = models.PositiveIntegerField(default=0)
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES, default='shoes')
    description = models.TextField(blank=True, null=True)
    thumbnail = models.URLField(blank=True, null=True)
    stock = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.product_name

    @property
    def is_discounted(self):
        return self.discount_percent > 0

    def calculate_discount(self):
        if self.old_price > 0:
            self.discount_percent = round(
                (1 - (self.special_price / self.old_price)) * 100
            )
            self.save()
        return self.discount_percent
