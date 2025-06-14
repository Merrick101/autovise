# apps/orders/utils/stripe_helpers.py

import stripe
import logging
from django.conf import settings

logger = logging.getLogger(__name__)

# 1) Set API key and lock in a consistent API version
stripe.api_key = settings.STRIPE_SECRET_KEY
stripe.api_version = getattr(settings, "STRIPE_API_VERSION", None)


def create_checkout_session(user, line_items, metadata=None, success_url=None, cancel_url=None):
    """
    Create a Stripe Checkout Session.
    """
    try:
        # 2) Use idempotency_key in metadata or kwargs to guard against double-clicks
        return stripe.checkout.Session.create(
            payment_method_types=['card'],
            mode='payment',
            line_items=line_items,
            success_url=success_url or settings.DEFAULT_SUCCESS_URL,
            cancel_url=cancel_url or settings.DEFAULT_CANCEL_URL,
            metadata=metadata or {},
            # idempotency_key=f"checkout_{user.id}_{timestamp}"  # optional
        )
    except stripe.error.StripeError as e:
        logger.error(f"[STRIPE] Checkout session creation failed: {e.user_message or e}")
        return None
    except Exception as e:
        logger.exception(f"[STRIPE] Unexpected error creating checkout session: {e}")
        return None


def retrieve_checkout_session(session_id, expand_line_items=False):
    """
    Retrieve an existing Stripe Checkout Session by ID.
    Pass expand_line_items=True to include line_items in the response.
    """
    try:
        params = {}
        if expand_line_items:
            params["expand"] = ["line_items"]
        return stripe.checkout.Session.retrieve(session_id, **params)
    except stripe.error.InvalidRequestError as e:
        logger.warning(f"[STRIPE] Invalid session ID {session_id}: {e.user_message or e}")
    except stripe.error.StripeError as e:
        logger.error(f"[STRIPE] Error retrieving checkout session: {e.user_message or e}")
    except Exception as e:
        logger.exception(f"[STRIPE] Unexpected error retrieving session: {e}")
    return None


def verify_webhook_signature(request):
    """
    Verify incoming Stripe webhook request.
    Returns the event object if valid, or None if verification fails.
    """
    payload = request.body
    sig_header = request.META.get('HTTP_STRIPE_SIGNATURE', '')

    if not sig_header:
        logger.warning("[STRIPE] Missing Stripe signature header")
        return None

    try:
        return stripe.Webhook.construct_event(
            payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
        )
    except stripe.error.SignatureVerificationError as e:
        logger.warning(f"[STRIPE] Webhook signature verification failed: {e}")
    except ValueError as e:
        logger.warning(f"[STRIPE] Invalid payload: {e}")
    except Exception as e:
        logger.exception(f"[STRIPE] Unexpected webhook verification error: {e}")
    return None
