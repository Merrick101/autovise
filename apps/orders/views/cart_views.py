# apps/orders/views/cart_views.py

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
    """
    try:
        quantity = int(request.POST.get('quantity', 1))
    except (TypeError, ValueError):
        quantity = 1

    if quantity < 1:
        messages.error(request, "Quantity must be at least 1.")
        return redirect('orders:cart')

    cart_data, cart_type = get_active_cart(request)

    # Authenticated users: DB cart (products only)
    if cart_type == 'db':
        # Accept either numeric product_id or product_code
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

    # Guest users: session cart
    cart = cart_data or {}
    if item_key in cart:
        cart[item_key]['quantity'] = quantity
        save_cart(request, cart)  # persists and marks session modified
        messages.success(request, "Quantity updated.")
    else:
        messages.warning(request, "Could not find that item in your cart.")
    return redirect('orders:cart')


@require_POST
def remove_item(request, item_key):
    """
    Remove a cart line for guest session or DB cart.
    """
    cart_data, cart_type = get_active_cart(request)

    if cart_type == 'db':
        # Accept either numeric product_id or product_code
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

    # Guest: session cart
    cart = cart_data or {}
    if cart.pop(item_key, None) is not None:
        save_cart(request, cart)
        messages.success(request, "Item removed from cart.")
    else:
        messages.warning(request, "Could not find that item in your cart.")
    return redirect('orders:cart')


@require_POST
def clear_cart(request):
    cart_data, cart_type = get_active_cart(request)

    if cart_type == 'db':
        cart_data.items.all().delete()
    else:
        request.session['cart'] = {}
        request.session.modified = True

    messages.success(request, "Cart has been cleared.")
    return redirect('orders:cart')
