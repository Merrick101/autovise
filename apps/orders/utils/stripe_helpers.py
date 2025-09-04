# apps/orders/utils/stripe_helpers.py

import logging
from decimal import Decimal
from typing import Dict, Optional

import stripe
from django.conf import settings

logger = logging.getLogger(__name__)

# 1) Configure Stripe once
stripe.api_key = settings.STRIPE_SECRET_KEY
stripe.api_version = getattr(settings, "STRIPE_API_VERSION", "2024-06-20")
# Optional: retry transient network errors automatically
# stripe.max_network_retries = 2


# ---------- Shared Helpers ----------

def to_pence(amount_gbp: Decimal) -> int:
    """Robust Decimal(£) → int(pence)."""
    return int((amount_gbp * Decimal("100")).quantize(Decimal("1")))


def make_idempotency_key(prefix: str, *, user_id=None, order_id=None, suffix: str = "") -> str:
    """
    Consistent idempotency key scheme for both Sessions and PaymentIntents.
    """
    parts = [prefix, str(user_id or "guest")]
    if order_id:
        parts.append(str(order_id))
    if suffix:
        parts.append(suffix)
    return "_".join(parts)


# ---------- Payment Element (Inline) ----------

def create_payment_intent(
    *,
    amount_gbp: Decimal,
    currency: str = "gbp",
    metadata: Optional[Dict[str, str]] = None,
    receipt_email: Optional[str] = None,
    idempotency_key: Optional[str] = None,
    enable_automatic_payment_methods: bool = True,
):
    """
    Create a Stripe PaymentIntent for the Payment Element flow.
    Returns the PI object or None on error.
    """
    try:
        params = {
            "amount": to_pence(amount_gbp),
            "currency": currency,
            "metadata": metadata or {},
            "receipt_email": receipt_email,
            "automatic_payment_methods": {"enabled": enable_automatic_payment_methods},
        }
        # Remove Nones
        params = {k: v for k, v in params.items() if v is not None}

        pi = stripe.PaymentIntent.create(**params, idempotency_key=idempotency_key)
        logger.info(
            "[STRIPE] PaymentIntent created",
            extra={"pi_id": pi.id, "amount": params["amount"], "currency": currency, "metadata": params.get("metadata")},
        )
        return pi
    except stripe.error.StripeError as e:
        logger.error(f"[STRIPE] PI creation failed: {getattr(e, 'user_message', None) or e}")
    except Exception as e:
        logger.exception(f"[STRIPE] Unexpected error creating PI: {e}")
    return None


# ---------- Hosted Checkout ----------

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
    Create a Stripe Checkout Session (hosted).
    Returns the Session or None on error.
    """
    try:
        params = {
            "mode": "payment",
            "line_items": line_items,
            "metadata": metadata or {},
            "success_url": success_url or settings.DEFAULT_SUCCESS_URL,
            "cancel_url": cancel_url or settings.DEFAULT_CANCEL_URL,
            "customer_creation": "always",
            "customer_email": customer_email or None,
            "allow_promotion_codes": allow_promotion_codes or None,
        }
        params = {k: v for k, v in params.items() if v is not None}

        idempotency_key = make_idempotency_key(
            "checkout",
            user_id=getattr(user, "id", None),
            order_id=(metadata or {}).get("order_id"),
        )

        session = stripe.checkout.Session.create(**params, idempotency_key=idempotency_key)
        logger.info("[STRIPE] Checkout Session created", extra={"cs_id": session.id, "metadata": params.get("metadata")})
        return session

    except stripe.error.StripeError as e:
        logger.error(f"[STRIPE] Checkout session creation failed: {getattr(e, 'user_message', None) or e}")
    except Exception as e:
        logger.exception(f"[STRIPE] Unexpected error creating checkout session: {e}")
    return None


def retrieve_checkout_session(session_id, expand_line_items=False):
    """
    Retrieve a Stripe Checkout Session by ID.
    """
    try:
        params = {"expand": ["line_items"]} if expand_line_items else {}
        return stripe.checkout.Session.retrieve(session_id, **params)
    except stripe.error.InvalidRequestError as e:
        logger.warning(f"[STRIPE] Invalid session ID {session_id}: {e.user_message or e}")
    except stripe.error.StripeError as e:
        logger.error(f"[STRIPE] Error retrieving checkout session: {e.user_message or e}")
    except Exception as e:
        logger.exception(f"[STRIPE] Unexpected error retrieving session: {e}")
    return None


# ---------- Webhook Verification ----------

def verify_webhook_signature(request):
    """
    Verify incoming Stripe webhook request.
    Returns the event dict if valid, or None if verification fails.
    """
    payload = request.body.decode("utf-8", errors="replace")
    sig_header = request.META.get("HTTP_STRIPE_SIGNATURE", "")

    if not sig_header:
        logger.warning("[STRIPE] Missing Stripe signature header")
        return None

    try:
        return stripe.Webhook.construct_event(payload, sig_header, settings.STRIPE_WEBHOOK_SECRET)
    except stripe.error.SignatureVerificationError as e:
        logger.warning(f"[STRIPE] Webhook signature verification failed: {e}")
    except ValueError as e:
        logger.warning(f"[STRIPE] Invalid payload: {e}")
    except Exception as e:
        logger.exception(f"[STRIPE] Unexpected webhook verification error: {e}")
    return None
