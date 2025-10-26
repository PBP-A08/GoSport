import datetime
import decimal
import json
import os
from django.urls import reverse
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
from django.core import serializers
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.utils.html import strip_tags
from django.contrib.auth.models import User
from django.db import transaction
from main.forms import RegisterForm
from main.models import Product, ProductsData
from django.conf import settings

# ========== MAIN DASHBOARD ==========
@login_required(login_url='/login')
def show_main(request):
    if not request.user.is_authenticated:
        return redirect('main:login')

    filter_type = request.GET.get("filter", "all")
    selected_category = request.GET.get("category", None)

    if request.user.is_superuser:
        product_list = Product.objects.all()
    else:
        if filter_type == "all":
            product_list = Product.objects.all()
        else:
            product_list = Product.objects.filter(seller=request.user)

    if selected_category and selected_category.lower() != "all":
        product_list = product_list.filter(category__iexact=selected_category.strip())

    if 'product_data' in settings.DATABASES:
        ecommerce_products = ProductsData.objects.using('product_data').all()
    else:
        ecommerce_products = []
    
    if request.user.is_superuser:
        role = 'admin'
    else:
        profile = getattr(request.user, 'profile', None)
        if profile and hasattr(profile, 'role') and profile.role:
            role = profile.role
        else:
            role = 'buyer'

    internal_categories = list(Product.objects.values_list('category', flat=True).distinct())
    if 'product_data' in settings.DATABASES:
        external_products = ProductsData.objects.using('product_data').all()
    else:
        external_products = []
    external_categories = [infer_category(getattr(p, 'product_name', '')) for p in external_products]
    combined_categories = sorted(set(filter(None, internal_categories + external_categories)))

    context = {
        'product_list': product_list,
        'ecommerce_products': ecommerce_products,
        'last_login': request.COOKIES.get('last_login', "Never"),
        'role': role,
        'is_admin': request.user.is_superuser,
        'is_buyer': role == 'pembeli',
        'categories': combined_categories,
        'selected_category': selected_category,
    }

    return render(request, "main.html", context)

@login_required(login_url='/login')
def show_product(request, id):
    product = get_object_or_404(Product, pk=id)
    
    is_owner = product.seller == request.user
    
    profile = getattr(request.user, 'profile', None)
    user_role = getattr(profile, 'role', None) if profile else None
    
    is_admin_or_superuser = request.user.is_superuser or user_role == 'admin'
    
    can_modify = is_owner or is_admin_or_superuser
    
    context = {
        'product': product,
        'can_modify': can_modify, 
        'product_id': str(product.id),
    }
    
    return render(request, "product_detail.html", context)

# ========== REGISTER / LOGIN / LOGOUT ==========
def register(request):
    storage = messages.get_messages(request)
    storage.used = True
    is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'

    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            if is_ajax:
                return JsonResponse({
                    'status': 'success',
                    'redirect_url': reverse('main:login')
                })
            messages.success(request, "Account created successfully!")
            return redirect('main:login')
        else:
            errors = form.errors.as_json()
            if is_ajax:
                return JsonResponse({
                    'status': 'error',
                    'message': 'Please fix the errors in the form',
                    'errors': errors
                })
            messages.error(request, "Please correct the errors below.")
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
    ADMIN_PASSWORD = os.getenv('ADMIN_PASSWORD', 'akuadalahadmin')
    
    if username == "admin" and password == ADMIN_PASSWORD:
        try:
            # Cek apakah user admin sudah ada
            user = User.objects.get(username='admin')
            
            # PASTIKAN user ini adalah superuser
            if not user.is_superuser or not user.is_staff:
                user.is_superuser = True
                user.is_staff = True
                user.set_password(password)  # Update password juga
                user.save()
                print(f"Updated existing admin user to superuser")
            
        except User.DoesNotExist:
            # Buat user baru jika belum ada
            user = User.objects.create_superuser(
                username='admin',
                password=password,
                email='admin@gosport.com'
            )
            print(f"Created new admin superuser")
        
        # Authenticate user
        user = authenticate(request, username=username, password=password)
        
        if user and user.is_superuser:
            login(request, user)
            response = HttpResponseRedirect(reverse("main:show_main"))
            response.set_cookie('last_login', str(datetime.datetime.now()))
            
            if is_ajax:
                return JsonResponse({'status': 'success', 'redirect_url': reverse('main:show_main')})
            return response
    
    return None

def _handle_regular_user_login(request, username, password, is_ajax):
    if not User.objects.filter(username=username).exists():
        return _login_error_response(
            'Account not found. Please register first.',
            is_ajax,
            request
        )
    
    user = authenticate(request, username=username, password=password)
    
    if user:
        return _login_success_response(request, user, is_ajax)
    
    return _login_error_response(
        'Wrong password. Please try again.',
        is_ajax,
        request
    )

def _login_success_response(request, user, is_ajax):
    login(request, user)
    request.session['is_admin'] = False
    
    if is_ajax:
        return JsonResponse({
            'status': 'success',
            'redirect_url': reverse('main:show_main')
        })
    return redirect('main:show_main')

