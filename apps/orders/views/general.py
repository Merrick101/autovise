# apps/orders/views/general.py

from django.conf import settings
from django.contrib import messages
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from apps.orders.models import Order
from apps.orders.utils.stripe_helpers import retrieve_checkout_session
from apps.orders.utils.cart import clear_session_cart
from apps.orders.views.cart_views import clear_cart
import logging

logger = logging.getLogger(__name__)


def checkout_success_view(request):
    """
    Display the order confirmation page after a successful Stripe checkout.
    Expects ?session_id=<SESSION_ID> in the URL.
    """
    # 1) Extract and validate the session_id
    session_id = request.GET.get("session_id")
    logger.info(f"[ORDER] checkout_success called with session_id={session_id}")

    if not session_id or session_id == "{CHECKOUT_SESSION_ID}":
        messages.warning(
            request,
            "Invalid session ID. Please check your email or contact support."
        )
        return redirect("products:product_list")

    # 2) Retrieve the Stripe session to verify payment
    session = retrieve_checkout_session(session_id)
    if not session or session.payment_status != "paid":
        messages.error(
            request,
            "Unable to verify your payment. Please contact support if your card was charged."
        )
        return redirect("products:product_list")

    # 3) Find Order by stripe_session_id
    order = Order.objects.filter(stripe_session_id=session_id).first()
    if not order:
        messages.warning(
            request,
            "Order not found for this session. Please contact support."
        )
        return redirect("products:product_list")

    # Log successful order
    logger.info("[ORDER] Success page for Order #%s (session=%s)", order.id, session_id)

    # 4) Mark the order as paid and store payment intent
    if not order.is_paid:
        order.is_paid = True
        order.stripe_payment_intent = session.payment_intent
        order.save(update_fields=["is_paid", "stripe_payment_intent"])

    # 5) Clear the cart after a confirmed order
    if request.user.is_authenticated:
        clear_cart(request)
    else:
        clear_session_cart(request)

    # 6) Render the confirmation template
    context = {
        "order": order,
        "support_email": getattr(settings, "SUPPORT_EMAIL", "support@example.com"),
        "contact_page_url": "/contact/",
    }
    return render(request, "orders/checkout_success.html", context)


def checkout_cancel_view(request):
    return render(request, 'orders/checkout_cancel.html')


@login_required
def order_history_view(request):
    return render(request, 'orders/order_history.html')
