"""
Additional functional tests for the users app:
- Auth redirects for profile/dashboard
- Dashboard context has saved items + order_count
- Save product/bundle requires login
- Delete account removes the user
Located at apps/users/tests/test_dashboard_and_profile.py
"""

import pytest
from decimal import Decimal
from django.urls import reverse
from django.contrib.auth import get_user_model
from apps.products.models import Category, ProductType, Product, Bundle

User = get_user_model()


@pytest.mark.django_db
def test_login_required_redirects_for_profile_and_dashboard(client):
    resp = client.get(reverse("users:profile"))
    assert resp.status_code == 302
    assert "/accounts/login" in resp.url

    resp = client.get(reverse("users:dashboard"))
    assert resp.status_code == 302
    assert "/accounts/login" in resp.url


@pytest.mark.django_db
def test_dashboard_includes_saved_items_and_order_count(client):
    user = User.objects.create_user(username="u1", password="pass", email="u1@example.com")
    assert client.login(username="u1", password="pass")

    # Minimal catalogue data
    cat = Category.objects.create(name="Accessories", slug="accessories")
    ptype = ProductType.objects.create(name="Mount")

    product = Product.objects.create(
        name="DashCam", variant="A", description="desc",
        type=ptype, tier="Standard", category=cat,
        price=Decimal("9.99"), stock=1, sku="SKU-DC-1", product_code="PC-DC-1", is_draft=False,
    )
    bundle = Bundle.objects.create(
        name="Care Kit", description="bundle",
        discount_percentage=Decimal("10.00"),
        price=Decimal("0.00"), subtotal_price=Decimal("0.00"),
        bundle_type="Standard", sku="BNDL-100", bundle_code="bundle-care-kit-100",
    )

    # Save both to the user's profile
    profile = user.profile
    profile.saved_products.add(product)
    profile.saved_bundles.add(bundle)

    resp = client.get(reverse("users:dashboard"))
    assert resp.status_code == 200
    # Context should contain saved sets and order_count (0 here)
    assert "saved_products" in resp.context and list(resp.context["saved_products"])
    assert "saved_bundles" in resp.context and list(resp.context["saved_bundles"])
    assert resp.context["order_count"] == 0


@pytest.mark.django_db
def test_save_product_requires_login(client):
    cat = Category.objects.create(name="Cat", slug="cat")
    ptype = ProductType.objects.create(name="Type")
    product = Product.objects.create(
        name="Thing", variant="V", description="d",
        type=ptype, tier="Standard", category=cat,
        price=Decimal("5.00"), stock=1, sku="SKU-T-1", product_code="PC-T-1", is_draft=False,
    )

    resp = client.post(reverse("users:save_product", args=[product.id]))
    assert resp.status_code == 302
    assert "/accounts/login" in resp.url


@pytest.mark.django_db
def test_save_bundle_requires_login(client):
    bundle = Bundle.objects.create(
        name="B", description="d",
        discount_percentage=Decimal("10.00"),
        price=Decimal("0.00"), subtotal_price=Decimal("0.00"),
        bundle_type="Standard", sku="B-200", bundle_code="bundle-200",
    )
    resp = client.post(reverse("users:save_bundle", args=[bundle.id]))
    assert resp.status_code == 302
    assert "/accounts/login" in resp.url


@pytest.mark.django_db
def test_delete_account_removes_user(client):
    user = User.objects.create_user(username="deleteme", password="pass")
    assert client.login(username=user.username, password="pass")

    resp = client.post(reverse("users:delete_account"))
    assert resp.status_code == 302
    assert "/accounts/login" in resp.url

    assert not User.objects.filter(pk=user.pk).exists()
