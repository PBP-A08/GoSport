from django.http import JsonResponse
from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden
from .models import Cart, CartItem
from main.models import Product
from payment.models import Transaction, TransactionProduct

def is_buyer(user):
    """Pastikan hanya user dengan role 'pembeli' yang bisa akses keranjang."""
    try:
        return hasattr(user, 'profile') and user.profile.role == 'pembeli'
    except Exception:
        return False


@login_required
def view_cart(request):
    """Tampilkan isi keranjang belanja user."""
    if not is_buyer(request.user):
        return HttpResponseForbidden("Hanya pembeli yang dapat mengakses keranjang.")

    cart, _ = Cart.objects.get_or_create(user=request.user)
    context = {
        'cart': cart,
        'items': cart.items.all(),
        'total_price': cart.total_price,
    }
    return render(request, 'cart/view_cart.html', context)


@login_required
def add_to_cart(request, product_id):
    if not is_buyer(request.user):
        return HttpResponseForbidden("Hanya pembeli yang dapat menambahkan ke keranjang.")
    
    # langsung gunakan product_id yang diterima dari URL
    product = get_object_or_404(Product, id=product_id)
    cart, _ = Cart.objects.get_or_create(user=request.user)
    product_price = product.special_price or product.old_price

    item, created = CartItem.objects.get_or_create(
        cart=cart,
        product=product,
        defaults={'price': product_price}
    )

    if not created:
        item.quantity += 1
        item.save()

    messages.success(request, f"{product.product_name} berhasil ditambahkan ke keranjang.")
    return redirect('main:show_main')  

@login_required
def update_cart_item(request, item_id):
    """Ubah jumlah item di keranjang."""
    if not is_buyer(request.user):
        return JsonResponse({'success': False, 'error': 'Hanya pembeli yang dapat mengubah item.'}, status=403)

    item = get_object_or_404(CartItem, id=item_id, cart__user=request.user)

    if request.method == "POST":
        try:
            qty = int(request.POST.get('quantity', 1))
            if qty < 1:
                return JsonResponse({'success': False, 'error': 'Jumlah tidak boleh kurang dari 1.'})
            item.quantity = qty
            item.save()
            cart = item.cart
            return JsonResponse({
                'success': True,
                'message': f"Jumlah {item.product.product_name} diperbarui.",
                'total_price': float(cart.total_price)
            })
        except ValueError:
            return JsonResponse({'success': False, 'error': 'Input jumlah tidak valid.'})

    return JsonResponse({'success': False, 'error': 'Metode tidak diizinkan.'}, status=405)


@login_required
def remove_from_cart(request, item_id):
    """Hapus item dari keranjang (AJAX)."""
    if not is_buyer(request.user):
        return JsonResponse({'success': False, 'error': 'Hanya pembeli yang dapat menghapus item.'}, status=403)

    item = get_object_or_404(CartItem, id=item_id, cart__user=request.user)
    product_name = item.product.product_name
    item.delete()

    cart = item.cart
    return JsonResponse({
        'success': True,
        'message': f"{product_name} dihapus dari keranjang.",
        'total_price': float(cart.total_price)
    })

def checkout_cart(request):
    cart = getattr(request.user, 'cart', None)
    if not cart or not cart.items.exists():
        messages.warning(request, "Keranjang Anda kosong.")
        return redirect('cart:view_cart')

    # Payment baru
    payment = Transaction.objects.create(
        buyer=request.user,
        payment_status='paid',  # langsung paid karena simulasi
        amount_paid=cart.total_price
    )

    # Tambahkan produk dari cart ke TransactionProduct
    for item in cart.items.all():
        TransactionProduct.objects.create(
            transaction=payment,
            product=item.product,
            amount=item.quantity,
            price=item.price
        )
    # Kosongkan keranjang
    cart.items.all().delete()

    # Pesan sukses
    messages.success(request, "Checkout berhasil! Terima kasih telah berbelanja.")
    return redirect('main:show_main')
