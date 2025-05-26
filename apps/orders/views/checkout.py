# apps/orders/views/checkout.py

from django.shortcuts import redirect
from django.conf import settings
import stripe

from apps.orders.utils.cart import get_active_cart

stripe.api_key = settings.STRIPE_SECRET_KEY


def checkout_view(request):
    cart_data, cart_type = get_active_cart(request)
    line_items = []

    if cart_type == 'db':
        for item in cart_data.items.select_related('product'):
            line_items.append({
                'price_data': {
                    'currency': 'gbp',
                    'product_data': {'name': item.product.name},
                    'unit_amount': int(item.product.price * 100),
                },
                'quantity': item.quantity,
            })
    else:
        for code, item in cart_data.items():
            line_items.append({
                'price_data': {
                    'currency': 'gbp',
                    'product_data': {'name': item['name']},
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
