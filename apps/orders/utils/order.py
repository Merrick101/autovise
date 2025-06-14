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
    Expects `order_id` in session.metadata.
    """
    metadata = getattr(session, "metadata", {})
    order_id = metadata.get("order_id")
    if not order_id:
        logger.error("[ORDER] No order_id in Stripe session metadata")
        return None

    try:
        order = Order.objects.get(pk=order_id)
    except Order.DoesNotExist:
        logger.error(f"[ORDER] Order {order_id} not found in DB")
        return None

    # If not already paid, mark and email
    if not order.is_paid:
        order.is_paid = True
        order.stripe_payment_intent = session.get("payment_intent")
        order.save(update_fields=["is_paid", "stripe_payment_intent"])
        logger.info(f"[ORDER] Marked Order #{order.id} as paid")

        # Send confirmation email if user is present
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
