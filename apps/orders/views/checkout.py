# apps/orders/views/checkout.py

from django.shortcuts import redirect
from django.conf import settings
from apps.orders.utils.cart import get_active_cart
from django.contrib.auth.decorators import login_required
import stripe


stripe.api_key = settings.STRIPE_SECRET_KEY


def checkout_view(request):
    cart_data, cart_type = get_active_cart(request)
    line_items = []
    product_ids = []

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
            product_ids.append(str(item.product.id))
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
            product_ids.append(str(item['product_id']))

    metadata = {
        'user_id': str(request.user.id) if request.user.is_authenticated else 'guest',
        'product_ids': ','.join(product_ids)
    }

    checkout_session = stripe.checkout.Session.create(
        payment_method_types=['card'],
        mode='payment',
        line_items=line_items,
        success_url=request.build_absolute_uri('/checkout/success/'),
        cancel_url=request.build_absolute_uri('/checkout/cancel/'),
        metadata=metadata,
    )

    return redirect(checkout_session.url)
