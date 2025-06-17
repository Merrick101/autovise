# apps/orders/tests/test_cart_models.py

import pytest
from apps.orders.models import Cart, CartItem
from apps.products.models import Product, Category, ProductType


@pytest.mark.django_db
def test_add_single_product_to_cart(django_user_model):
    user = django_user_model.objects.create_user(username='testuser', password='pass')
    category = Category.objects.create(name="Test Category", slug="test-category")
    ptype = ProductType.objects.create(name="Test Type")

    product = Product.objects.create(
        name="Test Product",
        price=10.00,
        sku="P001",
        stock=10,
        category=category,
        type=ptype
    )
    cart = Cart.objects.create(user=user)
    item = CartItem.objects.create(cart=cart, product=product, quantity=2)

    assert item.subtotal() == 20.00
    assert str(item) == "2 × Test Product"
    assert item.cart == cart
    assert item.product == product


def test_cart_str_output(django_user_model):
    user = django_user_model.objects.create_user(username='testuser_str', password='pass')
    cart = Cart.objects.create(user=user)
    assert str(cart) == f"Cart for {user.username} (Active: {cart.is_active})"
