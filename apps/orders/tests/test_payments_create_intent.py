# apps/orders/tests/test_payments_create_intent.py

import json
from decimal import Decimal
import pytest
from django.urls import reverse

from apps.orders.models import Order, OrderItem


@pytest.fixture
def stripe_pi_spy(monkeypatch):
    captured = {}

    class PI:
        id = "pi_test_123"
        client_secret = "cs_test_456"

    class FakePI:
        @staticmethod
        def create(amount, currency, metadata=None, receipt_email=None, automatic_payment_methods=None, idempotency_key=None):
            captured.update(dict(amount=amount, currency=currency, metadata=metadata,
                                 receipt_email=receipt_email, automatic_payment_methods=automatic_payment_methods,
                                 idempotency_key=idempotency_key))
            return PI()
    import sys
    fake = type("S", (), {"PaymentIntent": FakePI})
    monkeypatch.setitem(sys.modules, "stripe", fake)
    return captured


@pytest.mark.django_db
def test_create_intent_guest_success(client, bundle, product, set_session_cart, stripe_pi_spy):
    # Cart: 1 bundle @ 19.32, 2x product @ 10.00 => pre=41.47, discount=2.15, grand=39.32 (free delivery)
    set_session_cart({
        f"bundle_{bundle.id}": {"type": "bundle", "name": bundle.name, "price": "19.32", "quantity": 1},
        product.product_code: {"product_id": product.id, "name": product.name, "quantity": 2, "price": "10.00", "image_type": product.image_type},
    })

    resp = client.post(reverse("orders:create_payment_intent"), data={"guest_email": "guest@example.com"})
    assert resp.status_code == 200

    data = resp.json()
    assert set(data.keys()) == {"client_secret", "payment_intent_id", "order_id"}
    assert data["client_secret"] == "cs_test_456"
    assert data["payment_intent_id"] == "pi_test_123"
    order = Order.objects.get(id=data["order_id"])

    # Order persisted
    assert order.user is None
    assert order.total_amount.quantize(Decimal("0.01")) == Decimal("41.47")
    assert order.discount_total.quantize(Decimal("0.01")) == Decimal("2.15")
    assert order.delivery_fee.quantize(Decimal("0.01")) == Decimal("0.00")
    assert order.total_price.quantize(Decimal("0.01")) == Decimal("39.32")
    assert order.stripe_payment_intent == "pi_test_123"

    # Items persisted
    items = list(OrderItem.objects.filter(order=order))
    assert len(items) == 2

    # Stripe call inspection
    cap = stripe_pi_spy
    assert cap["amount"] == 3932  # pence
    assert cap["currency"] == "gbp"
    assert cap["metadata"]["order_id"] == str(order.id)
    assert cap["receipt_email"] == "guest@example.com"
    assert cap["automatic_payment_methods"] == {"enabled": True}
    assert cap["idempotency_key"].startswith("pi_")


@pytest.mark.django_db
def test_create_intent_empty_cart_400(client, stripe_pi_spy):
    resp = client.post(reverse("orders:create_payment_intent"))
    assert resp.status_code == 400
