"""
Tests for the Product list view with filtering, sorting,
searching, and pagination.
Located at apps/products/tests/test_product_list_view.py
"""

import pytest
from django.urls import reverse
from apps.products.models import Category, ProductType, Product


@pytest.fixture
def cat_a(db): return Category.objects.create(name="Accessories", slug="accessories")


@pytest.fixture
def cat_b(db): return Category.objects.create(name="Care", slug="care")


@pytest.fixture
def ptype(db): return ProductType.objects.create(name="Mount")


@pytest.fixture
def products(db, cat_a, cat_b, ptype):
    items = []
    for i, (cat, tier, price, draft) in enumerate([
        (cat_a, "Standard", 9.99, False),
        (cat_a, "Pro",      19.99, False),
        (cat_b, "Standard", 14.50, False),
        (cat_b, "Pro",      29.99, True),   # draft -> excluded
    ], start=1):
        items.append(Product.objects.create(
            name=f"Item {i}", variant="V", description="x",
            type=ptype, tier=tier, category=cat, price=price,
            stock=5, sku=f"SKU-{i}", product_code=f"PC-{i}",
            is_draft=draft
        ))
    return items


@pytest.mark.django_db
def test_list_excludes_drafts_and_filters_by_category(client, products, cat_a):
    url = reverse("products:product_list") + f"?category={cat_a.slug}"
    resp = client.get(url)
    assert resp.status_code == 200
    names = {p.name for p in resp.context["products"]}
    assert names == {"Item 1", "Item 2"}  # only cat_a, draft excluded


@pytest.mark.django_db
def test_list_filters_by_tier(client, products):
    url = reverse("products:product_list") + "?tier=Pro"
    resp = client.get(url)
    assert {p.name for p in resp.context["products"]} == {"Item 2"}  # draft Pro excluded


@pytest.mark.django_db
def test_list_search_matches_name_and_type(client, products):
    # Name
    resp = client.get(reverse("products:product_list") + "?q=Item 1")
    assert {p.name for p in resp.context["products"]} == {"Item 1"}
    # Type
    resp2 = client.get(reverse("products:product_list") + "?q=Mount")
    assert len(resp2.context["products"]) == 3


@pytest.mark.django_db
def test_list_sort_price_asc_desc(client, products):
    asc = client.get(reverse("products:product_list") + "?sort=price_asc")
    desc = client.get(reverse("products:product_list") + "?sort=price_desc")
    assert [p.price for p in asc.context["products"]] == sorted([9.99, 14.50, 19.99])
    assert [p.price for p in desc.context["products"]] == sorted([9.99, 14.50, 19.99], reverse=True)


@pytest.mark.django_db
def test_list_pagination_with_invalid_page_falls_back(client, cat_a, ptype):
    # Create 23 non-draft items
    for i in range(23):
        Product.objects.create(
            name=f"P{i}", variant="V", description="x", type=ptype, tier="Standard",
            category=cat_a, price=1, stock=1, sku=f"S{i}", product_code=f"C{i}"
        )
    url_bad = reverse("products:product_list") + "?page=not-an-int"
    resp_bad = client.get(url_bad)
    assert resp_bad.status_code == 200
    assert len(resp_bad.context["products"]) == 20  # first page size

    url_over = reverse("products:product_list") + "?page=9999"
    resp_over = client.get(url_over)
    assert resp_over.status_code == 200
    # fallback to page 1 again per the view
    assert len(resp_over.context["products"]) == 20
