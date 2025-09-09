"""
Views for user profile management, dashboard, account deletion,
and saving products/bundles for later.
Located at /apps/users/views.py
"""

from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout
from django.contrib import messages
from django.urls import reverse
from django.views.decorators.http import require_POST
from django.shortcuts import render, redirect, get_object_or_404
from apps.products.models import Product, Bundle
from .models import UserProfile
from .forms import UserForm


@login_required
def profile_view(request):
    user_form = UserForm(instance=request.user)

    if request.method == 'POST':
        user_form = UserForm(request.POST, instance=request.user)
        if user_form.is_valid():
            user_form.save()
            return redirect('users:profile')

    context = {
        'user_form': user_form,
        'first_time_discount': request.user.profile.is_first_time_buyer
    }
    return render(request, 'users/profile.html', context)


@login_required
def dashboard(request):
    profile, _ = UserProfile.objects.get_or_create(user=request.user)

    saved_products = profile.saved_products.all()
    saved_bundles = profile.saved_bundles.all()
    order_count = request.user.order_set.count()

    context = {
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
    profile, _ = UserProfile.objects.get_or_create(user=request.user)

    if profile.saved_products.filter(id=product.id).exists():
        profile.saved_products.remove(product)
        messages.info(request, "Removed product from saved.")
    else:
        profile.saved_products.add(product)
        messages.success(request, "Saved product for later.")

    next_url = request.POST.get("next") or request.META.get("HTTP_REFERER") \
        or reverse("products:product_list")
    return redirect(next_url)


@require_POST
@login_required
def save_bundle(request, bundle_id):
    bundle = get_object_or_404(Bundle, id=bundle_id)
    profile, _ = UserProfile.objects.get_or_create(user=request.user)

    if profile.saved_bundles.filter(id=bundle.id).exists():
        profile.saved_bundles.remove(bundle)
        messages.info(request, "Removed bundle from saved.")
    else:
        profile.saved_bundles.add(bundle)
        messages.success(request, "Saved bundle for later.")

    next_url = request.POST.get("next") or request.META.get("HTTP_REFERER") \
        or reverse("products:bundle_list")
    return redirect(next_url)
