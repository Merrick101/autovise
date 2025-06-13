# apps/orders/views/checkout.py

from django.shortcuts import redirect
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from apps.orders.utils.cart import get_active_cart, calculate_cart_summary
from apps.orders.utils.stripe_helpers import create_checkout_session
import logging

logger = logging.getLogger(__name__)


@login_required
def checkout_view(request):
    cart_data, cart_type = get_active_cart(request)

    if cart_type == 'db' and not cart_data.items.exists():
        messages.error(request, "Your cart is empty. Add items before checking out.")
        return redirect('orders:cart')
    elif cart_type == 'session' and len(cart_data) == 0:
        messages.error(request, "Your cart is empty. Add items before checking out.")
        return redirect('orders:cart')

    summary = calculate_cart_summary(request, cart_data, cart_type)
    line_items = []
    product_ids = []

    for item in summary['cart_items']:
        product = item['product']
        line_items.append({
            'price_data': {
                'currency': 'gbp',
                'product_data': {'name': product.name},
                'unit_amount': int(item['subtotal'] / item['quantity'] * 100),
            },
            'quantity': item['quantity'],
        })
        product_ids.append(str(product.id))

    if summary['delivery_fee'] > 0:
        line_items.append({
            'price_data': {
                'currency': 'gbp',
                'product_data': {'name': 'Delivery Fee'},
                'unit_amount': int(summary['delivery_fee'] * 100),
            },
            'quantity': 1,
        })

    metadata = {
        'user_id': str(request.user.id),
        'product_ids': ','.join(product_ids)
    }

    expected_total = sum(item['price_data']['unit_amount'] * item['quantity'] for item in line_items)
    logger.info(f"[CHECKOUT] Stripe line item total (pence): {expected_total} | £{expected_total / 100:.2f}")

    session = create_checkout_session(
        user=request.user,
        line_items=line_items,
        metadata=metadata,
        success_url=request.build_absolute_uri('/checkout/success/'),
        cancel_url=request.build_absolute_uri('/checkout/cancel/')
    )

    if session:
        return redirect(session.url)
    else:
        messages.error(request, "Checkout failed. Please try again or contact support.")
        return redirect('orders:cart')
