"""
Additional functional tests for the pages app:
- Home context
- Contact form success and email-failure paths
Located at apps/pages/tests/test_contact_and_home.py
"""

import pytest
from django.urls import reverse
from apps.pages.models import ContactMessage


@pytest.mark.django_db
def test_home_includes_newsletter_form(client):
    resp = client.get(reverse("home"))
    assert resp.status_code == 200
    # the view injects NewsletterForm()
    assert "newsletter_form" in resp.context


@pytest.mark.django_db
def test_contact_post_creates_message_and_sends_email(client, monkeypatch):
    """Valid POST should save ContactMessage and attempt to send email (mocked)."""
    sent = {}

    def fake_send_mail(subject, message, from_email, recipient_list, **kwargs):
        # record the call; return 1 to simulate a successful send
        sent["args"] = (subject, message, from_email, tuple(recipient_list))
        return 1

    # Patch send_mail used *inside* the contact view
    monkeypatch.setattr("apps.pages.views.send_mail", fake_send_mail)

    data = {
        "name": "Alex Tester",
        "email": "alex@example.com",
        "subject": "Help with my order",
        "message": "Just testing the contact flow.",
    }
    resp = client.post(
        reverse("pages:contact"),
        data,
        follow=True,
        HTTP_X_FORWARDED_FOR="203.0.113.77",
        HTTP_USER_AGENT="pytest-UA",
    )
    assert resp.status_code == 200  # redirected back then rendered

    # DB row exists with captured metadata
    msg = ContactMessage.objects.get(email="alex@example.com")
    assert msg.subject.startswith("Help with my order")
    assert msg.ip_address == "203.0.113.77"
    assert "pytest-UA" in (msg.user_agent or "")

    # Email was "sent"
    assert "args" in sent
    assert "Help with my order" in sent["args"][0]  # subject


@pytest.mark.django_db
def test_contact_post_handles_email_error(client, monkeypatch):
    """If email send fails, page re-renders (200) and the message is still saved."""
    def boom(*args, **kwargs):
        raise Exception("smtp down")

    monkeypatch.setattr("apps.pages.views.send_mail", boom)

    data = {
        "name": "Casey",
        "email": "casey@example.com",
        "subject": "Question",
        "message": "Will this error path work?",
    }
    resp = client.post(reverse("pages:contact"), data, follow=True)
    # No redirect on failure — page renders with an error message
    assert resp.status_code == 200
    assert ContactMessage.objects.filter(email="casey@example.com").exists()
