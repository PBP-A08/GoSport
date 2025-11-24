from django.contrib.auth import authenticate, login as auth_login
from django.contrib.auth import logout as auth_logout
from django.http import JsonResponse
from django.contrib.auth.models import User
import json
from django.views.decorators.csrf import csrf_exempt

@csrf_exempt
def login(request):
    username = request.POST.get('username')
    password = request.POST.get('password')
    
    if not username or not password:
        return JsonResponse({
            "status": False,
            "message": "Username and password are required."
        }, status=400)
    
    user = authenticate(username=username, password=password)
    
    if user is not None and user.is_active:
        auth_login(request, user)

        if user.is_superuser:
            role = "admin"
        else:
            role = user.profile.role
        
        return JsonResponse({
            "username": user.username,
            "role": role,
            "status": True,
            "message": "Login successful!"
        }, status=200)

    return JsonResponse({
        "status": False,
        "message": "Login failed, please check your username or password."
    }, status=401)

    
@csrf_exempt
def register(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        username = data['username']
        password1 = data['password1']
        password2 = data['password2']

        # Check if the passwords match
        if password1 != password2:
            return JsonResponse({
                "status": False,
                "message": "Passwords do not match."
            }, status=400)
        
        # Check if the username is already taken
        if User.objects.filter(username=username).exists():
            return JsonResponse({
                "status": False,
                "message": "Username already exists."
            }, status=400)
        
        # Create the new user
        user = User.objects.create_user(username=username, password=password1)
        user.save()
        
        return JsonResponse({
            "username": user.username,
            "status": 'success',
            "message": "User created successfully!"
        }, status=200)
    
    else:
        return JsonResponse({
            "status": False,
            "message": "Invalid request method."
        }, status=400)
    
@csrf_exempt
def logout(request):
    username = request.user.username
    try:
        auth_logout(request)
        return JsonResponse({
            "username": username,
            "status": True,
            "message": "Logged out successfully!"
        }, status=200)
    except:
        return JsonResponse({
            "status": False,
            "message": "Logout failed."
        }, status=401)