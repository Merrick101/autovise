# apps/orders/tests/test_webhook.py

import json
import pytest
from decimal import Decimal
from django.urls import reverse

from apps.orders.models import Order


@pytest.fixture
def order_pending(db):
    return Order.objects.create(
        user=None,
        total_amount=Decimal("21.47"),
        discount_total=Decimal("2.15"),
        delivery_fee=Decimal("4.99"),
        total_price=Decimal("24.31"),
        stripe_payment_intent="pi_42",
        stripe_session_id="cs_42",
        is_paid=False,
    )


@pytest.fixture
def fake_verify(monkeypatch):
    """Monkeypatch verify_webhook_signature to return provided events."""
    def _set(event):
        from apps.orders import utils as utils_pkg
        from apps.orders.utils import stripe_helpers
        monkeypatch.setattr(stripe_helpers, "verify_webhook_signature", lambda request: event)
    return _set


@pytest.mark.django_db
def test_webhook_marks_paid_on_payment_intent_succeeded(client, order_pending, fake_verify):
    event = {
        "type": "payment_intent.succeeded",
        "data": {"object": {"object": "payment_intent", "id": "pi_42", "metadata": {"order_id": str(order_pending.id)}, "receipt_email": "guest@example.com"}},
    }
    fake_verify(event)
    resp = client.post(reverse("orders:webhook"), data=b"{}", content_type="application/json")
    assert resp.status_code == 200

    order_pending.refresh_from_db()
    assert order_pending.is_paid is True


@pytest.mark.django_db
def test_webhook_idempotent_on_replay(client, order_pending, fake_verify):
    event = {
        "type": "payment_intent.succeeded",
        "data": {"object": {"object": "payment_intent", "id": "pi_42", "metadata": {"order_id": str(order_pending.id)}}},
    }
    fake_verify(event)
    for _ in range(2):
        client.post(reverse("orders:webhook"), data=b"{}", content_type="application/json")

    order_pending.refresh_from_db()
    assert order_pending.is_paid is True  # no error on duplicate


@pytest.mark.django_db
def test_webhook_handles_checkout_session_completed(client, order_pending, fake_verify):
    event = {
        "type": "checkout.session.completed",
        "data": {"object": {"object": "checkout.session", "id": "cs_42", "payment_intent": "pi_42", "metadata": {"order_id": str(order_pending.id)}, "customer_details": {"email": "g@e.com"}}},
    }
    fake_verify(event)
    resp = client.post(reverse("orders:webhook"), data=b"{}", content_type="application/json")
    assert resp.status_code == 200
