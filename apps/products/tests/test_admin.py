# apps/products/tests/test_admin.py

import pytest
from decimal import Decimal
from django.contrib.admin.sites import site
from apps.products.admin import ProductAdmin, BundleAdmin
from apps.products.models import Product, Bundle, Category, ProductType, Tag


@pytest.mark.django_db
def test_product_admin_registered():
    assert isinstance(site._registry[Product], ProductAdmin)


@pytest.mark.django_db
def test_bundle_admin_registered():
    assert isinstance(site._registry[Bundle], BundleAdmin)


@pytest.mark.django_db
def test_bundle_admin_tag_list():
    tag1 = Tag.objects.create(name="Winter Kit")
    tag2 = Tag.objects.create(name="Pro Combo")
    bundle = Bundle.objects.create(name="Test Bundle", price=50, discount_percentage=10.0)
    bundle.tags.set([tag1, tag2])

    admin_instance = BundleAdmin(Bundle, site)
    result = admin_instance.tag_list(bundle)

    assert "Winter Kit" in result
    assert "Pro Combo" in result


@pytest.mark.django_db
def test_bundle_admin_formatted_price():
    bundle = Bundle.objects.create(name="Test Bundle", price=Decimal("29.99"), discount_percentage=10.0)
    admin_instance = BundleAdmin(Bundle, site)
    result = admin_instance.formatted_price(bundle)

    assert "£29.99" in result
