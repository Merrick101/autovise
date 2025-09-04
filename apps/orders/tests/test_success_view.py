# apps/orders/tests/test_success_view.py

import pytest
from decimal import Decimal
from django.urls import reverse

from apps.orders.models import Order


@pytest.fixture
def order_paid_pi(db):
    return Order.objects.create(
        user=None,
        total_amount=Decimal("10.00"),
        discount_total=Decimal("0.00"),
        delivery_fee=Decimal("0.00"),
        total_price=Decimal("10.00"),
        stripe_payment_intent="pi_success_1",
        is_paid=True,
    )


@pytest.fixture
def order_paid_session(db):
    return Order.objects.create(
        user=None,
        total_amount=Decimal("10.00"),
        discount_total=Decimal("0.00"),
        delivery_fee=Decimal("0.00"),
        total_price=Decimal("10.00"),
        stripe_session_id="cs_success_1",
        is_paid=True,
    )


@pytest.mark.django_db
def test_success_with_pi_param(client, order_paid_pi):
    url = reverse("orders:success") + "?pi=pi_success_1"
    resp = client.get(url)
    assert resp.status_code == 200
    assert b"Order" in resp.content or b"Thank" in resp.content  # basic smoke


@pytest.mark.django_db
def test_success_with_session_id_param(client, order_paid_session):
    url = reverse("orders:success") + "?session_id=cs_success_1"
    resp = client.get(url)
    assert resp.status_code == 200


@pytest.mark.django_db
def test_success_missing_params_redirects(client):
    resp = client.get(reverse("orders:success"))
    assert resp.status_code in (302, 301)
