"""
General views for order processing.
Handles checkout success, cancellation, and order history.
Located at apps/orders/views/general.py
"""

import logging
import stripe
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.urls import reverse

from apps.orders.models import Order
from apps.orders.utils.cart import clear_session_cart
from apps.orders.views.cart_views import clear_cart
from apps.users.models import ShippingAddress
from apps.orders.utils.stripe_helpers import retrieve_checkout_session

logger = logging.getLogger(__name__)

stripe.api_key = settings.STRIPE_SECRET_KEY
stripe.api_version = getattr(settings, "STRIPE_API_VERSION", None)


def inline_checkout_view(request):
    """
    Display the inline checkout page with Stripe Payment Element.
    """
    saved = None
    if request.user.is_authenticated:
        saved = ShippingAddress.objects.filter(
            user=request.user, is_default=True
        ).first()

    return render(request, "orders/inline_checkout.html", {
        "stripe_publishable_key": settings.STRIPE_PUBLISHABLE_KEY,
        "success_url": request.build_absolute_uri(reverse("orders:success")),
        "saved_address": saved,
    })


def checkout_success_view(request):
    """
    Success page for inline or hosted checkout.

    Webhooks mark orders paid; as a resiliency we also mark paid here if the
    PaymentIntent already reports `succeeded`. Then we clear the cart only
    when payment is confirmed.
    """
    pi = request.GET.get("pi")
    session_id = request.GET.get("session_id")
    logger.info(
        f"[ORDER] checkout_success called with pi={pi}, session_id={session_id}"
    )

    order = None
    session = None
    source_label = ""

    if pi:
        order = Order.objects.filter(stripe_payment_intent=pi).first()
        source_label = f"pi={pi}"
    elif session_id and session_id != "{CHECKOUT_SESSION_ID}":
        order = Order.objects.filter(stripe_session_id=session_id).first()
        source_label = f"session_id={session_id}"
        try:
            session = retrieve_checkout_session(session_id)
        except Exception:
            session = None
    else:
        messages.warning(request, "Missing or invalid payment reference.")
        return redirect("products:product_list")

    if not order:
        messages.warning(
            request, "Order not found for this payment reference."
        )
        return redirect("products:product_list")

    logger.info(
        "[ORDER] Success page for Order #%s (%s)", order.id, source_label
    )

    # Determine confirmation email
    confirmation_email = order.contact_email or (
        order.user.email if order.user_id else None
    )

    paid = order.is_paid

    # Fallback: check Stripe PaymentIntent or Checkout Session status
    if not confirmation_email or not paid:
        try:
            if pi:
                intent = stripe.PaymentIntent.retrieve(pi)
                if getattr(
                    intent, "status", None
                ) == "succeeded" and not order.is_paid:
                    order.is_paid = True
                    order.save(update_fields=["is_paid"])
                paid = order.is_paid
                if not confirmation_email:
                    confirmation_email = getattr(
                        intent, "receipt_email", None
                    )
            elif session and getattr(
                session, "customer_details", None
            ):
                if not confirmation_email:
                    confirmation_email = getattr(
                        session.customer_details, "email", None
                    )
        except Exception as e:
            logger.debug(
                "[ORDER] Stripe fallback lookups failed: %s", e
            )

    # Clear the cart only if payment is confirmed
    if paid:
        if request.user.is_authenticated:
            clear_cart(request)
        else:
            clear_session_cart(request)

    context = {
        "order": order,
        "support_email": getattr(
            settings, "SUPPORT_EMAIL", "hello.autovise@gmail.com"
        ),
        "contact_page_url": "/contact/",
        "confirmation_email": confirmation_email,
        "settings": settings,
    }

    return render(request, "orders/checkout_success.html", context)


def checkout_cancel_view(request):
    return render(request, 'orders/checkout_cancel.html')


@login_required
def order_history_view(request):
    return render(request, 'orders/order_history.html')
