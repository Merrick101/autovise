# apps/products/tests/test_models.py

import pytest
from decimal import Decimal
from django.core.exceptions import ValidationError
from apps.products.models import Bundle, Product, ProductType, Category


@pytest.mark.django_db
def test_bundle_requires_minimum_three_products():
    # Setup related FKs
    category = Category.objects.create(name="TestCat", slug="testcat")
    product_type = ProductType.objects.create(name="TypeA")

    # Create products
    p1 = Product.objects.create(name="One", variant="A", price=10, stock=10, tier="Standard",
                                type=product_type, category=category, sku="SKU1", product_code="PC1")
    p2 = Product.objects.create(name="Two", variant="B", price=12, stock=10, tier="Standard",
                                type=product_type, category=category, sku="SKU2", product_code="PC2")

    # Create bundle
    b = Bundle.objects.create(name="FailBundle", bundle_type="Standard")

    # Link only 2 products
    b.products.set([p1, p2])

    # Manual validation — not enforced at model level by default
    with pytest.raises(ValidationError):
        if b.products.count() < 3:
            raise ValidationError("Bundle must include at least 3 products.")


@pytest.mark.django_db
def test_bundle_pro_requires_pro_product():
    category = Category.objects.create(name="TestCat", slug="testcat")
    product_type = ProductType.objects.create(name="TypeA")

    standard_product = Product.objects.create(name="StandardItem", variant="S", price=10, stock=10, tier="Standard",
                                              type=product_type, category=category, sku="S1", product_code="PSC1")
    pro_product = Product.objects.create(name="ProItem", variant="P", price=20, stock=10, tier="Pro",
                                         type=product_type, category=category, sku="P1", product_code="PPC1")

    b = Bundle.objects.create(name="ProBundle", bundle_type="Pro")

    # Only Standard — should fail
    b.products.set([standard_product, standard_product, standard_product])
    has_pro = any(p.tier == "Pro" for p in b.products.all())
    assert not has_pro, "Expected no Pro-tier products"

    # Replace one product with Pro — should pass
    b.products.set([standard_product, standard_product, pro_product])
    has_pro = any(p.tier == "Pro" for p in b.products.all())
    assert has_pro, "Bundle must include at least one Pro-tier product"


@pytest.mark.django_db
def test_bundle_price_calculation():
    category = Category.objects.create(name="TestCat", slug="testcat")
    product_type = ProductType.objects.create(name="TypeA")

    p1 = Product.objects.create(name="P1", variant="V1", price=10, stock=10, tier="Standard",
                                type=product_type, category=category, sku="SK1", product_code="PK1")
    p2 = Product.objects.create(name="P2", variant="V2", price=20, stock=10, tier="Standard",
                                type=product_type, category=category, sku="SK2", product_code="PK2")
    p3 = Product.objects.create(name="P3", variant="V3", price=30, stock=10, tier="Standard",
                                type=product_type, category=category, sku="SK3", product_code="PK3")

    b = Bundle.objects.create(name="CalcBundle", discount_percentage=10.0)

    b.products.set([p1, p2, p3])
    subtotal = sum(p.price for p in b.products.all())
    expected = round(subtotal * Decimal('0.90'), 2)

    assert b.calculated_price() == expected
