# apps/orders/utils/stripe_helpers.py

import stripe
import logging
from django.conf import settings

logger = logging.getLogger(__name__)

# 1) Set API key and lock in a consistent API version
stripe.api_key = settings.STRIPE_SECRET_KEY
stripe.api_version = getattr(settings, "STRIPE_API_VERSION", "2024-06-20")


def create_checkout_session(
    user,
    line_items,
    metadata=None,
    success_url=None,
    cancel_url=None,
    customer_email=None,
    allow_promotion_codes=False,
):
    """
    Create a Stripe Checkout Session.
    - Sends customer_email when provided (guest-friendly).
    - Ensures a customer is created (so webhook has customer_details.email).
    - Uses idempotency_key to guard against double submits.
    """
    try:
        # Build params for the Session
        params = {
            "mode": "payment",
            "line_items": line_items,
            "metadata": metadata or {},
            "success_url": success_url or settings.DEFAULT_SUCCESS_URL,
            "cancel_url": cancel_url or settings.DEFAULT_CANCEL_URL,
            # ensure the completed session includes customer_details.email
            "customer_creation": "always",
            # if provided, prefill email and skip Stripe email step
            "customer_email": customer_email or None,
            # optional polish
            "allow_promotion_codes": allow_promotion_codes or None,
        }
        # Remove Nones
        params = {k: v for k, v in params.items() if v is not None}

        # Idempotency: prevents double-charges if user double-clicks
        # (Note: idempotency_key is a request option, not a param)
        user_key = getattr(user, "id", None) or "guest"
        order_key = (metadata or {}).get("order_id", "")
        idempotency_key = f"checkout_{user_key}_{order_key}" if order_key else f"checkout_{user_key}"

        session = stripe.checkout.Session.create(
            **params,
            idempotency_key=idempotency_key,
        )
        return session

    except stripe.error.StripeError as e:
        logger.error(f"[STRIPE] Checkout session creation failed: {getattr(e, 'user_message', None) or e}")
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
