# apps/orders/utils/email.py

import logging
from django.conf import settings
from django.core.mail import send_mail
from django.template.loader import render_to_string

logger = logging.getLogger(__name__)


def send_order_confirmation_email(order):
    """
    Sends an order confirmation email if enabled in settings.
    """
    # Feature flag to turn emails on/off
    if not getattr(settings, "SEND_ORDER_CONFIRMATION_EMAIL", True):
        logger.info(f"[EMAIL] Confirmation emails are disabled. Skipping Order #{order.id}")
        return

    if not (order.user and order.user.email):
        logger.warning(f"[EMAIL] No user/email for Order #{order.id}. Skipping.")
        return

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
        logger.info(f"[EMAIL] Sent confirmation email for Order #{order.id}")
    except Exception as e:
        logger.error(f"[EMAIL] Failed to send confirmation for Order #{order.id}: {e}")
