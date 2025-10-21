import collections
import datetime
import decimal
import uuid
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

from main.forms import ProductForm, RegisterForm, UserEditForm
from main.models import Product, ProductsData, Profile


# ========== MAIN DASHBOARD ==========
@login_required(login_url='/login')
def show_main(request):
    filter_type = request.GET.get("filter", "all")

    if filter_type == "all":
        product_list = Product.objects.all()
    else:
        product_list = Product.objects.filter(user=request.user)

    context = {
        'product_list': product_list,
        'last_login': request.COOKIES.get('last_login', "Never"),
        'role': getattr(request.user.profile, 'role', None)
    }
    return render(request, "main.html", context)


# ========== PRODUCT CRUD ==========
@login_required(login_url='/login')
def create_product(request):
    form = ProductForm(request.POST or None)

    if form.is_valid() and request.method == 'POST':
        product_entry = form.save(commit=False)
        product_entry.seller = request.user
        product_entry.save()
        return redirect('main:show_main')

    return render(request, "create_product.html", {'form': form})


@login_required(login_url='/login')
def show_product(request, id):
    product = get_object_or_404(Product, pk=id)
    return render(request, "product_detail.html", {'product': product})


@login_required(login_url='/login')
def edit_product(request, id):
    product = get_object_or_404(Product, pk=id)
    form = ProductForm(request.POST or None, instance=product)
    if form.is_valid() and request.method == 'POST':
        form.save()
        return redirect('main:show_main')
    return render(request, "edit_product.html", {'form': form})


@login_required(login_url='/login')
def delete_product(request, id):
    product = get_object_or_404(Product, pk=id)
    product.delete()
    return HttpResponseRedirect(reverse('main:show_main'))


# ========== REGISTER / LOGIN / LOGOUT ==========
def register(request):
    if not User.objects.filter(username="admin").exists():
        User.objects.create_superuser(username="admin", password="admin123")

    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Account created successfully!")
            return redirect('main:login')
    else:
        form = RegisterForm()

    return render(request, 'register.html', {'form': form})

def login_user(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)

            try:
                profile = Profile.objects.get(user=user)
            except Profile.DoesNotExist:
                messages.error(request, "Account not found.")
                logout(request)
                return redirect('main:login')

            response = HttpResponseRedirect(reverse("main:show_main"))
            response.set_cookie('last_login', str(datetime.datetime.now()))

            if profile.is_admin:
                return redirect('main:show_main')
            elif profile.role == 'penjual':
                return redirect('main:show_main')
            elif profile.role == 'pembeli':
                return redirect('main:show_main')
            else:
                return response

        else:
            messages.error(request, "Wrong username or password.")
    return render(request, 'login.html')


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


# New implementation
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
                # Include the seller's username!
                "seller_username": product.seller.username if product.seller else "N/A"
            }
        }
        
        return JsonResponse([product_data], safe=False) 
    
    except Product.DoesNotExist:
        return JsonResponse([], safe=False)


# ========== AJAX CREATE ==========
@csrf_exempt
# @require_POST
def add_product_entry_ajax(request):
    product_name = strip_tags(request.POST.get("product_name")) 
    description = strip_tags(request.POST.get("description"))
    category = request.POST.get("category")
    old_price = request.POST.get("old_price")
    special_price = request.POST.get("special_price")
    thumbnail = request.POST.get("thumbnail")
    stock = request.POST.get("stock", 0)

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

# ========== PROFILE DASHBOARD ==========
@login_required(login_url='/login')
def profile_dashboard(request):
    user = request.user
    masked_password = '••••••••'
    
    try:
        user_role = user.profile.role
    except:
        user_role = 'N/A'

    context = {
        'username': user.username,
        'role': user_role,
        'masked_password': masked_password, 
    }
    
    return render(request, "profile_dashboard.html", context)

@login_required(login_url='/login')
def edit_username(request):
    user_form = UserEditForm(request.POST or None, instance=request.user)
    
    if request.method == 'POST':
        old_password = request.POST.get('old_password')
        
        user_authenticated = authenticate(
            request,
            username=request.user.username,
            password=old_password
        )

        if user_authenticated is None:
            messages.error(request, 'The current password you entered is incorrect.')
            
        elif user_form.is_valid():
            user_form.save()
            update_session_auth_hash(request, request.user)
            messages.success(request, 'Your username has been successfully updated!')
            return redirect('main:profile_dashboard')
        
        else:
            messages.error(request, 'There was an error updating your username. Please check the fields below.')

    context = {'user_form': user_form}
    return render(request, "edit_username.html", context)

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
        messages.success(request, "Your account has been successfully deleted. See ya!")
        return redirect('main:register') 
    
    return render(request, "delete_account_confirm.html")