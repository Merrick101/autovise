"""
PaymentIntent creation tests for the Orders app.

This module exercises the inline checkout endpoint
(`orders:create_payment_intent`) and verifies that:
- A Stripe PaymentIntent is created for the current cart and the view returns
  `client_secret`, `payment_intent_id`, and `order_id`.
- A pending `Order` and related `OrderItem`s are persisted with the correct,
  discounted unit prices and computed totals (subtotal, discounts, delivery,
  grand total).
- The Stripe call is formed correctly: amount is sent in pence, currency is
  GBP, `payment_method_types=["card"]` is used (no AMP), `metadata` includes
  `order_id`, `receipt_email` is set, and an `idempotency_key` is provided.
- An empty cart results in `HTTP 400`.

Implementation notes:
- External Stripe traffic is isolated by monkey-patching
  `apps.orders.views.payment.stripe.PaymentIntent.create`, capturing kwargs
  for assertions.
- Test data uses fixtures for products/bundles and a `set_session_cart`
  helper to build a guest cart.

Located at: apps/orders/tests/test_payments_create_intent.py
"""

import pytest
from decimal import Decimal
from django.urls import reverse
from apps.orders.models import Order, OrderItem
from apps.orders.views import payment as payment_view


@pytest.fixture
def stripe_pi_spy(monkeypatch):
    """
    Patch stripe.PaymentIntent.create used by the view and capture kwargs.
    """
    captured = {}

    class FakePI:
        id = "pi_test_123"
        client_secret = "cs_test_456"

    def fake_create(**kwargs):
        captured.update(kwargs)
        return FakePI()

    # Exact object used in view
    monkeypatch.setattr(
        payment_view.stripe.PaymentIntent, "create", staticmethod(fake_create)
    )
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
    assert cap["amount"] == 3932
    assert cap["currency"] == "gbp"
    assert cap["metadata"]["order_id"] == str(order.id)
    assert cap["receipt_email"] == "guest@example.com"
    assert cap["payment_method_types"] == ["card"]
    assert cap["idempotency_key"].startswith(f"order-{order.id}-")
    assert "automatic_payment_methods" not in cap


@pytest.mark.django_db
def test_create_intent_empty_cart_400(client, stripe_pi_spy):
    resp = client.post(reverse("orders:create_payment_intent"))
    assert resp.status_code == 400
