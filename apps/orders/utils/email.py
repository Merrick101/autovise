# apps/orders/utils/email.py

import logging
from django.conf import settings
from django.core import mail
from django.template.loader import render_to_string

logger = logging.getLogger(__name__)


def send_order_confirmation_email(order, to_email=None):
    """
    Send order confirmation to the customer (if an email is provided) and an admin copy.
    Honors SEND_ORDER_CONFIRMATION_EMAIL. Failures are logged, not raised.
    """
    if not getattr(settings, "SEND_ORDER_CONFIRMATION_EMAIL", True):
        logger.info("[EMAIL] Confirmation emails disabled. Skipping Order #%s", order.id)
        return

    # Resolve recipients
    customer_email = to_email or (order.user.email if getattr(order.user, "email", None) else None)
    admin_email = getattr(settings, "ORDERS_NOTIFICATION_EMAIL", None) or getattr(settings, "DEFAULT_FROM_EMAIL", None)

    subject = f"Your Autovise Order #{order.id} Confirmation"
    context = {"user": getattr(order, "user", None), "order": order}
    text_body = render_to_string("emails/order_confirmation.txt", context)
    html_body = render_to_string("emails/order_confirmation.html", context)

    # Send to customer (if address is provided)
    if customer_email:
        try:
            mail.send_mail(
                subject=subject,
                message=text_body,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[customer_email],
                html_message=html_body,
                fail_silently=False,
            )
            logger.info("[EMAIL] Sent confirmation email to %s for Order #%s", customer_email, order.id)
        except Exception as e:
            logger.exception("[EMAIL] Customer email failed for Order #%s: %s", order.id, e)
    else:
        logger.warning("[EMAIL] No customer email for Order #%s; skipping customer send", order.id)

    # Send admin copy
    if admin_email:
        try:
            mail.send_mail(
                subject=f"[Admin Copy] {subject}",
                message=text_body,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[admin_email],
                html_message=html_body,
                fail_silently=False,
            )
            logger.info("[EMAIL] Sent admin copy to %s for Order #%s", admin_email, order.id)
        except Exception as e:
            logger.exception("[EMAIL] Admin copy failed for Order #%s: %s", order.id, e)
