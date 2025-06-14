# apps/orders/views/general.py

from django.contrib import messages
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from apps.orders.models import Order
from apps.orders.utils.stripe_helpers import retrieve_checkout_session
from apps.orders.utils.cart import clear_session_cart
import logging

logger = logging.getLogger(__name__)


def checkout_success_view(request):
    # This assumes the session ID was stored during webhook processing
    # or passed as a query parameter after successful payment.
    session_id = request.GET.get('session_id')
    logger.info(f"[ORDER DEBUG] Looking up Order with session ID from URL: {session_id}")

    logger.debug(f"[SUCCESS] Query string: {request.GET.urlencode()}")
    logger.debug(f"[SUCCESS] Extracted session_id: {session_id}")

    if not session_id or session_id == "{CHECKOUT_SESSION_ID}":
        messages.warning(request, "Invalid session ID. Please check your email or contact support.")
        return redirect('products:product_list')

    session = retrieve_checkout_session(session_id)

    if not session:
        messages.error(request, "Unable to verify your payment session. Please contact support.")
        return redirect('products:product_list')

    # Try to find the order using the real session ID
    order = Order.objects.filter(stripe_session_id=session_id).first()

    if not order:
        messages.warning(request, "Order not found for this session. Please contact support if this was unexpected.")
        return redirect('products:product_list')

    if not request.user.is_authenticated:
        clear_session_cart(request)

    context = {
        'order': order,
        'support_email': 'hello.autovise@gmail.com',
        'contact_page_url': '/contact/',
    }
    return render(request, 'orders/checkout_success.html', context)


def checkout_cancel_view(request):
    return render(request, 'orders/checkout_cancel.html')


@login_required
def order_history_view(request):
    return render(request, 'orders/order_history.html')
