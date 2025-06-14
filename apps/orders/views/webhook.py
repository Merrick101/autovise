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
    Endpoint to receive Stripe webhooks.
    Verifies signature, handles checkout.session.completed by updating the Order.
    """
    logger.info("[WEBHOOK] Stripe webhook endpoint was hit.")

    # 1) Verify signature & payload
    event = verify_webhook_signature(request)
    if event is None:
        logger.warning("[WEBHOOK] Invalid Stripe signature or payload.")
        return HttpResponseBadRequest("Invalid signature or payload")

    # 2) Handle the checkout.session.completed event
    if event.get("type") == "checkout.session.completed":
        session = event["data"]["object"]
        logger.info(f"[WEBHOOK] checkout.session.completed | session_id={session.get('id')}")

        try:
            update_order_from_stripe_session(session)
        except Exception as e:
            logger.error(f"[WEBHOOK] Failed updating order for session {session.get('id')}: {e}")
            return HttpResponse(status=500)

    # 3) Acknowledge receipt for all other events
    return HttpResponse(status=200)
