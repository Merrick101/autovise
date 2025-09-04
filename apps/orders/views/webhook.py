# apps/orders/views/webhook.py

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

    try:
        # 2) Handle success events
        if event_type == "payment_intent.succeeded":
            # Inline checkout path
            logger.info("[WEBHOOK] payment_intent.succeeded | pi=%s", obj.get("id"))
            update_order_from_stripe_session(obj)  # expects PaymentIntent-like dict

        elif event_type == "checkout.session.completed":
            # Hosted checkout path
            logger.info("[WEBHOOK] checkout.session.completed | session_id=%s", obj.get("id"))
            update_order_from_stripe_session(obj)  # expects Session-like dict

        # 3) Optional: log other notable events
        elif event_type == "payment_intent.payment_failed":
            logger.warning("[WEBHOOK] payment_intent.payment_failed | pi=%s reason=%s",
                           obj.get("id"), (obj.get("last_payment_error") or {}).get("message"))

        else:
            logger.debug("[WEBHOOK] Unhandled event type: %s", event_type)

    except Exception as e:
        # Return 500 so Stripe retries
        logger.exception("[WEBHOOK] Error processing %s: %s", event_type, e)
        return HttpResponse(status=500)

    # 4) Acknowledge
    return HttpResponse(status=200)
