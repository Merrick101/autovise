# apps/orders/tests/conftest.py

import pytest
from decimal import Decimal
from django.test import Client, RequestFactory
from django.contrib.sessions.backends.db import SessionStore


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
            subtotal_price=Decimal("21.47"),
            price=Decimal("19.32"),
            discount_percentage=Decimal("10.00"),
            bundle_type="Starter",
        )


@pytest.fixture
def set_session_cart(client):
    def _set(data: dict):
        session: SessionStore = client.session
        session["cart"] = data
        session.save()
    return _set


@pytest.fixture(autouse=True)
def no_real_emails(monkeypatch, request):
    # If a test or module sets @pytest.mark.allow_emails, don't patch
    if request.node.get_closest_marker("allow_emails"):
        return
    from apps.orders.utils import email as email_utils
    monkeypatch.setattr(email_utils, "send_order_confirmation_email", lambda *a, **k: None)
