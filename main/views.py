import datetime
import decimal
from django.urls import reverse
from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
from django.contrib.auth.forms import PasswordChangeForm
from django.core import serializers
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.utils.html import strip_tags
from django.contrib.auth.models import User
from django.db import transaction

from main.forms import RegisterForm, UserForm, ProfileForm
from main.models import Product, Profile

# ========== MAIN DASHBOARD ==========
@login_required(login_url='/login')
def show_main(request):
    if not request.user.is_authenticated and not request.session.get('is_admin', False):
        return redirect('main:login')

    filter_type = request.GET.get("filter", "all")

    if request.session.get('is_admin', False):
        product_list = Product.objects.all()
    else:
        if filter_type == "all":
            product_list = Product.objects.all()
        else:
            product_list = Product.objects.filter(user=request.user)

    context = {
        'product_list': product_list,
        'last_login': request.COOKIES.get('last_login', "Never"),
        'role': 'admin' if request.session.get('is_admin', False)
                 else getattr(getattr(request.user, 'profile', None), 'role', None),
        'is_admin': request.session.get('is_admin', False),
    }

    return render(request, "main.html", context)

@login_required(login_url='/login')
def show_product(request, id):
    product = get_object_or_404(Product, pk=id)
    return render(request, "product_detail.html", {'product': product})

# ========== REGISTER / LOGIN / LOGOUT ==========
def register(request):
    storage = messages.get_messages(request)
    storage.used = True

    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()

            Profile.objects.create(user=user, role='buyer')

            messages.success(request, "Account created successfully!")
            return redirect('main:login')
    else:
        form = RegisterForm()
    return render(request, 'register.html', {'form': form})

def login_user(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'
        
        admin_response = _handle_admin_login(request, username, password, is_ajax)
        if admin_response:
            return admin_response
        
        return _handle_regular_user_login(request, username, password, is_ajax)
    
    return render(request, 'login.html')

def _handle_admin_login(request, username, password, is_ajax):
    if username == "admin" and password == "admin123":
        request.session['is_admin'] = True
        request.session['username'] = username
        response = HttpResponseRedirect(reverse("main:show_main"))
        response.set_cookie('last_login', str(datetime.datetime.now()))
        
        if is_ajax:
            return JsonResponse({
                'status': 'success',
                'redirect_url': reverse('main:show_main')
            })
        return response
    return None

def _handle_regular_user_login(request, username, password, is_ajax):
    """Handle regular user login with validation."""
    # Check if user exists
    if not User.objects.filter(username=username).exists():
        return _login_error_response(
            'Account not found. Please register first.',
            is_ajax,
            request
        )
    
    # Authenticate user
    user = authenticate(request, username=username, password=password)
    
    if user:
        return _login_success_response(request, user, is_ajax)
    
    return _login_error_response(
        'Wrong password. Please try again.',
        is_ajax,
        request
    )

def _login_success_response(request, user, is_ajax):
    """Handle successful login response."""
    login(request, user)
    request.session['is_admin'] = False
    
    if is_ajax:
        return JsonResponse({
            'status': 'success',
            'redirect_url': reverse('main:show_main')
        })
    return redirect('main:show_main')

def _login_error_response(message, is_ajax, request):
    """Handle login error response for both AJAX and regular requests."""
    if is_ajax:
        return JsonResponse({
            'status': 'error',
            'message': message
        })
    
    messages.error(request, message)
    return redirect('main:login')

def is_admin(request) -> bool:
    return bool(request.session.get('is_admin'))

def logout_user(request):
    logout(request)
    response = HttpResponseRedirect(reverse('main:login'))
    response.delete_cookie('last_login')
    return response

# ========== JSON / XML ENDPOINTS ==========
def show_xml(request):
    products = Product.objects.all()
    xml_data = serializers.serialize("xml", products)
    return HttpResponse(xml_data, content_type="application/xml")


def show_json(request):
    products = Product.objects.all()
    data = serializers.serialize("json", products)
    return HttpResponse(data, content_type="application/json")


def show_xml_by_id(request, product_id):
    product = Product.objects.filter(pk=product_id)
    xml_data = serializers.serialize("xml", product)
    return HttpResponse(xml_data, content_type="application/xml")


def show_json_by_id(request, product_id):
    try:

        product = Product.objects.select_related('seller').get(pk=product_id)

        product_data = {
            "pk": str(product.id),
            "model": "main.product",
            "fields": {
                "product_name": product.product_name,
                "description": product.description,
                "category": product.category,
                "old_price": float(product.old_price),
                "special_price": float(product.special_price),
                "discount_percent": product.discount_percent,
                "thumbnail": product.thumbnail,
                "stock": product.stock,
                "created_at": product.created_at.isoformat(),
                "seller_username": product.seller.username if product.seller else "N/A"
            }
        }
        
        return JsonResponse([product_data], safe=False) 
    
    except Product.DoesNotExist:
        return JsonResponse([], safe=False)

# ========== PROFILE DASHBOARD ==========
@login_required(login_url='/login')
def profile_dashboard(request):
    user = request.user
    masked_password = '••••••••'

    try:
        user_role = user.profile.role
        store_name = user.profile.store_name or '-'
        address = user.profile.address or '-'
    except Profile.DoesNotExist:
        user_role = 'N/A'
        store_name = '-'
        address = '-'

    context = {
        'username': user.username,
        'role': user_role,
        'masked_password': masked_password,
        'store_name': store_name,
        'address': address,
    }

    return render(request, "profile_dashboard.html", context)

@login_required
def edit_profile(request):
    user = request.user
    profile = Profile.objects.get(user=user)

    if request.method == 'POST':
        user_form = UserForm(request.POST, instance=user)
        profile_form = ProfileForm(request.POST, instance=profile)

        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()
            profile_form.save()
            messages.success(request, 'Profile updated successfully!')
            return redirect('main:profile_dashboard')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        user_form = UserForm(instance=user)
        profile_form = ProfileForm(instance=profile)

    return render(request, 'edit_profile.html', {
        'user_form': user_form,
        'profile_form': profile_form,
        'role': profile.role,
    })

@login_required(login_url='/login')
def edit_password(request):
    if request.method == 'POST':
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)
            messages.success(request, 'Your password was successfully updated!')
            return redirect('main:profile_dashboard')
        else:
            messages.error(request, 'Please correct the error below.')
    else:
        form = PasswordChangeForm(request.user)
        
    context = {'form': form}
    return render(request, 'edit_password.html', context)

