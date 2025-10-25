from django.http import JsonResponse
from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden
from .models import Cart, CartItem
from main.models import Product
from payment.models import Transaction, TransactionProduct

def is_buyer(user):
    try:
        return hasattr(user, 'profile') and user.profile.role == 'buyer'
    except Exception:
        return False


@login_required
def view_cart(request):
    if not is_buyer(request.user):
        return HttpResponseForbidden("Only buyer that allow to access cart.")

    cart, _ = Cart.objects.get_or_create(user=request.user)
    context = {
        'cart': cart,
        'items': cart.items.all(),
        'total_price': cart.total_price,
    }
    return render(request, 'view_cart.html', context)


@login_required
def add_to_cart(request, product_id):
    if not is_buyer(request.user):
        return JsonResponse({'success': False, 'error': 'Only buyer that allow to add to cart.'}, status=403)

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

    return JsonResponse({
        'success': True,
        'message': f"{product.product_name} successfully added to cart.",
        'total_price': float(cart.total_price)
    })

@login_required
def update_cart_item(request, item_id):
    if not is_buyer(request.user):
        return JsonResponse({'success': False, 'error': 'Only buyer that allow to change the total item.'}, status=403)

    item = get_object_or_404(CartItem, id=item_id, cart__user=request.user)

    if request.method == "POST":
        try:
            qty = int(request.POST.get('quantity', 1))
            if qty < 1:
                return JsonResponse({'success': False, 'error': 'Quantity must be at least 1.'})
            
            item.quantity = qty
            item.save()
            cart = item.cart

            # Hitung subtotal item
            subtotal = float(item.quantity * item.product.special_price)

            return JsonResponse({
                'success': True,
                'message': f"Quantity of {item.product.product_name} has been updated.",
                'total_price': float(cart.total_price),
                'subtotal': subtotal,
                'item_id': item.id  # optional, untuk update DOM spesifik
            })
        except ValueError:
            return JsonResponse({'success': False, 'error': 'Input quantity is not valid.'})

    return JsonResponse({'success': False, 'error': 'Method not allowed.'}, status=405)


@login_required
def remove_from_cart(request, item_id):
    if not is_buyer(request.user):
        return JsonResponse({'success': False, 'error': 'Only buyer that allow to remove item.'}, status=403)

    item = get_object_or_404(CartItem, id=item_id, cart__user=request.user)
    product_name = item.product.product_name
    item.delete()

    cart = item.cart
    return JsonResponse({
        'success': True,
        'message': f"{product_name} successfully removed from cart.",
        'total_price': float(cart.total_price)
    })

@login_required
def checkout_cart(request):
    if request.method != 'POST':
        return redirect('cart:checkout_review')

    cart = getattr(request.user, 'cart', None)
    if not cart or not cart.items.exists():
        messages.warning(request, "Your cart is empty.")
        return redirect('cart:view_cart')

    # Payment baru
    payment = Transaction.objects.create(
        buyer=request.user,
        payment_status='paid',
        amount_paid=cart.total_price
    )

    for item in cart.items.all():
        TransactionProduct.objects.create(
            transaction=payment,
            product=item.product,
            amount=item.quantity,
            price=item.price
        )

    cart.items.all().delete()
    messages.success(request, "Order has been successfully created!")
    return redirect('main:show_main')

@login_required
def checkout_review(request):
    if not is_buyer(request.user):
        return HttpResponseForbidden("Only buyer that allow to checkout.")

    cart = getattr(request.user, 'cart', None)
    if not cart or not cart.items.exists():
        messages.warning(request, "Your cart is empty.")
        return redirect('cart:view_cart')

    items_data = []
    total = 0
    for item in cart.items.all():
        subtotal = item.quantity * item.price
        total += subtotal
        items_data.append({
            'product': item.product,
            'quantity': item.quantity,
            'price': item.price,
            'subtotal': subtotal
        })

    context = {
        'user': request.user,
        'address': request.user.profile.address,
        'items': items_data,
        'total': total
    }
    return render(request, 'checkout_review.html', context)
