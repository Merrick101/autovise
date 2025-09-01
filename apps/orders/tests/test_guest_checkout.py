# apps/orders/tests/test_guest_checkout.py

import types
from decimal import Decimal

import pytest
from django.urls import reverse
from django.test import Client, RequestFactory
from django.contrib.sessions.backends.db import SessionStore

from apps.orders.models import Order, OrderItem
from apps.orders.utils.cart import calculate_cart_summary


@pytest.fixture
def rf():
    return RequestFactory()


@pytest.fixture
def client():
    return Client()


@pytest.fixture
def product(django_db_blocker):
    from apps.products.models import Product, ProductType, Category
    with django_db_blocker.unblock():
        cat = Category.objects.create(name="Gadgets", slug="gadgets")
        ptype = ProductType.objects.create(name="Standard")
        return Product.objects.create(
            name="Widget",
            variant="Base",
            description="Test widget",
            type=ptype,
            tier="Standard",
            category=cat,
            price=Decimal("10.00"),
            stock=100,
            sku="SKU-WID-001",
            product_code="WID-001",
            image_type="jpg",
        )


@pytest.fixture
def bundle(django_db_blocker):
    from apps.products.models import Bundle
    with django_db_blocker.unblock():
        return Bundle.objects.create(
            name="Starter Kit",
            subtotal_price=Decimal("21.47"),        # pre-discount base
            price=Decimal("19.32"),                 # after 10% discount
            discount_percentage=Decimal("10.00"),
            bundle_type="Starter",
        )


@pytest.fixture(autouse=True)
def mock_stripe_and_email(monkeypatch):
    """
    - Mock Stripe checkout session creation to avoid network calls.
    - Mock order confirmation email to a no-op.
    """
    from apps.orders.utils import stripe_helpers
    fake_session = types.SimpleNamespace(id="cs_test_123", url="https://stripe.test/session/cs_test_123")
    monkeypatch.setattr(stripe_helpers, "create_checkout_session", lambda **kwargs: fake_session)

    from apps.orders.utils import email as email_utils
    monkeypatch.setattr(email_utils, "send_order_confirmation_email", lambda order: None)


def _set_session_cart(client: Client, data: dict):
    """Helper: set the session cart for an anonymous client."""
    session: SessionStore = client.session
    session["cart"] = data
    session.save()


@pytest.mark.django_db
def test_guest_checkout_with_bundle_only(client, bundle, rf):
    """
    Guest adds a bundle to cart, goes to checkout:
    - Summary math is correct (10% bundle discount applied once)
    - Order + OrderItems persist discounted unit prices
    - Redirect to Stripe occurs
    """
    # Arrange: session cart with ONE bundle, quantity 1
    # Simulate UI storing discounted price (10% off of 21.47 = 19.32)
    session_cart = {
        f"bundle_{bundle.id}": {
            "type": "bundle",
            "name": bundle.name,
            "price": "19.32",  # discounted unit saved in session
            "quantity": 1,
        }
    }
    _set_session_cart(client, session_cart)

    # Summary check
    req = rf.get("/cart/")
    req.user = types.SimpleNamespace(is_authenticated=False)
    summary = calculate_cart_summary(req, session_cart, "session")

    # Assert (summary math):
    # pre-discount subtotal = 21.47
    # bundle discount = 2.15
    # total after discount = 19.32
    # delivery = 4.99 (since pre-discount < 40 and not first-time logged-in)
    # grand total = 24.31
    assert summary["total_before_discount"].quantize(Decimal("0.01")) == Decimal("21.47")
    assert summary["bundle_discount"].quantize(Decimal("0.01")) == Decimal("2.15")
    assert summary["cart_total"].quantize(Decimal("0.01")) == Decimal("19.32")
    assert summary["delivery_fee"].quantize(Decimal("0.01")) == Decimal("4.99")
    assert summary["grand_total"].quantize(Decimal("0.01")) == Decimal("24.31")

    # Act: POST to checkout (guest)
    resp = client.post(reverse("orders:checkout"))

    # Assert: redirected to Stripe session URL
    assert resp.status_code in (302, 303)
    assert "stripe.test/session" in resp["Location"]

    # Assert: Order persisted with correct figures
    order = Order.objects.last()
    assert order is not None
    assert order.user is None  # guest
    assert order.total_amount.quantize(Decimal("0.01")) == Decimal("21.47")
    assert order.discount_total.quantize(Decimal("0.01")) == Decimal("2.15")
    assert order.delivery_fee.quantize(Decimal("0.01")) == Decimal("4.99")
    assert order.total_price.quantize(Decimal("0.01")) == Decimal("24.31")

    # Assert: OrderItems reflect discounted unit price (19.32)
    items = list(OrderItem.objects.filter(order=order))
    assert len(items) == 1
    oi = items[0]
    assert oi.bundle_id == bundle.id
    assert oi.product_id is None
    assert oi.quantity == 1
    assert oi.unit_price.quantize(Decimal("0.01")) == Decimal("19.32")