def _login_error_response(message, is_ajax, request):
    if is_ajax:
        return JsonResponse({
            'status': 'error',
            'message': message
        })
    
    messages.error(request, message)
    return redirect('main:login')

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
    sync_products_data()
    products = Product.objects.all()
    product_json = serializers.serialize('json', products)
    all_products = json.loads(product_json)
    return JsonResponse(all_products, safe=False)

def show_xml_by_id(request, product_id):
    product = Product.objects.filter(pk=product_id)
    xml_data = serializers.serialize("xml", product)
    return HttpResponse(xml_data, content_type="application/xml")

def show_json_by_id(request, product_id):
    try:
        product = Product.objects.select_related('seller__profile').get(pk=product_id)
        
        seller_display = "N/A"
        if product.seller:
            profile = getattr(product.seller, 'profile', None)
            if profile and profile.store_name:
                seller_display = profile.store_name
            else:
                seller_display = product.seller.username
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
                "seller": product.seller.id if product.seller else None,
                "seller_username": product.seller.username if product.seller else "N/A",
                "seller_display": seller_display
            }
        }
        
        return JsonResponse([product_data], safe=False) 
    
    except Product.DoesNotExist:
        return JsonResponse([], safe=False)

# ========== AJAX CRUD FUNCTIONALITY ==========
@csrf_exempt
@require_POST
def add_product_entry_ajax(request):
    product_name = strip_tags(request.POST.get("product_name"))
    description = strip_tags(request.POST.get("description"))
    category = request.POST.get("category", "")
    thumbnail = request.POST.get("thumbnail", "")

    try:
        old_price = decimal.Decimal(request.POST.get("old_price") or '0.00')
        special_price = decimal.Decimal(request.POST.get("special_price") or '0.00')
        stock = int(request.POST.get("stock") or 0)
    except (decimal.InvalidOperation, ValueError):
        return HttpResponse(b"Invalid input", status=400)

    if not product_name:
        return HttpResponse(b"Product name is required", status=400)
        
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
        return HttpResponse(b"Internal Server Error", status=500)

@csrf_exempt
@require_POST
@login_required
def edit_product_ajax(request, id):
    try:
        prod = Product.objects.get(pk=id)
    except Product.DoesNotExist:
        return JsonResponse({"status": "error", "message": "Product not found."}, status=404)

    is_owner = prod.seller and prod.seller.id == request.user.id
    is_admin = request.user.is_superuser
    
    if not (is_owner or is_admin):
        return JsonResponse({
            "status": "error", 
            "message": "You are not authorized to edit this product."
        }, status=403)

    prod.product_name = strip_tags(request.POST.get("product_name", prod.product_name))
    prod.description = strip_tags(request.POST.get("description", prod.description))
    prod.category = request.POST.get("category", prod.category)
    prod.thumbnail = request.POST.get("thumbnail", prod.thumbnail)

    try:
        prod.old_price = decimal.Decimal(request.POST.get("old_price", prod.old_price))
        prod.special_price = decimal.Decimal(request.POST.get("special_price", prod.special_price))
        prod.stock = int(request.POST.get("stock", prod.stock))
  
        discount_str = request.POST.get("discount_percent", "0")
        prod.discount_percent = int(discount_str) if discount_str else 0
        
    except (ValueError, TypeError, decimal.InvalidOperation):
        return JsonResponse({
            "status": "error",
            "message": "Invalid numeric input."
        }, status=400)

    try:
        prod.save()
        return JsonResponse({"status": "success", "message": "Product updated successfully"}, status=200)
    except Exception as e:
        return JsonResponse({"status": "error", "message": f"Failed to save: {e}"}, status=500)
    
@csrf_exempt
@require_POST
@login_required
def delete_product_ajax(request, id):
    try:
        product = get_object_or_404(Product, pk=id)

        is_owner = product.seller and product.seller.id == request.user.id
        is_admin = request.user.is_superuser
        
        if not (is_owner or is_admin):
            return JsonResponse({
                "status": "error", 
                "message": "You are not authorized to delete this product."
            }, status=403)

        product.delete()
        return JsonResponse({"status": "success", "message": "Product deleted successfully"}, status=200)

    except Exception as e:
        return JsonResponse({
            "status": "error", 
            "message": "An error occurred during deletion."
        }, status=500)

# ========== HELPER FUNCTIONS ==========
def sync_products_data():
    if 'product_data' in settings.DATABASES:
        external_products = ProductsData.objects.using('product_data').all()
    else:
        external_products = []

    for ext in external_products:
        if not Product.objects.filter(product_name=ext.product_name).exists():
            Product.objects.create(
                seller=None,
                product_name=ext.product_name or "Unnamed Product",
                old_price=ext.old_price or 0,
                special_price=ext.special_price or 0,
                discount_percent=int(ext.discount_field or 0),
                category=infer_category(ext.product_name),
                description="No description for this product",
                thumbnail="",
                stock=10
            )
            
def infer_category(name: str):
            name = (name or "").lower()
            if any(x in name for x in ["badminton", "racket", "racquet"]):
                return "Badminton"
            elif "volley" in name:
                return "Volleyball"
            elif any(x in name for x in ["cricket", "bat", "ball", "wicket"]):
                return "Cricket"
            elif "squash" in name:
                return "Squash"
            else:
                return "Accessory"