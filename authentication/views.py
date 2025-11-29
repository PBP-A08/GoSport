import json
from django.shortcuts import render
from django.contrib.auth.models import User, Group 
from django.contrib.auth import logout as auth_logout
from django.contrib.auth import authenticate, login as auth_login
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from main.models import Profile

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

@csrf_exempt
def login(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")

        user = authenticate(request, username=username, password=password)

        if user is None:
            return JsonResponse({"error": "Invalid username or password."}, status=400)

        if not user.is_active:
            return JsonResponse({"error": "Account is inactive."}, status=403)

        auth_login(request, user)

        role = user.profile.role  

        return JsonResponse({
            "status": "success",
            "message": "Login successful",
            "username": username,
            "role": role
        })

@csrf_exempt
def register(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password1 = request.POST.get("password1")
        password2 = request.POST.get("password2")
        role = request.POST.get("role", "buyer")

        if password1 != password2:
            return JsonResponse({
                "status": "error",
                "message": "Passwords do not match."
            }, status=400)

        if User.objects.filter(username=username).exists():
            return JsonResponse({
                "status": "error",
                "message": "Username already exists. Please choose another one."
            }, status=400)

        user = User.objects.create_user(username=username, password=password1)

        group, created = Group.objects.get_or_create(name=role)
        user.groups.add(group)

        profile = Profile.objects.get(user=user)
        profile.role = role
        profile.save()

        return JsonResponse({
            "status": "success",
            "message": "User registered successfully",
            "username": user.username,
            "role": role,
        }, status=200)

    
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