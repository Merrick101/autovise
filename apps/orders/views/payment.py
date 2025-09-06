# apps/orders/views/payment.py

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
    Create a Stripe PaymentIntent and persist a pending Order.
    Returns: { client_secret, payment_intent_id, order_id }
    """
    try:
        # read JSON body first; fall back to POST
        payload = {}
        if request.META.get("CONTENT_TYPE", "").startswith("application/json"):
            try:
                payload = json.loads(request.body.decode() or "{}")
            except json.JSONDecodeError:
                payload = {}

        guest_email = None
        if not request.user.is_authenticated:
            guest_email = (payload.get("guest_email")
                           or request.POST.get("guest_email")
                           or "").strip() or None

        cart_data, cart_type = get_active_cart(request)
        summary = calculate_cart_summary(request, cart_data, cart_type)
        if not summary["cart_items"]:
            return HttpResponseBadRequest("Cart empty")

        source = payload if payload else request.POST
        shipping_fields = {k: (source.get(k) or "").strip() for k in [
            "shipping_name", "shipping_line1", "shipping_line2", "shipping_city",
            "shipping_postcode", "shipping_country", "shipping_phone"
        ]}

        # Normalize country code before persisting/using it
        country = (shipping_fields.get("shipping_country") or "").strip()
        if country:
            shipping_fields["shipping_country"] = country.upper()

        save_address = str((source.get("save_address") or "")).lower() in {"1", "true", "on", "yes"}

        # Optionally save/overwrite default address for logged-in users
        save_flag = str((payload or request.POST).get("save_shipping", "")).lower() in ("1", "true", "on", "yes")
        if request.user.is_authenticated and save_flag:
            addr_kwargs = {
                "user": request.user,
                "name": shipping_fields.get("shipping_name", ""),
                "line1": shipping_fields.get("shipping_line1", ""),
                "line2": shipping_fields.get("shipping_line2", ""),
                "city": shipping_fields.get("shipping_city", ""),
                "postcode": shipping_fields.get("shipping_postcode", ""),
                "country": shipping_fields.get("shipping_country", "GB"),
                "phone": shipping_fields.get("shipping_phone", ""),
                "is_default": True,
            }
            existing = ShippingAddress.objects.filter(
                user=request.user, is_default=True
            ).first()
            if existing:
                for k, v in addr_kwargs.items():
                    if k != "user":
                        setattr(existing, k, v)
                existing.is_default = True
                existing.save()
            else:
                ShippingAddress.objects.create(**addr_kwargs)

        with transaction.atomic():
            # 1) Create Order (pending)
            order = Order.objects.create(
                user=request.user if request.user.is_authenticated else None,
                total_amount=summary["total_before_discount"],
                discount_total=summary["bundle_discount"] + summary["cart_discount"],
                delivery_fee=summary["delivery_fee"],
                total_price=summary["grand_total"],
                contact_email=(
                    request.user.email if request.user.is_authenticated else (
                        guest_email or ""
                    )
                ),
                **shipping_fields,
                is_paid=False,
            )

            # Save shipping address if requested (and user is authenticated)
            if request.user.is_authenticated and save_address and shipping_fields.get(
                "shipping_line1"
            ):
                ShippingAddress.objects.update_or_create(
                    user=request.user,
                    is_default=True,
                    defaults={
                        "name": shipping_fields["shipping_name"],
                        "line1": shipping_fields["shipping_line1"],
                        "line2": shipping_fields["shipping_line2"],
                        "city": shipping_fields["shipping_city"],
                        "postcode": shipping_fields["shipping_postcode"],
                        "country": shipping_fields["shipping_country"] or "GB",
                        "phone": shipping_fields["shipping_phone"],
                    },
                )

            # 2) Persist items (discounted unit prices)
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

            # 3) Create PI (card only)
            amount_pence = _to_pence(summary["grand_total"])
            idemp = f"pi_{order.id}_{getattr(request.user, 'id', 'guest')}"
            intent = stripe.PaymentIntent.create(
                amount=amount_pence,
                currency="gbp",
                payment_method_types=["card"],  # restrict to card-only
                metadata={
                    "order_id": str(order.id),
                    "user_id": str(getattr(request.user, "id", "guest")),
                },
                receipt_email=(
                    request.user.email if request.user.is_authenticated else guest_email
                ),
                shipping=order.shipping_for_stripe(),
                idempotency_key=idemp,
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


@require_POST
def update_payment_intent(request):
    """
    Set/overwrite receipt_email (and metadata) on an existing PaymentIntent.
    """
    try:
        if request.META.get("CONTENT_TYPE", "").startswith("application/json"):
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
