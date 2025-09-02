# apps/orders/utils/order.py

import logging

from django.conf import settings
from django.db import transaction
from django.template.loader import render_to_string

from apps.orders.models import Order
from apps.orders.utils.email import send_order_confirmation_email

logger = logging.getLogger(__name__)


# apps/orders/utils/order.py

def update_order_from_stripe_session(session):
    """
    Idempotently mark the existing Order paid and send confirmation email.
    Tries metadata['order_id'] first, then falls back to stripe_session_id.
    """
    metadata = getattr(session, "metadata", {}) or {}
    order = None

    # 1) Primary lookup by metadata.order_id
    order_id = metadata.get("order_id")
    if order_id:
        order = Order.objects.filter(pk=order_id).first()
        if not order:
            logger.warning(f"[ORDER] No Order with ID {order_id} in metadata")

    # 2) Fallback lookup by stripe_session_id
    if order is None:
        session_id = session.get("id")
        order = Order.objects.filter(stripe_session_id=session_id).first()
        if not order:
            logger.error(f"[ORDER] No Order found for stripe_session_id={session_id!r}")
            return None

    # -- NEW: resolve customer email (guest-safe) --
    customer_email = None
    try:
        details = session.get("customer_details") or {}
        customer_email = details.get("email")
    except Exception:
        pass
    if not customer_email and order.user and getattr(order.user, "email", None):
        customer_email = order.user.email

    # 3) Mark paid (idempotent)
    if not order.is_paid:
        with transaction.atomic():
            order.is_paid = True
            order.stripe_payment_intent = session.get("payment_intent")
            order.save(update_fields=["is_paid", "stripe_payment_intent"])
        logger.info(
            "[ORDER] Marked Order #%s as paid (intent=%s)",
            order.id, order.stripe_payment_intent
        )

        # 4) Send confirmation email (do NOT block on failure)
        try:
            send_order_confirmation_email(order, to_email=customer_email)  # <-- pass email
        except Exception as e:
            logger.exception("[EMAIL] Failed to send confirmation for Order #%s: %s", order.id, e)
    else:
        logger.info("&#91;ORDER] Order #%s already marked paid, skipping", order.id)

    return order
