# apps/orders/utils/stripe_helpers.py

import stripe
import logging
from django.conf import settings

logger = logging.getLogger(__name__)

# Load Stripe secret key
stripe.api_key = settings.STRIPE_SECRET_KEY


def create_checkout_session(user, line_items, metadata=None, success_url=None, cancel_url=None):
    """
    Create a Stripe Checkout Session.
    """
    try:
        session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            mode='payment',
            line_items=line_items,
            success_url=success_url or settings.DEFAULT_SUCCESS_URL,
            cancel_url=cancel_url or settings.DEFAULT_CANCEL_URL,
            metadata=metadata or {},
        )
        return session
    except Exception as e:
        logger.error(f"[STRIPE] Failed to create checkout session: {e}")
        return None


def retrieve_checkout_session(session_id):
    """
    Retrieve an existing Stripe Checkout Session by ID.
    """
    try:
        return stripe.checkout.Session.retrieve(session_id)
    except Exception as e:
        logger.error(f"[STRIPE] Failed to retrieve checkout session: {e}")
        return None


def verify_webhook_signature(request):
    """
    Verify incoming Stripe webhook request.
    Returns the event object if valid, or None if verification fails.
    """
    payload = request.body
    sig_header = request.META.get('HTTP_STRIPE_SIGNATURE')
    secret = settings.STRIPE_WEBHOOK_SECRET

    try:
        event = stripe.Webhook.construct_event(payload, sig_header, secret)
        return event
    except stripe.error.SignatureVerificationError as e:
        logger.warning(f"[STRIPE] Webhook signature verification failed: {e}")
    except Exception as e:
        logger.error(f"[STRIPE] Unexpected error in webhook verification: {e}")
    return None
