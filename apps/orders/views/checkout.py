# apps/orders/views/checkout.py

from decimal import Decimal
import logging

from django.contrib import messages
from django.shortcuts import redirect, render
from django.urls import reverse

from apps.orders.models import Order, OrderItem
from apps.orders.utils.cart import get_active_cart, calculate_cart_summary, clear_session_cart
from apps.orders.utils.stripe_helpers import create_checkout_session
from apps.orders.views.cart_views import clear_cart

logger = logging.getLogger(__name__)


def checkout_view(request):
    # 1) fetch & validate cart
    cart_data, cart_type = get_active_cart(request)
    if cart_type == "db" and not cart_data.items.exists():
        messages.error(request, "Your cart is empty. Add items before checking out.")
        return redirect("orders:cart")
    if cart_type == "session" and not cart_data:
        messages.error(request, "Your cart is empty. Add items before checking out.")
        return redirect("orders:cart")

    # 2) build summary & Stripe line_items
    summary = calculate_cart_summary(request, cart_data, cart_type)
    line_items = []
    for ci in summary["cart_items"]:
        # pick the right display name
        display_name = ci["bundle"].name if ci["is_bundle"] else ci["product"].name
        unit_amount = int(ci["discounted_price"] * 100)
        line_items.append({
            "price_data": {
                "currency": "gbp",
                "product_data": {"name": display_name},
                "unit_amount": unit_amount,
            },
            "quantity": ci["quantity"],
        })

    # 3) add delivery fee
    if summary["delivery_fee"] > 0:
        line_items.append({
            "price_data": {
                "currency": "gbp",
                "product_data": {"name": "Delivery Fee"},
                "unit_amount": int(summary["delivery_fee"] * 100),
            },
            "quantity": 1,
        })

    # 4) create our Order record
    order = Order.objects.create(
        user=request.user if request.user.is_authenticated else None,
        total_price=Decimal(summary["grand_total"]),
        delivery_fee=Decimal(summary["delivery_fee"]),
    )

    # 5) prepare Stripe session
    metadata = {
        "order_id": str(order.pk),
        "user_id": str(request.user.id) if request.user.is_authenticated else "guest",
    }
    success_url = (
        request.build_absolute_uri(reverse("orders:checkout_success"))
        + "?session_id={CHECKOUT_SESSION_ID}"
    )
    cancel_url = request.build_absolute_uri(reverse("orders:checkout_cancel"))

    session = create_checkout_session(
        user=request.user,
        line_items=line_items,
        metadata=metadata,
        success_url=success_url,
        cancel_url=cancel_url,
    )
    if not session:
        messages.error(request, "Checkout failed. Please try again or contact support.")
        return redirect("orders:cart")

    # save the Stripe session ID for lookup on success
    order.stripe_session_id = session.id
    order.save(update_fields=["stripe_session_id"])

    # 6) persist OrderItems
    for ci in summary["cart_items"]:
        if ci["is_bundle"]:
            OrderItem.objects.create(
                order=order,
                bundle=ci["bundle"],
                quantity=ci["quantity"],
                unit_price=ci["discounted_price"],
            )
        else:
            OrderItem.objects.create(
                order=order,
                product=ci["product"],
                quantity=ci["quantity"],
                unit_price=ci["unit_price"],
            )

    # 7) clear the cart (defer session vs. db)
    if request.user.is_authenticated:
        clear_cart(request)
    else:
        clear_session_cart(request)

    # 8) hand off to Stripe
    return redirect(session.url, code=303)
