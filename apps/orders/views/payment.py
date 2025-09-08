"""
Views for handling payment intents with Stripe.
Covers both creating a new PaymentIntent and updating an existing one.
Located at apps/orders/views/payment.py
"""

import json
import logging
from decimal import Decimal
from django.db import transaction
from django.http import JsonResponse, HttpResponseBadRequest
from django.views.decorators.http import require_POST
from django.conf import settings

import stripe
from apps.orders.models import Order, OrderItem
from apps.orders.utils.cart import get_active_cart, calculate_cart_summary
from apps.users.models import ShippingAddress

logger = logging.getLogger(__name__)

stripe.api_key = settings.STRIPE_SECRET_KEY
stripe.api_version = getattr(settings, "STRIPE_API_VERSION", None)


def _to_pence(amount_gbp: Decimal) -> int:
    return int((amount_gbp * Decimal("100")).quantize(Decimal("1")))


@require_POST
def create_payment_intent(request):
    """
    Create (or reuse) a Stripe PaymentIntent and a single pending Order
    per browser session. Returns { client_secret, payment_intent_id, order_id }.
    """
    try:
        # Ensure session key is set for storing the pending order id
        if not request.session.session_key:
            request.session.save()

        # ---- parse body (JSON preferred) ----
        if (request.META.get("CONTENT_TYPE") or "").startswith("application/json"):
            try:
                source = json.loads((request.body or b"").decode() or "{}")
            except json.JSONDecodeError:
                source = {}
        else:
            source = request.POST

        # guest receipt email (only when not authenticated)
        guest_email = None
        if not request.user.is_authenticated:
            guest_email = (source.get("guest_email") or "").strip() or None

        # ---- cart summary ----
        cart_data, cart_type = get_active_cart(request)
        summary = calculate_cart_summary(request, cart_data, cart_type)
        if not summary["cart_items"]:
            return HttpResponseBadRequest("Cart empty")

        # ---- shipping fields ----
        shipping_fields = {
            k: (source.get(k) or "").strip()
            for k in [
                "shipping_name",
                "shipping_line1",
                "shipping_line2",
                "shipping_city",
                "shipping_postcode",
                "shipping_country",
                "shipping_phone",
            ]
        }
        if shipping_fields["shipping_country"]:
            shipping_fields["shipping_country"] = shipping_fields["shipping_country"].upper()

        save_shipping = str(source.get("save_shipping", "")).lower() in {"1", "true", "on", "yes"}

        amount_pence = _to_pence(summary["grand_total"])

        with transaction.atomic():
            # ---- reuse one pending order per session ----
            order = None
            pending_id = request.session.get("pending_order_id")
            if pending_id:
                # lock it to avoid parallel creation
                order = (
                    Order.objects.select_for_update()
                    .filter(id=pending_id, is_paid=False)
                    .first()
                )

            if order:
                # refresh core fields
                order.user = request.user if request.user.is_authenticated else None
                order.total_amount = summary["total_before_discount"]
                order.discount_total = summary["bundle_discount"] + summary["cart_discount"]
                order.delivery_fee = summary["delivery_fee"]
                order.total_price = summary["grand_total"]
                order.contact_email = (
                    request.user.email if request.user.is_authenticated else (guest_email or "")
                )
                for f, v in shipping_fields.items():
                    setattr(order, f, v)
                order.save()
                # refresh items
                order.items.all().delete()
            else:
                order = Order.objects.create(
                    user=request.user if request.user.is_authenticated else None,
                    total_amount=summary["total_before_discount"],
                    discount_total=summary["bundle_discount"] + summary["cart_discount"],
                    delivery_fee=summary["delivery_fee"],
                    total_price=summary["grand_total"],
                    contact_email=(
                        request.user.email if request.user.is_authenticated else (guest_email or "")
                    ),
                    **shipping_fields,
                    is_paid=False,
                )
                request.session["pending_order_id"] = order.id
                request.session.modified = True

            OrderItem.objects.bulk_create(
                [
                    OrderItem(
                        order=order,
                        product=item["product"],
                        bundle=item["bundle"],
                        quantity=item["quantity"],
                        unit_price=item["discounted_price"],
                    )
                    for item in summary["cart_items"]
                ]
            )

            # ---- optionally store default shipping address ----
            if request.user.is_authenticated and save_shipping and shipping_fields.get("shipping_line1"):
                try:
                    data = {
                        "name": shipping_fields["shipping_name"],
                        "line1": shipping_fields["shipping_line1"],
                        "line2": shipping_fields.get("shipping_line2", ""),
                        "city": shipping_fields.get("shipping_city", ""),
                        "postcode": shipping_fields.get("shipping_postcode", ""),
                        "country": shipping_fields.get("shipping_country") or "GB",
                        "phone": shipping_fields.get("shipping_phone", ""),
                        "is_default": True,
                    }
                    addr = ShippingAddress.objects.filter(user=request.user, is_default=True).first()
                    if addr:
                        for k, v in data.items():
                            setattr(addr, k, v)
                        addr.save()
                    else:
                        ShippingAddress.objects.create(user=request.user, **data)
                except Exception as e:
                    logger.warning("[CHECKOUT] Could not save default shipping address: %s", e)

            # ---- reuse or create payment intent ----
            intent = None
            email_for_receipt = (
                request.user.email if request.user.is_authenticated else guest_email
            )

            if order.stripe_payment_intent:
                # Fetch & modify if still active
                si = stripe.PaymentIntent.retrieve(order.stripe_payment_intent)
                status = si.get("status")
                if status in ("requires_payment_method", "requires_confirmation", "requires_action", "processing"):
                    intent = stripe.PaymentIntent.modify(
                        order.stripe_payment_intent,
                        amount=amount_pence,
                        shipping=order.shipping_for_stripe(),
                        receipt_email=email_for_receipt,
                        metadata={
                            "order_id": str(order.id),
                            "user_id": str(getattr(request.user, "id", "guest")),
                        },
                    )
                elif status in ("canceled", "succeeded"):
                    # start a fresh PI (should be rare for a still-pending order)
                    intent = stripe.PaymentIntent.create(
                        amount=amount_pence,
                        currency="gbp",
                        payment_method_types=["card"],
                        shipping=order.shipping_for_stripe(),
                        receipt_email=email_for_receipt,
                        metadata={
                            "order_id": str(order.id),
                            "user_id": str(getattr(request.user, "id", "guest")),
                        },
                        # stable idempotency per order
                        idempotency_key=f"order-{order.id}-create-v1",
                    )
                    if order.stripe_payment_intent != intent.id:
                        order.stripe_payment_intent = intent.id
                        order.save(update_fields=["stripe_payment_intent"])
                else:
                    # default to returning the current intent
                    intent = si
            else:
                intent = stripe.PaymentIntent.create(
                    amount=amount_pence,
                    currency="gbp",
                    payment_method_types=["card"],
                    shipping=order.shipping_for_stripe(),
                    receipt_email=email_for_receipt,
                    metadata={
                        "order_id": str(order.id),
                        "user_id": str(getattr(request.user, "id", "guest")),
                    },
                    idempotency_key=f"order-{order.id}-create-v1",
                )
                order.stripe_payment_intent = intent.id
                order.save(update_fields=["stripe_payment_intent"])

        return JsonResponse(
            {
                "client_secret": intent.client_secret,
                "payment_intent_id": intent.id,
                "order_id": order.id,
            }
        )

    except Exception as e:
        logger.exception("[CHECKOUT] Failed creating payment intent: %s", e)
        return HttpResponseBadRequest("Error creating payment intent")


@require_POST
def update_payment_intent(request):
    """
    Set/overwrite receipt_email (and metadata) on an existing PaymentIntent.
    """
    try:
        if (request.META.get("CONTENT_TYPE") or "").startswith("application/json"):
            data = json.loads((request.body or b"").decode() or "{}")
        else:
            data = request.POST

        pi_id = (data.get("pi_id") or "").strip()
        guest_email = (data.get("guest_email") or "").strip()

        if not pi_id or not guest_email:
            return HttpResponseBadRequest("Missing pi_id or guest_email")

        stripe.PaymentIntent.modify(
            pi_id,
            receipt_email=guest_email,
            metadata={"customer_email": guest_email},
        )
        logger.info("[CHECKOUT] Updated PI %s with guest email %s", pi_id, guest_email)
        return JsonResponse({"ok": True})
    except Exception as e:
        logger.exception("[CHECKOUT] Failed to update PI: %s", e)
        return HttpResponseBadRequest("Error updating payment intent")
