"""
Tests for the sitemap.xml and robots.txt endpoints.
Located at apps/products/tests/test_sitemap.py
"""

import xml.etree.ElementTree as ET
from decimal import Decimal
from urllib.parse import urlparse

import pytest
from django.urls import reverse, NoReverseMatch

from apps.products.models import Category, ProductType, Product, Bundle

pytestmark = pytest.mark.django_db

NS = {"sm": "http://www.sitemaps.org/schemas/sitemap/0.9"}


def _local(el):
    return el.tag.split('}', 1)[-1]


def _locs(root):
    # Works for both <sitemapindex> and <urlset>
    return [n.text for n in root.findall(".//sm:loc", NS)]


def _seed_minimum():
    cat = Category.objects.create(name="Accessories", slug="accessories")
    ptype = ProductType.objects.create(name="Mount")
    p = Product.objects.create(
        name="X", variant="V", description="d",
        type=ptype, tier="Standard", category=cat,
        price=Decimal("9.99"), stock=1, sku="S1", product_code="C1", is_draft=False
    )
    b = Bundle.objects.create(
        name="B", description="d", discount_percentage=Decimal("10.00"),
        price=Decimal("0.00"), subtotal_price=Decimal("0.00"),
        bundle_type="Standard", sku="B1", bundle_code="bundle-b"
    )
    return p, b


def test_products_sitemap_has_urls(client):
    p, _ = _seed_minimum()

    # Prefer a section route (deterministic <urlset>)
    try:
        url = reverse("sitemap_section", kwargs={"section": "products"})
        resp = client.get(url)
        print("SECTION URL:", url, "status:", resp.status_code, "CT:", resp.get("Content-Type"))
        print(resp.content.decode()[:1500])
        assert resp.status_code == 200
        root = ET.fromstring(resp.content)
        assert _local(root) == "urlset"
    except NoReverseMatch:
        # Fall back to index then follow the products section
        resp = client.get(reverse("sitemap"))
        print("SECTION URL:", url, "status:", resp.status_code, "CT:", resp.get("Content-Type"))
        print(resp.content.decode()[:1500])
        assert resp.status_code == 200
        root = ET.fromstring(resp.content)
        assert _local(root) in {"sitemapindex", "urlset"}

        if _local(root) == "sitemapindex":
            locs = _locs(root)
            print("Index LOCs:", locs)
            products_section = next((u for u in locs if "sitemap-products" in (u or "")), None)
            assert products_section, "Products section missing from sitemap index"
            sec = client.get(urlparse(products_section).path or "/")
            print("FOLLOWED SECTION:", products_section, "status:", sec.status_code)
            print(sec.content.decode()[:1500])
            assert sec.status_code == 200
            root = ET.fromstring(sec.content)
            assert _local(root) == "urlset"

    locs = _locs(root)
    print("Final LOCs:", locs)
    assert locs, "Sitemap had no <loc> entries"
    # Ensure our seeded product appears
    product_path = reverse("products:product_detail", kwargs={"pk": p.pk})
    assert any(product_path in (u or "") for u in locs)


def test_robots_points_to_sitemap(client):
    resp = client.get("/robots.txt")
    assert resp.status_code == 200
    body = resp.content.decode()
    assert "Sitemap:" in body
    assert reverse("sitemap") in body
