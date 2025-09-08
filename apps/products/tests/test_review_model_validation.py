"""
Tests for Review model validation.
Located at apps/products/tests/test_review_model_validation.py
"""

import pytest
from django.core.exceptions import ValidationError
from django.contrib.auth.models import User
from apps.products.models import Review, Product, Bundle, Category, ProductType


@pytest.fixture
def base(db):
    return {
        "user": User.objects.create_user("u", password="pw"),
        "cat": Category.objects.create(name="Accessories", slug="accessories"),
        "ptype": ProductType.objects.create(name="Mount"),
        "bundle": Bundle.objects.create(
          name="B", description="", discount_percentage=10, price=0, subtotal_price=0, bundle_type="Standard", sku="B1", bundle_code="bundle-b"
        ),
    }


@pytest.mark.django_db
def test_review_clean_requires_exactly_one_target(base):
    p = Product.objects.create(
        name="P", variant="V", description="x", type=base["ptype"], tier="Standard",
        category=base["cat"], price=1, stock=1, sku="S", product_code="C"
    )

    r_none = Review(user=base["user"], rating=5, comment="")
    with pytest.raises(ValidationError):
        r_none.clean()

    r_both = Review(user=base["user"], product=p, bundle=base["bundle"], rating=5, comment="")
    with pytest.raises(ValidationError):
        r_both.clean()

    r_ok = Review(user=base["user"], product=p, rating=5, comment="")
    # Should not raise
    r_ok.clean()
