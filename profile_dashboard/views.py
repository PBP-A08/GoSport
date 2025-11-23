import json
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.contrib.auth import update_session_auth_hash, logout
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib import messages
from django.shortcuts import render, redirect
from main.forms import UserForm, ProfileForm
from main.models import Profile
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.models import User

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
        if request.headers.get('Content-Type') == 'application/json':
            try:
                data = json.loads(request.body)
                
                # Update username
                if 'username' in data:
                    user.username = data['username']
                    user.save()
                
                # Update profile based on role
                if profile.role == 'buyer' and 'address' in data:
                    profile.address = data['address']
                elif profile.role == 'seller' and 'store_name' in data:
                    profile.store_name = data['store_name']
                
                profile.save()
                
                return JsonResponse({
                    'success': True,
                    'message': 'Profile updated successfully!'
                })
            
            except Exception as e:
                return JsonResponse({
                    'success': False,
                    'error': str(e)
                }, status=400)
        
        else:
            user_form = UserForm(request.POST, instance=user)
            profile_form = ProfileForm(request.POST, instance=profile)

            if user_form.is_valid() and profile_form.is_valid():
                user_form.save()
                profile_form.save()
                messages.success(request, 'Profile updated successfully!')
                return redirect('profile_dashboard:profile_dashboard')
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
            return redirect('profile_dashboard:profile_dashboard')
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

@csrf_exempt
def profile_json(request):
    if not request.user.is_authenticated:
        return JsonResponse({
            "error": "Not authenticated"
        }, status=401)
    
    user = request.user
    try:
        profile = user.profile
        return JsonResponse({
            "username": user.username,
            "role": profile.role,
            "address": profile.address or "-",
            "store_name": profile.store_name or "-",
        })
    except Profile.DoesNotExist:
        return JsonResponse({
            "error": "Profile not found"
        }, status=404)
    
@csrf_exempt
def edit_profile_json(request):
    if not request.user.is_authenticated:
        return JsonResponse({
            'success': False,
            'error': 'Not authenticated'
        }, status=401)
    
    if request.method != 'POST':
        return JsonResponse({
            'success': False,
            'error': 'Method not allowed'
        }, status=405)
    
    user = request.user
    
    try:
        profile = user.profile
        data = json.loads(request.body)
  
        if 'username' in data:
            if User.objects.filter(username=data['username']).exclude(id=user.id).exists():
                return JsonResponse({
                    'success': False,
                    'error': 'Username already taken'
                }, status=400)
            user.username = data['username']
            user.save()
        
        if profile.role == 'buyer' and 'address' in data:
            profile.address = data['address']
        elif profile.role == 'seller' and 'store_name' in data:
            profile.store_name = data['store_name']
        
        profile.save()
        
        return JsonResponse({
            'success': True,
            'message': 'Profile updated successfully!'
        })
        
    except Profile.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Profile not found'
        }, status=404)
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': 'Invalid JSON'
        }, status=400)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=400)

@csrf_exempt
def change_password(request):
    if not request.user.is_authenticated:
        return JsonResponse({
            "success": False,
            "message": "Not authenticated"
        }, status=401)
    
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            old_password = data.get('old_password')
            new_password1 = data.get('new_password1')
            new_password2 = data.get('new_password2')
            
            # Check old password
            if not request.user.check_password(old_password):
                return JsonResponse({
                    "success": False,
                    "message": "Current password is incorrect"
                }, status=400)
            
            # Check if new passwords match
            if new_password1 != new_password2:
                return JsonResponse({
                    "success": False,
                    "message": "New passwords do not match"
                }, status=400)
            
            # Check password length
            if len(new_password1) < 8:
                return JsonResponse({
                    "success": False,
                    "message": "Password must be at least 8 characters"
                }, status=400)
            
            # Change password
            request.user.set_password(new_password1)
            request.user.save()
            
            # Update session to keep user logged in
            update_session_auth_hash(request, request.user)
            
            return JsonResponse({
                "success": True,
                "message": "Password changed successfully"
            })
            
        except Exception as e:
            return JsonResponse({
                "success": False,
                "message": str(e)
            }, status=400)
    
    return JsonResponse({
        "success": False,
        "message": "Invalid request method"
    }, status=400)

@csrf_exempt
def delete_account_json(request):
    if not request.user.is_authenticated:
        return JsonResponse({
            "success": False,
            "message": "Not authenticated"
        }, status=401)
    
    if request.method == 'POST':
        try:
            user = request.user
            logout(request)
            user.delete()
            
            return JsonResponse({
                "success": True,
                "message": "Account deleted successfully"
            })
        except Exception as e:
            return JsonResponse({
                "success": False,
                "message": str(e)
            }, status=400)
    
    return JsonResponse({
        "success": False,
        "message": "Invalid request method"
    }, status=400)