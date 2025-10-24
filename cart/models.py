from django.conf import settings
from django.db import models
from decimal import Decimal
from main.models import Product


class Cart(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='cart')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Keranjang {self.user.username}"

    @property
    def total_items(self):
        """Jumlah total item (bukan jenis produk)."""
        return self.items.aggregate(total=models.Sum('quantity'))['total'] or 0

    @property
    def total_price(self):
        """Hitung total harga dari semua item di keranjang."""
        total = Decimal('0.00')
        for item in self.items.all():
            total += item.quantity * item.price
        return total


class CartItem(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    price = models.DecimalField(max_digits=12, decimal_places=2)

    class Meta:
        unique_together = ('cart', 'product')

    def __str__(self):
        return f"{self.product.product_name} x {self.quantity}"

    def subtotal(self):
        """Hitung subtotal per item."""
        return self.quantity * self.price
