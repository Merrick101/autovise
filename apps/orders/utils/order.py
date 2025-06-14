# apps/orders/utils/order.py

import logging

from django.conf import settings
from django.core.mail import send_mail
from django.template.loader import render_to_string
from apps.orders.models import Order

logger = logging.getLogger(__name__)


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

    # 3) Mark paid and send email if not already done
    if not order.is_paid:
        order.is_paid = True
        order.stripe_payment_intent = session.get("payment_intent")
        order.save(update_fields=["is_paid", "stripe_payment_intent"])
        logger.info(f"[ORDER] Marked Order #{order.id} as paid")

        if order.user and order.user.email:
            subject = f"Your Autovise Order #{order.id} Confirmation"
            context = {"user": order.user, "order": order}
            text_body = render_to_string("emails/order_confirmation.txt", context)
            html_body = render_to_string("emails/order_confirmation.html", context)
            try:
                send_mail(
                    subject=subject,
                    message=text_body,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[order.user.email],
                    html_message=html_body,
                    fail_silently=False,
                )
                logger.info(f"[EMAIL] Confirmation sent for Order #{order.id}")
            except Exception as e:
                logger.error(f"[EMAIL] Failed to send confirmation for Order #{order.id}: {e}")
    else:
        logger.info(f"[ORDER] Order #{order.id} already marked paid, skipping")

    return order
