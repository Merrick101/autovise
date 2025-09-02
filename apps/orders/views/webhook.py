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
    logger.info("[WEBHOOK] Stripe webhook endpoint was hit.")
    event = verify_webhook_signature(request)
    if event is None:
        logger.warning("[WEBHOOK] Invalid Stripe signature or payload.")
        return HttpResponseBadRequest("Invalid signature or payload")

    if event.get("type") == "checkout.session.completed":
        session = event["data"]["object"]
        logger.info("[WEBHOOK] checkout.session.completed | session_id=%s", session.get("id"))
        # Any exceptions are handled inside update_order_from_stripe_session
        update_order_from_stripe_session(session)

    return HttpResponse(status=200)
