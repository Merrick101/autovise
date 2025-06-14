# apps/orders/views/checkout.py

from decimal import Decimal
import logging

from django.contrib import messages
from django.shortcuts import redirect
from django.urls import reverse

from apps.orders.models import Order, OrderItem
from apps.orders.utils.cart import get_active_cart, calculate_cart_summary
from apps.orders.utils.stripe_helpers import create_checkout_session
from apps.orders.views.cart_views import clear_cart

logger = logging.getLogger(__name__)


def checkout_view(request):
    # 1) fetch the cart
    cart_data, cart_type = get_active_cart(request)
    if cart_type == "db" and not cart_data.items.exists():
        messages.error(request, "Your cart is empty. Add items before checking out.")
        return redirect("orders:cart")
    if cart_type == "session" and len(cart_data) == 0:
        messages.error(request, "Your cart is empty. Add items before checking out.")
        return redirect("orders:cart")

    # 2) build summary & Stripe line_items
    summary = calculate_cart_summary(request, cart_data, cart_type)
    line_items = []
    for item in summary["cart_items"]:
        unit_amount = int((item["subtotal"] / item["quantity"]) * 100)
        line_items.append({
            "price_data": {
                "currency": "gbp",
                "product_data": {"name": item["product"].name},
                "unit_amount": unit_amount,
            },
            "quantity": item["quantity"],
        })

    # add delivery fee as its own line if needed
    if summary["delivery_fee"] > 0:
        line_items.append({
            "price_data": {
                "currency": "gbp",
                "product_data": {"name": "Delivery Fee"},
                "unit_amount": int(summary["delivery_fee"] * 100),
            },
            "quantity": 1,
        })

    # 3) create the Order in our DB
    order = Order.objects.create(
        user=request.user if request.user.is_authenticated else None,
        total_price=Decimal(summary["grand_total"]),
        delivery_fee=Decimal(summary["delivery_fee"]),
    )

    # 4) stripe metadata + URLs
    metadata = {
        "order_id": str(order.pk),
        "user_id": str(request.user.id) if request.user.is_authenticated else "guest",
    }
    success_url = request.build_absolute_uri(reverse("orders:checkout_success")) + "?session_id={CHECKOUT_SESSION_ID}"
    cancel_url = request.build_absolute_uri(reverse("orders:checkout_cancel"))

    # 5) kick off Stripe
    logger.info(
        "[CHECKOUT] Stripe expects £%.2f",
        sum(li["price_data"]["unit_amount"] * li["quantity"] / 100.0 for li in line_items),
    )
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

    # 6) persist OrderItems now that we have an order
    for item in summary["cart_items"]:
        OrderItem.objects.create(
            order=order,
            product=item["product"],
            quantity=item["quantity"],
            unit_price=(
                item.get("discounted_price")
                if item.get("is_bundle", False)
                else item["unit_price"]
            ),
        )

    # 7) clear the cart & hand off to Stripe
    #    (make sure clear_cart is imported or available)
    clear_cart(request)
    return redirect(session.url, code=303)
