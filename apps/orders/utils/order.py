"""
Utilities for order processing and fulfillment.
Contains logic to idempotently mark orders paid.
Located at apps/orders/utils/order.py
"""

import logging
from django.db import transaction
from django.utils import timezone
from apps.orders.models import Order
from apps.orders.utils.email import send_order_confirmation_email

logger = logging.getLogger(__name__)


def _mark_paid(order, pi_id: str | None, latest_event: str | None):
    if not order.is_paid:
        order.is_paid = True
        order.paid_at = timezone.now()
    order.payment_status = "succeeded"
    if pi_id:
        order.stripe_payment_intent = pi_id
    if latest_event:
        order.stripe_latest_event = latest_event
    order.stripe_last_error = ""
    order.save(update_fields=[
        "is_paid", "paid_at", "payment_status",
        "stripe_payment_intent", "stripe_latest_event", "stripe_last_error"
    ])


def _mark_failed(order, pi_id: str | None, latest_event: str | None, message: str = ""):
    order.payment_status = "failed"
    if pi_id:
        order.stripe_payment_intent = pi_id
    if latest_event:
        order.stripe_latest_event = latest_event
    order.stripe_last_error = (message or "")[:2000]
    order.save(update_fields=[
        "payment_status", "stripe_payment_intent",
        "stripe_latest_event", "stripe_last_error"
    ])


def update_order_from_stripe_session(payload):
    """
    Accepts a Checkout Session or PaymentIntent (event.data.object) and
    updates the matching Order. Idempotent; only sends email on first
    transition to paid. Returns the Order or None.
    """
    obj_type = payload.get("object")  # "payment_intent" or "checkout.session"
    metadata = payload.get("metadata") or {}
    order = None

    # Prefer explicit order id from metadata
    order_id = metadata.get("order_id")
    if order_id:
        order = Order.objects.filter(pk=order_id).first()
        if not order:
            logger.warning("[ORDER] Metadata order_id=%s not found", order_id)

    pi_id = None
    session_id = None
    status = None
    customer_email = None
    latest = None  # what to store in stripe_latest_event

    if obj_type == "checkout.session":
        session_id = payload.get("id")
        pi_id = payload.get("payment_intent")
        status = payload.get("payment_status")  # "paid" | "unpaid"
        customer_email = (
            (payload.get("customer_details") or {}).get("email")
            or payload.get("customer_email")
        )
        latest = f"checkout.session:{status or ''}"

        if order is None and session_id:
            order = Order.objects.filter(stripe_session_id=session_id).first()
        if order is None and pi_id:
            order = Order.objects.filter(stripe_payment_intent=pi_id).first()

        # Persist session id if not already set
        if order and session_id and not order.stripe_session_id:
            try:
                order.stripe_session_id = session_id
                order.save(update_fields=["stripe_session_id"])
            except Exception:
                pass  # ignore uniqueness races; order is already linked elsewhere

    elif obj_type == "payment_intent":
        pi_id = payload.get("id")
        status = payload.get("status")  # "succeeded", "processing", etc.
        customer_email = (
            payload.get("receipt_email")
            or ((payload.get("charges") or {}).get("data") or [{}])[0].get("billing_details", {}).get("email")
            or (payload.get("metadata") or {}).get("customer_email")
        )
        latest = f"payment_intent:{status or ''}"

        if order is None and pi_id:
            order = Order.objects.filter(stripe_payment_intent=pi_id).first()
    else:
        logger.debug("[ORDER] Unsupported Stripe object type: %r", obj_type)
        return None

    if order is None:
        logger.error(
            "[ORDER] No Order found for Stripe object type=%r (pi=%r, session=%r, meta order_id=%r)",
            obj_type, pi_id, session_id, order_id
        )
        return None

    # Email fallback chain
    if not customer_email:
        customer_email = order.contact_email or (
            getattr(order.user, "email", None) if order.user_id else None
        )

    was_paid = bool(order.is_paid)

    # --- Transition handling ---
    if obj_type == "checkout.session":
        if status == "paid":
            with transaction.atomic():
                _mark_paid(order, pi_id, latest)
            mark_user_not_first_time(order.user)
        elif status in {"unpaid", "expired"}:
            _mark_failed(order, pi_id, latest, "Checkout session not paid")
        else:
            # Keep as pending for any unusual states
            order.payment_status = "pending"
            order.stripe_latest_event = latest or ""
            order.save(update_fields=["payment_status", "stripe_latest_event"])

    elif obj_type == "payment_intent":
        if status == "succeeded":
            with transaction.atomic():
                _mark_paid(order, pi_id, latest)
            mark_user_not_first_time(order.user)
        elif status == "canceled":
            order.payment_status = "canceled"
            order.stripe_latest_event = latest or ""
            if pi_id:
                order.stripe_payment_intent = pi_id
            order.save(update_fields=["payment_status", "stripe_latest_event", "stripe_payment_intent"])
        elif status in {"requires_payment_method", "requires_action"}:
            msg = ((payload.get("last_payment_error") or {}).get("message")) or "Payment requires action/new method"
            _mark_failed(order, pi_id, latest, msg)
        elif status == "processing":
            order.payment_status = "pending"
            order.stripe_latest_event = latest or ""
            if pi_id:
                order.stripe_payment_intent = pi_id
            order.save(update_fields=["payment_status", "stripe_latest_event", "stripe_payment_intent"])
        else:
            logger.info("[ORDER] PaymentIntent %s status=%s; no state change.", pi_id, status)

    # Send email only on first transition to paid
    if order.is_paid and not was_paid:
        try:
            send_order_confirmation_email(order, to_email=customer_email)
        except Exception as e:
            logger.exception("[EMAIL] Failed confirmation for Order #%s: %s", order.id, e)

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
