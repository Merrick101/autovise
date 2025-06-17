# conftest.py (place at project root or inside your main folder)

import pytest
from django.contrib.auth.models import User
from apps.products.models import (
    Product, Category, ProductType, Subcategory,
    Bundle, Tag
)


@pytest.fixture
def user(db):
    return User.objects.create_user(username="testuser", password="pass")


@pytest.fixture
def category(db):
    return Category.objects.create(name="Test Category", slug="test-category")


@pytest.fixture
def subcategory(db, category):
    return Subcategory.objects.create(name="Test Subcategory", slug="test-sub", category=category)


@pytest.fixture
def product_type(db):
    return ProductType.objects.create(name="Test Type")


@pytest.fixture
def tag(db):
    return Tag.objects.create(name="Test Tag")


@pytest.fixture
def product(db, category, product_type):
    return Product.objects.create(
        name="Test Product",
        variant="Standard",
        price=10.00,
        stock=5,
        sku="SKU-123",
        product_code="PC-123",
        tier="Standard",
        category=category,
        type=product_type
    )


@pytest.fixture
def pro_product(db, category, product_type):
    return Product.objects.create(
        name="Pro Product",
        variant="Pro",
        price=25.00,
        stock=8,
        sku="SKU-456",
        product_code="PC-456",
        tier="Pro",
        category=category,
        type=product_type
    )


@pytest.fixture
def bundle(db):
    return Bundle.objects.create(
        name="Test Bundle",
        discount_percentage=10.00,
        bundle_type="Standard",
        sku="B-SKU-001",
        bundle_code="B-CODE-001"
    )