@pytest.mark.django_db
def test_guest_checkout_mixed_bundle_and_product(client, bundle, product, rf):
    """
    Guest cart with a bundle (qty 1) and a product (qty 2).
    - Bundle has 10% off; product is full price unless you store a session price.
    - Totals & persisted values should align with summary.
    """
    session_cart = {
        f"bundle_{bundle.id}": {
            "type": "bundle",
            "name": bundle.name,
            "price": "19.32",  # 10% off 21.47
            "quantity": 1,
        },
        product.product_code: {
            "product_id": product.id,
            "name": product.name,
            "quantity": 2,
            "price": "10.00",
            "image_type": product.image_type,
        },
    }
    _set_session_cart(client, session_cart)

    # Summary check
    req = rf.get("/cart/")
    req.user = types.SimpleNamespace(is_authenticated=False)
    summary = calculate_cart_summary(req, session_cart, "session")

    # Pre-discount subtotal: 21.47 (bundle base) + 2*10.00 (product) = 41.47
    # Bundle discount: 2.15
    # After discount items: 19.32 + 20.00 = 39.32
    # Pre-discount >= 40 → free delivery
    # Grand total = 39.32
    assert summary["total_before_discount"].quantize(Decimal("0.01")) == Decimal("41.47")
    assert summary["bundle_discount"].quantize(Decimal("0.01")) == Decimal("2.15")
    assert summary["cart_total"].quantize(Decimal("0.01")) == Decimal("39.32")
    assert summary["delivery_fee"].quantize(Decimal("0.01")) == Decimal("0.00")
    assert summary["grand_total"].quantize(Decimal("0.01")) == Decimal("39.32")

    # Checkout
    resp = client.post(reverse("orders:checkout"))
    assert resp.status_code in (302, 303)

    order = Order.objects.last()
    assert order is not None
    assert order.user is None
    assert order.total_amount.quantize(Decimal("0.01")) == Decimal("41.47")
    assert order.discount_total.quantize(Decimal("0.01")) == Decimal("2.15")
    assert order.delivery_fee.quantize(Decimal("0.01")) == Decimal("0.00")
    assert order.total_price.quantize(Decimal("0.01")) == Decimal("39.32")

    items = list(OrderItem.objects.filter(order=order).order_by("id"))
    assert len(items) == 2

    # One bundle line @ 19.32, one product line @ 10.00 with qty 2
    bundle_item = next(i for i in items if i.bundle_id is not None)
    product_item = next(i for i in items if i.product_id is not None)

    assert bundle_item.quantity == 1
    assert bundle_item.unit_price.quantize(Decimal("0.01")) == Decimal("19.32")

    assert product_item.quantity == 2
    assert product_item.unit_price.quantize(Decimal("0.01")) == Decimal("10.00")
