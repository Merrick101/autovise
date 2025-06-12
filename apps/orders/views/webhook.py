# apps/orders/views/webhook.py

import logging
from django.http import HttpResponse, HttpResponseBadRequest
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from apps.orders.utils.stripe_helpers import verify_webhook_signature
from apps.orders.utils.order import create_order_from_stripe_session

logger = logging.getLogger(__name__)


@require_POST
@csrf_exempt
def stripe_webhook_view(request):
    logger.info("[WEBHOOK] Stripe webhook endpoint was hit.")
    print("[WEBHOOK] Endpoint triggered")

    if request.method != "POST":
        logger.warning("[WEBHOOK] Received non-POST request.")
        return HttpResponse(status=405)

    event = verify_webhook_signature(request)
    if event is None:
        return HttpResponseBadRequest("Invalid signature or payload")

    if event['type'] == 'checkout.session.completed':
        session = event['data']['object']
        logger.info(f"Webhook: checkout.session.completed | Session ID: {session['id']}")

        try:
            create_order_from_stripe_session(session)
        except Exception as e:
            logger.error(f"Order creation failed for session {session['id']}: {e}")
            return HttpResponse(status=500)

    return HttpResponse(status=200)
