# apps/orders/views/payment.py

import json
import logging
from decimal import Decimal
from django.http import JsonResponse, HttpResponseBadRequest
from django.views.decorators.http import require_POST
from django.conf import settings

import stripe
from apps.orders.models import Order, OrderItem
from apps.orders.utils.cart import get_active_cart, calculate_cart_summary

logger = logging.getLogger(__name__)
stripe.api_key = settings.STRIPE_SECRET_KEY


@require_POST
def create_payment_intent(request):
    """
    Create a Stripe PaymentIntent and persist a pending Order.
    Returns { clientSecret } for Payment Element.
    """
    try:
        cart_data, cart_type = get_active_cart(request)
        summary = calculate_cart_summary(request, cart_data, cart_type)

        if not summary["cart_items"]:
            return HttpResponseBadRequest("Cart empty")

        # 1) Create pending Order
        order = Order.objects.create(
            user=request.user if request.user.is_authenticated else None,
            total_amount=summary["total_before_discount"],
            discount_total=summary["total_saved"],
            delivery_fee=summary["delivery_fee"],
            total_price=summary["grand_total"],
            is_paid=False,
        )

        # Add OrderItems
        for item in summary["cart_items"]:
            OrderItem.objects.create(
                order=order,
                product=item["product"],
                bundle=item["bundle"],
                quantity=item["quantity"],
                unit_price=item["discounted_price"],
            )

        # 2) Create PaymentIntent
        intent = stripe.PaymentIntent.create(
            amount=int(summary["grand_total"] * Decimal("100")),  # pence
            currency="gbp",
            metadata={"order_id": str(order.id)},
            receipt_email=(
                request.user.email if request.user.is_authenticated else None
            ),
            automatic_payment_methods={"enabled": True},
        )

        order.stripe_payment_intent = intent.id
        order.save(update_fields=["stripe_payment_intent"])

        return JsonResponse({"clientSecret": intent.client_secret})

    except Exception as e:
        logger.exception(f"[CHECKOUT] Failed creating payment intent: {e}")
        return HttpResponseBadRequest("Error creating payment intent")
