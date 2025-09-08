"""
Tests for Product and Bundle models.
Located at apps/products/tests/test_models_products.py
"""

from decimal import Decimal
import pytest
from django.contrib.auth.models import User
from apps.products.models import (
    Bundle, Product, Category, ProductType, ProductBundle, Review
)


@pytest.fixture
def base(db):
    return {
        "cat": Category.objects.create(name="Accessories", slug="accessories"),
        "ptype": ProductType.objects.create(name="Mount"),
        "user": User.objects.create_user("u", password="pw")
    }


@pytest.mark.django_db
def test_auto_slug_on_save(base):
    p = Product.objects.create(
        name="Phone Grip", variant="V", description="x", type=base["ptype"], tier="Standard",
        category=base["cat"], price=1, stock=1, sku="S1", product_code="C1"
    )
    b = Bundle.objects.create(
        name="My Bundle", description="x", discount_percentage=10, price=0, subtotal_price=0,
        bundle_type="Standard", sku="B1", bundle_code="bundle-my-bundle",
    )
    assert p.slug == "phone-grip"
    assert b.slug == "my-bundle"


@pytest.mark.django_db
def test_average_and_count_product(base):
    p = Product.objects.create(
        name="Rated", variant="V", description="x", type=base["ptype"], tier="Standard",
        category=base["cat"], price=1, stock=1, sku="S2", product_code="C2"
    )
    Review.objects.create(user=base["user"], product=p, rating=5, comment="")
    Review.objects.create(user=User.objects.create_user("u2"), product=p, rating=3, comment="")
    assert p.review_count() == 2
    # model returns 0 if no reviews; with two we expect 4.0
    assert float(p.average_rating()) == 4.0


@pytest.mark.django_db
def test_bundle_calculated_price_default_and_custom_with_products():
    cat = Category.objects.create(name="Accessories", slug="accessories")
    ptype = ProductType.objects.create(name="Mount")

    # Default discount is 10.00
    b = Bundle.objects.create(
        name="Calc", description="", bundle_type="Standard",
        price=0, subtotal_price=0, sku="B2", bundle_code="bundle-calc",
    )

    p = Product.objects.create(
        name="Phone Mount", variant="V", description="x", type=ptype, tier="Standard",
        category=cat, price=Decimal("100.00"), stock=5, sku="S100", product_code="C100",
    )
    ProductBundle.objects.create(product=p, bundle=b)

    # total=100 → with 10% -> 90.00
    assert b.calculated_price() == Decimal("90.00")

    # Change to 25% → 75.00
    b.discount_percentage = Decimal("25.00")
    assert b.calculated_price() == Decimal("75.00")
