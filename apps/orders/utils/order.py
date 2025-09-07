"""
Utilities for order processing and fulfillment.
Contains logic to idempotently mark orders paid.
Located at apps/orders/utils/order.py
"""

import logging
from django.db import transaction
from apps.orders.models import Order
from apps.orders.utils.email import send_order_confirmation_email

logger = logging.getLogger(__name__)


def update_order_from_stripe_session(payload):
    """
    Handle *either* a Checkout Session object or a PaymentIntent object.
    Idempotently marks the Order paid and
    sends the confirmation email (webhook-only).
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
        customer_email = payload.get("receipt_email")

        # Try charge billing_details
        if not customer_email:
            try:
                charges = (payload.get("charges") or {}).get("data") or []
                if charges:
                    customer_email = (charges[0].get("billing_details") or {}).get("email")
            except Exception:
                pass

        # try metadata echo from update-intent
        if not customer_email:
            customer_email = (payload.get("metadata") or {}).get("customer_email")

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
            update_fields = ["is_paid"]

            # Persist PI id if we learned it (or it changed)
            if pi_id and order.stripe_payment_intent != pi_id:
                order.stripe_payment_intent = pi_id
                update_fields.append("stripe_payment_intent")

            order.save(update_fields=update_fields)

            # Always mark user as no longer first-time once a paid order exists
            mark_user_not_first_time(order.user)

        logger.info("[ORDER] Marked Order #%s paid (pi=%s)",
                    order.id, order.stripe_payment_intent)

        try:
            send_order_confirmation_email(order, to_email=customer_email)
        except Exception as e:
            logger.exception("[EMAIL] Failed confirmation for Order #%s: %s", order.id, e)
    else:
        logger.info("[ORDER] Order #%s already paid; skipping", order.id)

    return order


def mark_user_not_first_time(user):
    """
    Disable the first-time flag safely once a user has a paid order.
    """
    if not user:
        return
    try:
        prof = getattr(user, "profile", None)
        if prof and prof.is_first_time_buyer:
            prof.is_first_time_buyer = False
            prof.save(update_fields=["is_first_time_buyer"])
    except Exception:
        # keep webhook idempotent; do not raise
        pass
