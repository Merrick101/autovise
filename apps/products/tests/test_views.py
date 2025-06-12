# apps/products/tests/test_views.py

import pytest
from decimal import Decimal
from django.urls import reverse
from apps.products.models import Bundle, Product, Category, ProductType


@pytest.mark.django_db
def test_bundle_list_displays_prices_correctly(client):
    # Set up
    category = Category.objects.create(name="TestCat", slug="testcat")
    product_type = ProductType.objects.create(name="TypeA")

    p1 = Product.objects.create(name="P1", variant="V1", price=10, stock=10, tier="Standard",
                                type=product_type, category=category, sku="SKU1", product_code="P1C")
    p2 = Product.objects.create(name="P2", variant="V2", price=20, stock=10, tier="Standard",
                                type=product_type, category=category, sku="SKU2", product_code="P2C")
    p3 = Product.objects.create(name="P3", variant="V3", price=30, stock=10, tier="Standard",
                                type=product_type, category=category, sku="SKU3", product_code="P3C")

    bundle = Bundle.objects.create(name="BundleX", discount_percentage=10.0)
    bundle.products.set([p1, p2, p3])
    bundle.subtotal_price = sum(p.price for p in bundle.products.all())
    bundle.price = round(bundle.subtotal_price * Decimal('0.90'), 2)
    bundle.save()

    # Act
    url = reverse('products:bundle_list')
    response = client.get(url)

    # Assert
    content = response.content.decode()
    assert "BundleX" in content
    assert f"£{bundle.price:.2f}" in content
    assert f"£{bundle.subtotal_price:.2f}" in content


@pytest.mark.django_db
def test_bundle_detail_displays_correct_prices(client):
    category = Category.objects.create(name="TestCat", slug="testcat")
    product_type = ProductType.objects.create(name="TypeB")

    p1 = Product.objects.create(name="P1", variant="V1", price=15, stock=10, tier="Standard",
                                type=product_type, category=category, sku="SKU4", product_code="P4C")
    p2 = Product.objects.create(name="P2", variant="V2", price=25, stock=10, tier="Standard",
                                type=product_type, category=category, sku="SKU5", product_code="P5C")
    p3 = Product.objects.create(name="P3", variant="V3", price=35, stock=10, tier="Standard",
                                type=product_type, category=category, sku="SKU6", product_code="P6C")

    bundle = Bundle.objects.create(name="BundleY", discount_percentage=10.0)
    bundle.products.set([p1, p2, p3])
    bundle.subtotal_price = sum(p.price for p in bundle.products.all())
    bundle.price = round(bundle.subtotal_price * Decimal('0.90'), 2)
    bundle.save()

    url = reverse('products:bundle_detail', args=[bundle.id])
    response = client.get(url)

    content = response.content.decode()
    assert f"£{bundle.price:.2f}" in content
    assert f"£{bundle.subtotal_price:.2f}" in content
