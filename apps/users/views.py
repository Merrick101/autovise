# apps/users/views.py

from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from .forms import UserForm, UserProfileForm


@login_required
def profile_view(request):
    user_form = UserForm(instance=request.user)
    profile_form = UserProfileForm(instance=request.user.profile)

    if request.method == 'POST':
        user_form = UserForm(request.POST, instance=request.user)
        profile_form = UserProfileForm(request.POST, instance=request.user.profile)
        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()
            profile_form.save()
            return redirect('profile')

    context = {
        'user_form': user_form,
        'profile_form': profile_form,
        'first_time_discount': request.user.profile.is_first_time_buyer
    }
    return render(request, 'users/profile.html', context)
