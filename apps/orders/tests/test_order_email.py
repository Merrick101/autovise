# apps/orders/tests/test_order_email.py

import pytest
from decimal import Decimal
from django.core import mail
from django.contrib.auth import get_user_model

from apps.orders.models import Order
from apps.orders.utils.order import update_order_from_stripe_session


@pytest.fixture(autouse=True)
def email_settings(settings):
    """
    Use in-memory email backend for assertions.
    Provide sane defaults for from/admin addresses.
    """
    settings.EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"
    settings.DEFAULT_FROM_EMAIL = "no-reply@test.com"
    settings.ORDERS_NOTIFICATION_EMAIL = "admin@test.com"
    settings.SEND_ORDER_CONFIRMATION_EMAIL = True
    yield


def _new_order(**overrides):
    defaults = dict(
        user=None,
        total_amount=Decimal("21.47"),
        discount_total=Decimal("2.15"),
        delivery_fee=Decimal("4.99"),
        total_price=Decimal("24.31"),
        stripe_session_id="cs_test_123",
        is_paid=False,
    )
    defaults.update(overrides)
    return Order.objects.create(**defaults)


def _session_for(order, **overrides):
    base = {
        "object": "checkout.session",
        "id": order.stripe_session_id,
        "payment_intent": "pi_test_123",
        "customer_details": {"email": "guest@example.com"},
        "metadata": {"order_id": str(order.id)},
    }
    base.update(overrides)
    return base


@pytest.mark.django_db
def test_confirmation_email_sent_to_guest_and_admin():
    order = _new_order()
    # Includes guest@example.com in customer_details
    session = _session_for(order)

    update_order_from_stripe_session(session)
    order.refresh_from_db()

    assert order.is_paid is True
    # Expect at least customer + admin messages in outbox
    recipients = {rcpt for m in mail.outbox for rcpt in (m.to or [])}
    assert "guest@example.com" in recipients
    assert "admin@test.com" in recipients


@pytest.mark.django_db
def test_admin_email_sent_when_no_customer_email_available():
    order = _new_order()
    # No email from Stripe
    session = _session_for(order, customer_details=None)

    update_order_from_stripe_session(session)
    order.refresh_from_db()

    assert order.is_paid is True
    # Only admin should receive an email
    recipients = [rcpt for m in mail.outbox for rcpt in (m.to or [])]
    assert "admin@test.com" in recipients
    assert all(rcpt != "guest@example.com" for rcpt in recipients)


@pytest.mark.django_db
def test_authenticated_user_email_used_if_stripe_email_missing():
    User = get_user_model()
    user = User.objects.create_user(
      username="alice", email="alice@test.com", password="x"
    )
    order = _new_order(user=user)
    session = _session_for(order, customer_details=None)

    update_order_from_stripe_session(session)
    order.refresh_from_db()

    assert order.is_paid is True
    recipients = {rcpt for m in mail.outbox for rcpt in (m.to or [])}
    assert "alice@test.com" in recipients  # used from the user account
    assert "admin@test.com" in recipients


@pytest.mark.django_db
def test_email_failures_do_not_block_order(monkeypatch):
    order = _new_order()
    session = _session_for(order)  # has guest email

    # Make send_mail raise for any call
    from django.core import mail as mail_mod

    def boom(*args, **kwargs):
        raise RuntimeError("smtp down")
    monkeypatch.setattr(mail_mod, "send_mail", boom, raising=True)

    # Should not raise; order still marked paid; outbox remains empty
    update_order_from_stripe_session(session)
    order.refresh_from_db()

    assert order.is_paid is True
    assert len(mail.outbox) == 0


@pytest.mark.django_db
def test_idempotent_no_duplicate_emails_when_already_paid():
    order = _new_order(is_paid=True)  # Already paid
    session = _session_for(order)

    update_order_from_stripe_session(session)

    # Since order was already paid, email should not be sent again
    assert len(mail.outbox) == 0
