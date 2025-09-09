"""
Views for checkout process.
Located at apps/orders/views/checkout.py
"""

from decimal import Decimal
import logging

from django.contrib import messages
from django.shortcuts import redirect
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

    def to_minor_units(dec):
        # quantize to 2dp then to whole pennies to avoid float-ish rounding quirks
        return int((dec.quantize(Decimal("0.01")) * 100).to_integral_value())

    line_items = []
    for ci in summary["cart_items"]:
        display_name = ci["bundle"].name if ci["is_bundle"] else ci["product"].name
        unit_amount = to_minor_units(ci["discounted_price"])
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
                "unit_amount": to_minor_units(summary["delivery_fee"]),
            },
            "quantity": 1,
        })

    # 4) create our Order record (persist all figures from summary)
    order = Order.objects.create(
        user=request.user if request.user.is_authenticated else None,
        total_amount=summary["total_before_discount"],
        discount_total=summary["bundle_discount"] + summary["cart_discount"],
        delivery_fee=summary["delivery_fee"],
        total_price=summary["grand_total"],                # amount to be charged
        is_first_order=summary["first_time_discount"],
    )

    guest_email = (request.POST.get("guest_email") or "").strip() if not request.user.is_authenticated else None

    # 5) prepare Stripe session
    metadata = {
        "order_id": str(order.pk),
        "user_id": str(request.user.id) if request.user.is_authenticated else "guest",
    }
    success_url = (
        request.build_absolute_uri(reverse("orders:success"))
        + "?session_id={CHECKOUT_SESSION_ID}"
    )
    cancel_url = request.build_absolute_uri(reverse("orders:checkout_cancel"))

    session = create_checkout_session(
        user=request.user,
        line_items=line_items,
        metadata=metadata,
        success_url=success_url,
        cancel_url=cancel_url,
        customer_email=guest_email if guest_email else (request.user.email if request.user.is_authenticated else None),
    )
    if not session:
        messages.error(request, "Checkout failed. Please try again or contact support.")
        return redirect("orders:cart")

    order.stripe_session_id = session.id
    order.save(update_fields=["stripe_session_id"])

    # 6) persist OrderItems with the *discounted* unit price for both types
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
                unit_price=ci["discounted_price"],  # <-- changed
            )

    # 7) clear the cart
    if request.user.is_authenticated:
        clear_cart(request)
    else:
        clear_session_cart(request)

    # 8) hand off to Stripe
    return redirect(session.url, code=303)
