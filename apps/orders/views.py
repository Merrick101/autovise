# orders/views.py

from django.shortcuts import redirect, get_object_or_404, render
from apps.products.models import Product
from orders.utils.cart import add_to_cart, get_active_cart, save_cart
from orders.models import CartItem
from django.views.decorators.http import require_POST
from django.contrib import messages


def add_to_cart_view(request, product_id):
    product = get_object_or_404(Product, id=product_id)

    if request.method == 'POST':
        quantity = int(request.POST.get('quantity', 1))
        add_to_cart(request, product_id, quantity)
        messages.success(request, f"Added {product.name} to your cart.")

    return redirect(request.META.get('HTTP_REFERER', 'products:product_list'))


def cart_view(request):
    cart_data, cart_type = get_active_cart(request)
    items = []
    total = 0

    if cart_type == 'db':
        for item in cart_data.items.select_related('product'):
            subtotal = item.quantity * item.product.price
            items.append({
                'product': item.product,
                'quantity': item.quantity,
                'subtotal': subtotal,
            })
            total += subtotal

    else:  # session cart
        for code, item in cart_data.items():
            product = Product.objects.get(id=item['product_id'])
            subtotal = item['quantity'] * product.price
            items.append({
                'product': product,
                'quantity': item['quantity'],
                'subtotal': subtotal,
            })
            total += subtotal

    context = {
        'cart_items': items,
        'cart_total': total,
        'cart_type': cart_type,
    }
    return render(request, 'orders/cart.html', context)


@require_POST
def update_quantity(request, product_id):
    quantity = int(request.POST.get('quantity', 1))
    if quantity < 1:
        messages.error(request, "Quantity must be at least 1.")
        return redirect('orders:cart')

    cart_data, cart_type = get_active_cart(request)

    if cart_type == 'db':
        cart_item = CartItem.objects.filter(cart__user=request.user, product_id=product_id).first()
        if cart_item:
            cart_item.quantity = quantity
            cart_item.save()
    else:
        cart = cart_data
        product_code = Product.objects.get(id=product_id).product_code
        if product_code in cart:
            cart[product_code]['quantity'] = quantity
            save_cart(request, cart)

    messages.success(request, "Cart updated.")
    return redirect('orders:cart')


@require_POST
def remove_item(request, product_id):
    cart_data, cart_type = get_active_cart(request)

    if cart_type == 'db':
        CartItem.objects.filter(cart__user=request.user, product_id=product_id).delete()
    else:
        cart = cart_data
        product_code = Product.objects.get(id=product_id).product_code
        if product_code in cart:
            del cart[product_code]
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
