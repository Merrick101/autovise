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
        unit_amount = int((ci["subtotal"] / ci["quantity"]) * 100)
        line_items.append({
            "price_data": {
                "currency": "gbp",
                "product_data": {"name": ci["product"].name},
                "unit_amount": unit_amount,
            },
            "quantity": ci["quantity"],
        })

    if summary["delivery_fee"] > 0:
        line_items.append({
            "price_data": {
                "currency": "gbp",
                "product_data": {"name": "Delivery Fee"},
                "unit_amount": int(summary["delivery_fee"] * 100),
            },
            "quantity": 1,
        })

    # 3) create Order record
    order = Order.objects.create(
        user=request.user if request.user.is_authenticated else None,
        total_price=Decimal(summary["grand_total"]),
        delivery_fee=Decimal(summary["delivery_fee"]),
    )

    # 4) prepare Stripe session
    metadata = {
        "order_id": str(order.pk),
        "user_id": str(request.user.id) if request.user.is_authenticated else "guest",
    }
    success_url = (
        request.build_absolute_uri(reverse("orders:checkout_success"))
        + "?session_id={CHECKOUT_SESSION_ID}"
    )
    cancel_url = request.build_absolute_uri(reverse("orders:checkout_cancel"))

    logger.info(
        "[CHECKOUT] Stripe expects £%.2f",
        sum(li["price_data"]["unit_amount"] * li["quantity"] / 100 for li in line_items),
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

    # 5) persist OrderItems with bundle vs. product
    for ci in summary["cart_items"]:
        if ci.get("is_bundle", False):
            # save into the bundle FK
            OrderItem.objects.create(
                order=order,
                bundle=ci["product"],
                quantity=ci["quantity"],
                unit_price=Decimal(ci["discounted_price"]),
            )
        else:
            # save into the product FK
            OrderItem.objects.create(
                order=order,
                product=ci["product"],
                quantity=ci["quantity"],
                unit_price=Decimal(ci["unit_price"]),
            )

    # 6) clear cart & redirect to Stripe
    clear_cart(request)
    return redirect(session.url, code=303)
