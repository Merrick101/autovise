# apps/orders/utils/order.py

import logging

from django.conf import settings
from django.db import transaction
from django.template.loader import render_to_string

from apps.orders.models import Order
from apps.orders.utils.email import send_order_confirmation_email

logger = logging.getLogger(__name__)


def update_order_from_stripe_session(payload):
    """
    Handle *either* a Checkout Session object or a PaymentIntent object.
    Idempotently marks the Order paid and sends the confirmation email (webhook-only).
    """
    # Stripe sends dict-like objects; normalize accessors
    obj_type = payload.get("object")  # "checkout.session" or "payment_intent"
    metadata = payload.get("metadata") or {}
    order = None

    # --- 1) Try metadata.order_id for both shapes ---
    order_id = metadata.get("order_id")
    if order_id:
        order = Order.objects.filter(pk=order_id).first()
        if not order:
            logger.warning("[ORDER] Metadata order_id=%s not found", order_id)

    # --- 2) Determine the PaymentIntent ID and secondary lookup keys ---
    pi_id = None
    session_id = None
    customer_email = None

    if obj_type == "checkout.session":
        session_id = payload.get("id")
        customer_email = (payload.get("customer_details") or {}).get("email") or payload.get("customer_email")
        pi_id = payload.get("payment_intent")  # Session stores PI id here

        # Fallback
        if order is None and session_id:
            order = Order.objects.filter(stripe_session_id=session_id).first()
            if not order:
                logger.error("[ORDER] No Order found for stripe_session_id=%r", session_id)
                return None

    elif obj_type == "payment_intent":
        pi_id = payload.get("id")
        # PaymentIntent can carry receipt_email directly
        customer_email = payload.get("receipt_email")
        # Fallback
        if order is None and pi_id:
            order = Order.objects.filter(stripe_payment_intent=pi_id).first()
            if not order:
                logger.error("[ORDER] No Order found for stripe_payment_intent=%r", pi_id)
                return None
    else:
        logger.debug("[ORDER] Unsupported Stripe object type: %r", obj_type)
        return None

    # Final fallback to user email if user exists
    if not customer_email and order.user and getattr(order.user, "email", None):
        customer_email = order.user.email

    # --- 3) Idempotent state transition ---
    if not order.is_paid:
        with transaction.atomic():
            order.is_paid = True
            # Always persist PI id when known
            if pi_id and order.stripe_payment_intent != pi_id:
                order.stripe_payment_intent = pi_id
                order.save(update_fields=["is_paid", "stripe_payment_intent"])
            else:
                order.save(update_fields=["is_paid"])
        logger.info("[ORDER] Marked Order #%s paid (pi=%s)", order.id, order.stripe_payment_intent)

        # 4) Fire-and-forget email
        try:
            send_order_confirmation_email(order, to_email=customer_email)
        except Exception as e:
            logger.exception("[EMAIL] Failed confirmation for Order #%s: %s", order.id, e)
    else:
        logger.info("[ORDER] Order #%s already paid; skipping", order.id)

    return order
