# apps/orders/views/general.py

import logging
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.urls import reverse

from apps.orders.models import Order
from apps.orders.utils.cart import clear_session_cart
from apps.orders.views.cart_views import clear_cart
from apps.users.models import ShippingAddress

logger = logging.getLogger(__name__)


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
    Unified success page for both flows.

    - Inline Payment Element: /orders/success/?pi=pi_...
    - Hosted Checkout:        /orders/success/?session_id=cs_...

    This view is read-only: it does not mark orders paid (webhook handles that).
    """
    pi = request.GET.get("pi")
    session_id = request.GET.get("session_id")

    order = None
    source_label = ""

    if pi:
        order = Order.objects.filter(stripe_payment_intent=pi).first()
        source_label = f"pi={pi}"
    elif session_id and session_id != "{CHECKOUT_SESSION_ID}":
        order = Order.objects.filter(stripe_session_id=session_id).first()
        source_label = f"session_id={session_id}"
    else:
        messages.warning(request, "Missing or invalid payment reference.")
        return redirect("products:product_list")

    if not order:
        messages.warning(request, "Order not found for this payment reference.")
        return redirect("products:product_list")

    logger.info("[ORDER] Success page for Order #%s (%s)", order.id, source_label)

    # Clear the cart safely (idempotent)
    if request.user.is_authenticated:
        clear_cart(request)
    else:
        clear_session_cart(request)

    context = {
        "order": order,
        "support_email": getattr(settings, "SUPPORT_EMAIL", "support@example.com"),
        "contact_page_url": "/contact/",
        "settings": settings,
    }
    return render(request, "orders/checkout_success.html", context)


def checkout_cancel_view(request):
    return render(request, 'orders/checkout_cancel.html')


@login_required
def order_history_view(request):
    return render(request, 'orders/order_history.html')
