# apps/orders/tests/test_cart_totals.py

import pytest
from apps.orders.models import Cart, CartItem
from apps.products.models import Product, Category, ProductType


@pytest.mark.django_db
def test_cart_total_matches_expected(django_user_model):
    user = django_user_model.objects.create_user(username='testuser2', password='pass')
    category = Category.objects.create(name="Test Category", slug="test-category")
    ptype = ProductType.objects.create(name="Test Type")

    cart = Cart.objects.create(user=user)

    p1 = Product.objects.create(
        name="Item A",
        price=5.00,
        sku="P002",
        product_code="TEST_CODE_1",
        stock=10,
        category=category,
        type=ptype
    )
    p2 = Product.objects.create(
        name="Item B",
        price=7.50,
        sku="P003",
        product_code="TEST_CODE_2",
        stock=10,
        category=category,
        type=ptype
    )

    CartItem.objects.create(cart=cart, product=p1, quantity=2)
    CartItem.objects.create(cart=cart, product=p2, quantity=1)

    expected_total = (2 * 5.00) + (1 * 7.50)
    assert round(cart.total(), 2) == expected_total
