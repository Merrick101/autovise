# apps/users/tests/test_views.py

import pytest
from django.urls import reverse
from django.contrib.auth.models import User
from apps.products.models import Product, Bundle
from apps.products.models import Category, ProductType


@pytest.mark.django_db
def test_profile_view_get(client):
    user = User.objects.create_user(username="testuser", password="pass")
    client.login(username="testuser", password="pass")

    url = reverse("users:profile")
    response = client.get(url)
    assert response.status_code == 200
    assert "user_form" in response.context
    assert "profile_form" in response.context


@pytest.mark.django_db
def test_dashboard_view(client):
    user = User.objects.create_user(username="dashuser", password="pass")
    client.login(username="dashuser", password="pass")

    url = reverse("users:dashboard")
    response = client.get(url)
    assert response.status_code == 200
    assert "profile" in response.context


@pytest.mark.django_db
def test_save_product_toggle(client):
    user = User.objects.create_user(username="produser", password="pass")
    profile = user.profile

    category = Category.objects.create(name="Cat", slug="cat")
    ptype = ProductType.objects.create(name="Type")

    product = Product.objects.create(
        name="Test Product", variant="A", price=10, stock=5, tier="Standard",
        type=ptype, category=category, sku="SKU1", product_code="PC1"
    )
    client.login(username="produser", password="pass")

    url = reverse("users:save_product", args=[product.id])
    client.post(url, follow=True)
    assert product in profile.saved_products.all()

    # Toggle off
    client.post(url, follow=True)
    profile.refresh_from_db()
    assert product not in profile.saved_products.all()


@pytest.mark.django_db
def test_save_bundle_toggle(client):
    user = User.objects.create_user(username="bundleuser", password="pass")
    profile = user.profile

    bundle = Bundle.objects.create(name="Test Bundle", price=10, discount_percentage=10.0)
    client.login(username="bundleuser", password="pass")

    url = reverse("users:save_bundle", args=[bundle.id])
    client.post(url, follow=True)
    assert bundle in profile.saved_bundles.all()

    # Toggle off
    client.post(url, follow=True)
    profile.refresh_from_db()
    assert bundle not in profile.saved_bundles.all()


@pytest.mark.django_db
def test_delete_account(client):
    user = User.objects.create_user(username="deleteuser", password="pass")
    client.login(username="deleteuser", password="pass")

    url = reverse("users:delete_account")
    response = client.post(url)
    assert response.status_code == 302  # Redirect to login
    assert not User.objects.filter(username="deleteuser").exists()
