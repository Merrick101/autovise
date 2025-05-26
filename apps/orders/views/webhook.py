# apps/orders/views/webhook.py

import stripe
import json
import logging

from django.conf import settings
from django.http import HttpResponse, HttpResponseBadRequest
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

logger = logging.getLogger(__name__)


@require_POST
@csrf_exempt
def stripe_webhook_view(request):
    payload = request.body
    sig_header = request.META.get('HTTP_STRIPE_SIGNATURE')
    webhook_secret = settings.STRIPE_WEBHOOK_SECRET

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, webhook_secret
        )
    except ValueError as e:
        logger.error(f"Invalid payload: {e}")
        return HttpResponseBadRequest()
    except stripe.error.SignatureVerificationError as e:
        logger.error(f"Invalid signature: {e}")
        return HttpResponseBadRequest()

    # Handle the completed checkout
    if event['type'] == 'checkout.session.completed':
        session = event['data']['object']
        logger.info(f"Checkout completed: {session['id']}")

        # Placeholder: implement this function
        from apps.orders.utils.order import create_order_from_stripe_session
        create_order_from_stripe_session(session)

    return HttpResponse(status=200)
