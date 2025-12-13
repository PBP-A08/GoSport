import json
import os
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from django.contrib.auth import authenticate, login as auth_login, logout
from django.contrib.auth.models import User
from main.models import Profile

@csrf_exempt
def login(request):
    if request.method != 'POST':
        return JsonResponse({
            'status': 'error',
            'message': 'Only POST method allowed'
        }, status=405)
    
    try:
        data = json.loads(request.body)
        username = data.get('username')
        password = data.get('password')
    except (json.JSONDecodeError, Exception):
        username = request.POST.get('username')
        password = request.POST.get('password')
    
    if not username or not password:
        return JsonResponse({
            'status': 'error',
            'message': 'Username and password are required'
        }, status=400)
    
    ADMIN_PASSWORD = os.getenv('ADMIN_PASSWORD', 'akuadalahadmin')
    if username == "admin" and password == ADMIN_PASSWORD:
        try:
            user = User.objects.get(username='admin')
            if not user.is_superuser or not user.is_staff:
                user.is_superuser = True
                user.is_staff = True
                user.set_password(password)
                user.save()
            Profile.objects.filter(user=user).delete()
        except User.DoesNotExist:
            user = User.objects.create_superuser(
                username='admin',
                password=password,
                email='admin@gosport.com'
            )
            Profile.objects.filter(user=user).delete()
        
        user = authenticate(request, username=username, password=password)
        if user and user.is_superuser:
            auth_login(request, user)
            return JsonResponse({
                'status': 'success',
                'message': 'Login successful',
                'username': user.username,
                'role': 'admin'
            })
    
    if not User.objects.filter(username=username).exists():
        return JsonResponse({
            'status': 'error',
            'message': 'Account not found. Please register first.'
        }, status=401)
    
    user = authenticate(request, username=username, password=password)
    
    if user is not None:
        auth_login(request, user)
        
        if user.is_superuser or user.is_staff:
            role = "admin"
            Profile.objects.filter(user=user).delete()
        else:
            try:
                role = user.profile.role
            except Profile.DoesNotExist:
                role = "buyer"
        
        return JsonResponse({
            "status": "success",
            "message": "Login successful",
            "username": user.username,
            "role": role
        })
    
    return JsonResponse({
        'status': 'error',
        'message': 'Invalid username or password.'
    }, status=401)

@csrf_exempt
def register(request):
    if request.method != 'POST':
        return JsonResponse({
            'status': 'error',
            'message': 'Only POST method allowed'
        }, status=405)
    
    try:
        data = json.loads(request.body)
        username = data.get('username')
        password1 = data.get('password1')
        password2 = data.get('password2')
        role = data.get('role', 'buyer')
    except (json.JSONDecodeError, Exception):
        username = request.POST.get('username')
        password1 = request.POST.get('password1')
        password2 = request.POST.get('password2')
        role = request.POST.get('role', 'buyer')
    
    if not username or not password1 or not password2:
        return JsonResponse({
            'status': 'error',
            'message': 'All fields are required'
        }, status=400)
    
    if password1 != password2:
        return JsonResponse({
            'status': 'error',
            'message': 'Passwords do not match'
        }, status=400)
    
    if User.objects.filter(username=username).exists():
        return JsonResponse({
            'status': 'error',
            'message': 'Username already exists'
        }, status=400)
    
    try:
        user = User.objects.create_user(
            username=username,
            password=password1
        )
        
        if not user.is_superuser and not user.is_staff:
            Profile.objects.create(
                user=user,
                role=role if role in ['buyer', 'seller'] else 'buyer'
            )
        
        return JsonResponse({
            'status': 'success',
            'message': 'User registered successfully'
        })
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=500)

@csrf_exempt
def logout_view(request):
    logout(request)
    return JsonResponse({
        'status': 'success',
        'message': 'Logged out successfully'
    })