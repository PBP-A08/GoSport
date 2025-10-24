from django.contrib.auth.decorators import login_required
from django.contrib.auth import update_session_auth_hash, logout
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib import messages
from django.shortcuts import render, redirect
from main.forms import UserForm, ProfileForm
from main.models import Profile

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
        messages.success(request, "Your account has been successfully deleted. See ya!") #what the heck
        return redirect('main:register') 
    
    return render(request, "delete_account_confirm.html")