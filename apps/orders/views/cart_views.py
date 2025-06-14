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


def add_bundle_to_cart_view(request, bundle_id):
    bundle = get_object_or_404(Bundle, id=bundle_id)
    cart = request.session.get('cart', {})

    item_key = f"bundle_{bundle.id}"
    quantity = int(request.POST.get('quantity', 1))

    if item_key in cart:
        cart[item_key]['quantity'] += quantity
    else:
        cart[item_key] = {
            'type': 'bundle',
            'name': bundle.name,
            'price': str(bundle.price),
            'quantity': quantity,
        }

    request.session['cart'] = cart

    messages.success(request, f"Added {bundle.name} to your cart.")

    return HttpResponseRedirect(request.META.get('HTTP_REFERER', '/'))


def cart_view(request):
    cart_data, cart_type = get_active_cart(request)
    context = calculate_cart_summary(request, cart_data, cart_type)
    return render(request, 'orders/cart.html', context)


@require_POST
def update_quantity(request, item_key):
    quantity = int(request.POST.get('quantity', 1))
    if quantity < 1:
        messages.error(request, "Quantity must be at least 1.")
        return redirect('orders:cart')

    cart_data, cart_type = get_active_cart(request)

    if cart_type == 'db':
        # Only applies to products
        cart_item = CartItem.objects.filter(cart__user=request.user, product_id=item_key).first()
        if cart_item:
            cart_item.quantity = quantity
            cart_item.save()
    else:
        cart = cart_data
        if item_key in cart:
            cart[item_key]['quantity'] = quantity
            save_cart(request, cart)

    messages.success(request, "Cart updated.")
    return redirect('orders:cart')


@require_POST
def remove_item(request, item_key):
    cart_data, cart_type = get_active_cart(request)

    if cart_type == 'db':
        # Only applies to Product model items
        CartItem.objects.filter(cart__user=request.user, product_id=item_key).delete()
    else:
        cart = cart_data
        if item_key in cart:
            del cart[item_key]
            save_cart(request, cart)

    messages.success(request, "Item removed from cart.")
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
