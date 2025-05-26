# orders/views.py

from django.shortcuts import redirect, get_object_or_404, render
from apps.products.models import Product
from apps.orders.utils.cart import add_to_cart, get_active_cart, save_cart, calculate_cart_summary
from apps.orders.models import CartItem, Order
from django.views.decorators.http import require_POST
from django.contrib import messages
from django.conf import settings
import stripe


stripe.api_key = settings.STRIPE_SECRET_KEY


def checkout_view(request):
    cart_data, cart_type = get_active_cart(request)
    line_items = []

    if cart_type == 'db':
        for item in cart_data.items.select_related('product'):
            line_items.append({
                'price_data': {
                    'currency': 'gbp',
                    'product_data': {
                        'name': item.product.name,
                    },
                    'unit_amount': int(item.product.price * 100),  # convert to pence
                },
                'quantity': item.quantity,
            })
    else:
        for code, item in cart_data.items():
            line_items.append({
                'price_data': {
                    'currency': 'gbp',
                    'product_data': {
                        'name': item['name'],
                    },
                    'unit_amount': int(item['price'] * 100),
                },
                'quantity': item['quantity'],
            })

    checkout_session = stripe.checkout.Session.create(
        payment_method_types=['card'],
        mode='payment',
        line_items=line_items,
        success_url=request.build_absolute_uri('/checkout/success/'),
        cancel_url=request.build_absolute_uri('/checkout/cancel/'),
        metadata={
            'user_id': request.user.id if request.user.is_authenticated else 'guest'
        }
    )

    return redirect(checkout_session.url)


def add_to_cart_view(request, product_id):
    product = get_object_or_404(Product, id=product_id)

    if request.method == 'POST':
        quantity = int(request.POST.get('quantity', 1))
        add_to_cart(request, product_id, quantity)
        messages.success(request, f"Added {product.name} to your cart.")

    return redirect(request.META.get('HTTP_REFERER', 'products:product_list'))


def cart_view(request):
    cart_data, cart_type = get_active_cart(request)
    context = calculate_cart_summary(request, cart_data, cart_type)
    return render(request, 'orders/cart.html', context)


def is_first_time_user(user):
    return not Order.objects.filter(user=user).exists()


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
