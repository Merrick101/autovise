"""
Tests for Product and Bundle admin forms.
Located at apps/products/tests/test_admin_forms.py
"""

import pytest
from decimal import Decimal
from apps.products.forms import ProductAdminForm, BundleAdminForm
from apps.products.models import Product, Bundle, Category, ProductType


@pytest.fixture
def base(db):
    return {
        "cat": Category.objects.create(name="Accessories", slug="accessories"),
        "ptype": ProductType.objects.create(name="Mount"),
    }


@pytest.mark.django_db
def test_product_admin_form_image_path_overrides_instance(base):
    p = Product(
        name="X", variant="V", description="x",
        type=base["ptype"], tier="Standard", category=base["cat"],
        price=1, stock=1, sku="S", product_code="C"
    )
    form = ProductAdminForm(data={"name": p.name, "variant": p.variant, "tier": p.tier,
                                  "type": base["ptype"].id, "category": base["cat"].id,
                                  "price": 1, "stock": 1, "sku": "S", "product_code": "C",
                                  "description": "x", "image_path": "products/path.png"},
                            instance=p)
    assert form.is_valid(), form.errors
    form.save()
    assert p.image.name == "products/path.png"


@pytest.mark.django_db
def test_bundle_admin_form_defaults_and_image_path():
    b = Bundle(name="B", description="", bundle_type="Standard",
               price=0, subtotal_price=0, sku="B1", bundle_code="bundle-b")
    form = BundleAdminForm(data={"name": "B", "slug": "", "description": "",
                                 "discount_percentage": "", "price": 0, "bundle_type": "Standard",
                                 "sku": "B1", "bundle_code": "bundle-b", "image_path": "bundles/img.png"},
                           instance=b)
    assert form.is_valid(), form.errors
    obj = form.save()
    assert obj.image.name == "bundles/img.png"
    # discount defaults to 10.0 when empty
    assert obj.discount_percentage == Decimal("10.0")
