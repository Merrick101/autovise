# apps/users/views.py

from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout
from django.contrib import messages
from django.views.decorators.http import require_POST
from django.shortcuts import render, redirect, get_object_or_404
from apps.products.models import Product, Bundle
from .models import UserProfile
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


@login_required
def dashboard(request):
    profile = request.user.profile
    saved_products = profile.saved_products.all()
    saved_bundles = profile.saved_bundles.all()
    order_count = request.user.orders.count() if hasattr(request.user, "orders") else 0

    context = {
        'user': request.user,
        'profile': profile,
        'saved_products': saved_products,
        'saved_bundles': saved_bundles,
        'order_count': order_count,
    }
    return render(request, 'users/dashboard.html', context)


@require_POST
@login_required
def delete_account(request):
    user = request.user
    logout(request)  # Log the user out first
    user.delete()
    messages.success(request, "Your account has been deleted.")
    return redirect('account_login')


@login_required
def save_product(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    profile, created = UserProfile.objects.get_or_create(user=request.user)

    if product in profile.saved_products.all():
        profile.saved_products.remove(product)
    else:
        profile.saved_products.add(product)

    # Redirect back to the same page or product detail
    return redirect(request.META.get('HTTP_REFERER', 'products:product_list'))


@login_required
def save_bundle(request, bundle_id):
    bundle = get_object_or_404(Bundle, id=bundle_id)
    profile, created = UserProfile.objects.get_or_create(user=request.user)

    if bundle in profile.saved_bundles.all():
        profile.saved_bundles.remove(bundle)
    else:
        profile.saved_bundles.add(bundle)

    return redirect(request.META.get('HTTP_REFERER', 'products:bundle_list'))