@login_required(login_url='/login')
def delete_account(request):
    if request.method == 'POST':
        user = request.user
        logout(request)
        user.delete() 
        messages.success(request, "Your account has been successfully deleted. See ya!") #what the heck
        return redirect('main:register') 
    
    return render(request, "delete_account_confirm.html")

# ========== AJAX CRUD FUNCTIONALITY ==========
@csrf_exempt
@require_POST
def add_product_entry_ajax(request):
    product_name = strip_tags(request.POST.get("product_name"))
    description = strip_tags(request.POST.get("description"))
    category = request.POST.get("category", "")
    thumbnail = request.POST.get("thumbnail", "")

    try:
        old_price_str = request.POST.get("old_price")
        old_price = decimal.Decimal(old_price_str) if old_price_str else decimal.Decimal('0.00')
    except decimal.InvalidOperation:
        return HttpResponse(b"Invalid Old Price", status=400)
    
    try:
        special_price_str = request.POST.get("special_price")
        special_price = decimal.Decimal(special_price_str) if special_price_str else decimal.Decimal('0.00')
    except decimal.InvalidOperation:
        return HttpResponse(b"Invalid Special Price", status=400)
        
    try:
        stock = int(request.POST.get("stock") or 0)
    except ValueError:
        return HttpResponse(b"Invalid Stock Value", status=400)


    if not product_name:
        return HttpResponse(b"Product name is required", status=400)
        
    # --- Database insertion is inside a transaction ---
    try:
        with transaction.atomic():
            new_product = Product(
                product_name=product_name,
                description=description,
                category=category,
                old_price=old_price,
                special_price=special_price,
                thumbnail=thumbnail,
                stock=stock,
                seller=request.user  
            )
            new_product.save()
            return HttpResponse(b"CREATED", status=201)
            
    except Exception as e:
        return HttpResponse(b"Internal Server Error during save", status=500)

def edit_product_ajax(request, id):
    try:
        prod = Product.objects.get(pk=id)
    except Product.DoesNotExist:
        return JsonResponse({"status": "error", "message": "Product not found."}, status=404)

    if not request.session.get('is_admin', False) and prod.seller != request.user:
        return JsonResponse(
            {"status": "error", "message": "You are not authorized to edit this product."},
            status=403
        )

    prod.product_name = request.POST.get("product_name") 
    prod.description = request.POST.get("description")
    prod.category = request.POST.get("category")
    prod.thumbnail = request.POST.get("thumbnail")

    try:
        prod.old_price = float(request.POST.get("old_price"))
        prod.special_price = float(request.POST.get("special_price"))
        prod.discount_percent = int(request.POST.get("discount_percent"))
        prod.stock = int(request.POST.get("stock"))
    except (ValueError, TypeError):
        return JsonResponse({
            "status": "error",
            "message": "Invalid numeric input detected for price, discount, or stock."
        }, status=400)

    try:
        prod.save()
        return JsonResponse({"status": "success", "message": "Product updated successfully"}, status=200)
    except Exception as e:
        return JsonResponse({"status": "error", "message": f"Failed to save product: {e}"}, status=500)
    
@login_required
@csrf_exempt
@require_POST
def delete_product_ajax(request, id):
    product = get_object_or_404(Product, pk=id)

    if request.session.get('is_admin', False):
        product.delete()
        return JsonResponse({"status": "success", "message": "Product deleted by admin."}, status=200)

    if product.seller != request.user:
        return JsonResponse({"status": "error", "message": "You are not authorized to delete this product."}, status=403)

    product.delete()
    return JsonResponse({"status": "success", "message": "Product deleted successfully."}, status=200)