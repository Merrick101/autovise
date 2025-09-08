"""
Tests for the Bundle list view with filtering, sorting, and searching.
Located at apps/products/tests/test_bundle_list_view.py
"""

import pytest
from django.urls import reverse
from apps.products.models import Bundle


@pytest.fixture
def bundles(db):
    return [
        Bundle.objects.create(name="Starter", description="good", bundle_type="Standard",
                              discount_percentage=10, price=10, subtotal_price=12,
                              sku="B1", bundle_code="bundle-starter"),
        Bundle.objects.create(name="Pro Kit", description="great", bundle_type="Pro",
                              discount_percentage=15, price=20, subtotal_price=25,
                              sku="B2", bundle_code="bundle-pro"),
        Bundle.objects.create(name="Special Box", description="limited", bundle_type="Special",
                              discount_percentage=5, price=30, subtotal_price=32,
                              sku="B3", bundle_code="bundle-special"),
    ]


@pytest.mark.django_db
def test_filter_by_bundle_type(client, bundles):
    resp = client.get(reverse("products:bundle_list") + "?type=Pro")
    assert resp.status_code == 200
    names = [b.name for b in resp.context["bundles"]]
    assert names == ["Pro Kit"]


@pytest.mark.django_db
def test_sort_price_asc_desc(client, bundles):
    asc = client.get(reverse("products:bundle_list") + "?sort=price_asc")
    desc = client.get(reverse("products:bundle_list") + "?sort=price_desc")
    assert [b.price for b in asc.context["bundles"]] == [10, 20, 30]
    assert [b.price for b in desc.context["bundles"]] == [30, 20, 10]


@pytest.mark.django_db
def test_search_name_and_description(client, bundles):
    by_name = client.get(reverse("products:bundle_list") + "?q=Pro")
    assert [b.name for b in by_name.context["bundles"]] == ["Pro Kit"]

    by_desc = client.get(reverse("products:bundle_list") + "?q=limited")
    assert [b.name for b in by_desc.context["bundles"]] == ["Special Box"]


@pytest.mark.django_db
def test_context_banner_and_search_cleared(client, bundles):
    resp = client.get(reverse("products:bundle_list"))
    assert "promo_banner" in resp.context
    assert resp.context["search_q"] == ""   # the view intentionally clears the input
