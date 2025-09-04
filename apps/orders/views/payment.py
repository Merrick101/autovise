# apps/orders/views/payment.py

import logging
from decimal import Decimal
from django.db import transaction
from django.http import JsonResponse, HttpResponseBadRequest
from django.views.decorators.http import require_POST
from django.conf import settings

import stripe
from apps.orders.models import Order, OrderItem
from apps.orders.utils.cart import get_active_cart, calculate_cart_summary

logger = logging.getLogger(__name__)
stripe.api_key = settings.STRIPE_SECRET_KEY
stripe.api_version = getattr(settings, "STRIPE_API_VERSION", None)


def _to_pence(amount_gbp: Decimal) -> int:
    # Safe Decimal -> int pennies
    return int((amount_gbp * Decimal("100")).quantize(Decimal("1")))


@require_POST
def create_payment_intent(request):
    """
    Create a Stripe PaymentIntent and persist a pending Order.
    Returns: { client_secret, payment_intent_id, order_id }
    """
    try:
        cart_data, cart_type = get_active_cart(request)
        summary = calculate_cart_summary(request, cart_data, cart_type)

        if not summary["cart_items"]:
            return HttpResponseBadRequest("Cart empty")

        guest_email = None
        if not request.user.is_authenticated:
            guest_email = (request.POST.get("guest_email") or "").strip() or None

        with transaction.atomic():
            # 1) Create pending Order
            order = Order.objects.create(
                user=request.user if request.user.is_authenticated else None,
                total_amount=summary["total_before_discount"],
                discount_total=summary["bundle_discount"] + summary["cart_discount"],
                delivery_fee=summary["delivery_fee"],
                total_price=summary["grand_total"],  # grand total to charge
                is_paid=False,
            )

            # 2) Persist OrderItems (discounted unit prices)
            OrderItem.objects.bulk_create([
                OrderItem(
                    order=order,
                    product=item["product"],
                    bundle=item["bundle"],
                    quantity=item["quantity"],
                    unit_price=item["discounted_price"],
                )
                for item in summary["cart_items"]
            ])

            # 3) Create PaymentIntent
            amount_pence = _to_pence(summary["grand_total"])
            idempotency_key = f"pi_{order.id}_{getattr(request.user, 'id', 'guest')}"

            intent = stripe.PaymentIntent.create(
                amount=amount_pence,
                currency="gbp",
                metadata={
                    "order_id": str(order.id),
                    "user_id": str(getattr(request.user, "id", "guest")),
                },
                receipt_email=(
                    request.user.email if request.user.is_authenticated else guest_email
                ),
                automatic_payment_methods={"enabled": True},
                idempotency_key=idempotency_key,  # request option
            )

            order.stripe_payment_intent = intent.id
            order.save(update_fields=["stripe_payment_intent"])

        return JsonResponse({
            "client_secret": intent.client_secret,
            "payment_intent_id": intent.id,
            "order_id": order.id,
        })

    except Exception as e:
        logger.exception("[CHECKOUT] Failed creating payment intent: %s", e)
        return HttpResponseBadRequest("Error creating payment intent")
