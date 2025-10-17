import datetime
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

from main.forms import ProductForm, RegisterForm
from main.models import Product, Profile


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
            messages.success(request, "Akun berhasil dibuat!")
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
                messages.error(request, "Akun tidak ditemukan.")
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


def show_json_by_id(request, product_id):
    product = Product.objects.filter(pk=product_id)
    json_data = serializers.serialize("json", product)
    return HttpResponse(json_data, content_type="application/json")


# ========== AJAX CREATE ==========
@csrf_exempt
@require_POST
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