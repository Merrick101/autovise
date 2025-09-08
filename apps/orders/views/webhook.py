"""
Views for handling Stripe webhooks.
Located at apps/orders/views/webhook.py
"""

import logging

from django.http import HttpResponse, HttpResponseBadRequest
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from apps.orders.utils.stripe_helpers import verify_webhook_signature
from apps.orders.utils.order import update_order_from_stripe_session

logger = logging.getLogger(__name__)


@require_POST
@csrf_exempt
def stripe_webhook_view(request):
    """
    Stripe webhook endpoint.
    Handles both hosted Checkout and inline Payment Element flows.
    """
    logger.info("[WEBHOOK] Stripe webhook endpoint hit")

    # 1) Verify signature & parse event
    event = verify_webhook_signature(request)
    if event is None:
        logger.warning("[WEBHOOK] Invalid Stripe signature or payload")
        return HttpResponseBadRequest("Invalid signature or payload")

    event_type = event.get("type")
    obj = (event.get("data") or {}).get("object") or {}

    # Event types that should update Order state in the DB
    HANDLED_TYPES = {
        # Payment Element / PI lifecycle
        "payment_intent.succeeded",
        "payment_intent.canceled",
        "payment_intent.payment_failed",
        "payment_intent.processing",

        # Hosted checkout lifecycle
        "checkout.session.completed",
        "checkout.session.async_payment_succeeded",
        "checkout.session.async_payment_failed",
        "checkout.session.expired",
    }

    try:
        if event_type in HANDLED_TYPES:
            order = update_order_from_stripe_session(obj)
            if order:
                logger.info(
                    "[WEBHOOK] %s -> Order #%s payment_status=%s",
                    event_type, order.id, order.payment_status
                )
            else:
                logger.warning(
                    "[WEBHOOK] %s did not match any Order", event_type
                )

        else:
            # Ignore duplicative events like charge.* or payment_intent.created
            logger.debug("[WEBHOOK] Ignoring event type: %s", event_type)

    except Exception as e:
        # Return 500 so Stripe retries
        logger.exception("[WEBHOOK] Error processing %s: %s", event_type, e)
        return HttpResponse(status=500)

    # 4) Acknowledge
    return HttpResponse(status=200)
