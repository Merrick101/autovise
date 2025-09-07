"""
Cart views for adding, updating, and removing items.
Handles both authenticated users (DB cart) and guest users (session cart).
Located at apps/orders/views/cart_views.py
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.http import require_POST
from django.contrib import messages
from django.http import HttpResponseRedirect

from apps.products.models import Product, Bundle
from apps.orders.models import CartItem
from apps.orders.utils.cart import (
    add_to_cart, get_active_cart, save_cart, calculate_cart_summary
)


def add_to_cart_view(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    if request.method == 'POST':
        quantity = int(request.POST.get('quantity', 1))
        add_to_cart(request, product_id, quantity)
        messages.success(request, f"Added {product.name} to your cart.")
    return redirect(request.META.get('HTTP_REFERER', 'products:product_list'))


@require_POST
def add_bundle_to_cart_view(request, bundle_id):
    bundle = get_object_or_404(Bundle, id=bundle_id)
    cart = request.session.get('cart', {})

    try:
        quantity = int(request.POST.get('quantity', 1))
    except (TypeError, ValueError):
        quantity = 1
    if quantity < 1:
        quantity = 1

    item_key = f"bundle_{bundle.id}"

    if item_key in cart:
        cart[item_key]['quantity'] += quantity
    else:
        cart[item_key] = {
            'type': 'bundle',
            'name': bundle.name,
            'price': str(bundle.price),
            'quantity': quantity,
        }

    save_cart(request, cart)

    messages.success(request, f"Added {bundle.name} to your cart.")
    return HttpResponseRedirect(request.META.get('HTTP_REFERER', '/'))


def cart_view(request):
    cart_data, cart_type = get_active_cart(request)
    context = calculate_cart_summary(request, cart_data, cart_type)
    return render(request, 'orders/cart.html', context)


@require_POST
def update_quantity(request, item_key):
    """
    Update quantity for a cart line (guest session or DB cart).
    Products for authed users live in the DB cart;
    bundles always live in session.
    """
    try:
        quantity = int(request.POST.get('quantity', 1))
    except (TypeError, ValueError):
        quantity = 1

    if quantity < 1:
        messages.error(request, "Quantity must be at least 1.")
        return redirect('orders:cart')

    # If this is a session bundle key, always update the session cart
    if isinstance(item_key, str) and item_key.startswith("bundle_"):
        cart = request.session.get('cart', {}) or {}
        if item_key in cart:
            cart[item_key]['quantity'] = quantity
            save_cart(request, cart)
            messages.success(request, "Quantity updated.")
        else:
            messages.warning(request, "Could not find that item in your cart.")
        return redirect('orders:cart')

    # Logged-in users: update DB cart product line
    if request.user.is_authenticated:
        cart_item = None
        if item_key.isdigit():
            cart_item = CartItem.objects.filter(
                cart__user=request.user, product_id=int(item_key)
            ).first()
        else:
            cart_item = CartItem.objects.filter(
                cart__user=request.user, product__product_code=item_key
            ).first()

        if cart_item:
            cart_item.quantity = quantity
            cart_item.save(update_fields=["quantity"])
            messages.success(request, "Quantity updated.")
        else:
            messages.warning(request, "Could not find that item in your cart.")
        return redirect('orders:cart')

    # Guests: update session cart product line
    cart = request.session.get('cart', {}) or {}

    # If the template passed a numeric id,
    # map it to the session cart key (product_code)
    if item_key.isdigit():
        pid = int(item_key)
        for k, v in cart.items():
            if k.startswith("bundle_"):
                continue
            if str(v.get("product_id")) == str(pid):
                item_key = k
                break

    if item_key in cart:
        cart[item_key]['quantity'] = quantity
        save_cart(request, cart)
        messages.success(request, "Quantity updated.")
    else:
        messages.warning(request, "Could not find that item in your cart.")
    return redirect('orders:cart')


@require_POST
def remove_item(request, item_key):
    """
    Remove a cart line.
    Products for authed users live in the DB cart;
    bundles always live in session.
    """
    # Session bundle? Always remove from session.
    if isinstance(item_key, str) and item_key.startswith("bundle_"):
        cart = request.session.get('cart', {}) or {}
        if cart.pop(item_key, None) is not None:
            save_cart(request, cart)
            messages.success(request, "Item removed from cart.")
        else:
            messages.warning(request, "Could not find that item in your cart.")
        return redirect('orders:cart')

    # Logged-in users: remove DB cart product line
    if request.user.is_authenticated:
        deleted = 0
        if item_key.isdigit():
            deleted = CartItem.objects.filter(
                cart__user=request.user, product_id=int(item_key)
            ).delete()[0]
        else:
            deleted = CartItem.objects.filter(
                cart__user=request.user, product__product_code=item_key
            ).delete()[0]

        if deleted:
            messages.success(request, "Item removed from cart.")
        else:
            messages.warning(request, "Could not find that item in your cart.")
        return redirect('orders:cart')

    # Guests: remove session product
    cart = request.session.get('cart', {}) or {}

    # If numeric id, map to session key (product_code)
    if item_key.isdigit():
        pid = int(item_key)
        for k, v in list(cart.items()):
            if k.startswith("bundle_"):
                continue
            if str(v.get("product_id")) == str(pid):
                item_key = k
                break

    if cart.pop(item_key, None) is not None:
        save_cart(request, cart)
        messages.success(request, "Item removed from cart.")
    else:
        messages.warning(request, "Could not find that item in your cart.")
    return redirect('orders:cart')


@require_POST
def clear_cart(request):
    """
    Clear the cart.
    For logged-in users, clear BOTH the DB cart (products) and any
    session cart entries (bundles) to avoid leftovers.
    """
    if request.user.is_authenticated:
        db_cart, _ = get_active_cart(request)  # DB cart
        db_cart.items.all().delete()
        # also nuke any session leftovers (e.g., bundles)
        request.session['cart'] = {}
        request.session.modified = True
    else:
        request.session['cart'] = {}
        request.session.modified = True

    messages.success(request, "Cart has been cleared.")
    return redirect('orders:cart')
