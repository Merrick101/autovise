# apps/pages/tests/test_views.py

import pytest
from django.urls import reverse
from apps.pages.models import NewsletterSubscriber


@pytest.mark.django_db
def test_newsletter_model_str():
    subscriber = NewsletterSubscriber.objects.create(email="test@example.com")
    assert str(subscriber) == "test@example.com"


@pytest.mark.django_db
def test_home_view_renders_successfully(client):
    response = client.get(reverse("home"))  # From config/urls.py
    assert response.status_code == 200
    assert "featured_products" in response.context
    assert "featured_bundles" in response.context


@pytest.mark.django_db
def test_privacy_policy_view(client):
    response = client.get(reverse("pages:privacy"))
    assert response.status_code == 200
    assert "html" in response.content.decode().lower()


@pytest.mark.django_db
def test_terms_and_conditions_view(client):
    response = client.get(reverse("pages:terms"))
    assert response.status_code == 200
    assert "html" in response.content.decode().lower()


@pytest.mark.django_db
def test_contact_view(client):
    response = client.get(reverse("pages:contact"))
    assert response.status_code == 200


@pytest.mark.django_db
def test_subscribe_newsletter_success(client):
    email = "new@example.com"
    response = client.post(
        reverse("pages:newsletter_subscribe"),
        data={"email": email},
        follow=True
    )
    assert response.status_code == 200
    assert NewsletterSubscriber.objects.filter(email=email).exists()


@pytest.mark.django_db
def test_subscribe_newsletter_duplicate(client):
    email = "existing@example.com"
    NewsletterSubscriber.objects.create(email=email)

    response = client.post(
        reverse("pages:newsletter_subscribe"),
        data={"email": email},
        follow=True
    )
    assert response.status_code == 200
    assert NewsletterSubscriber.objects.filter(email=email).count() == 1


@pytest.mark.django_db
def test_subscribe_newsletter_invalid_method(client):
    response = client.get(reverse("pages:newsletter_subscribe"))
    assert response.status_code == 405  # Method Not Allowed
