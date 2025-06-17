# apps/orders/tests/test_order_models.py

import pytest
from apps.orders.models import Order, OrderItem
from apps.products.models import Product, Category, ProductType


@pytest.mark.django_db
def test_order_total_matches_items(django_user_model):
    user = django_user_model.objects.create_user(username="user3", password="pass")
    order = Order.objects.create(user=user, total_price=30.00)
    category = Category.objects.create(name="Test Category", slug="test-category")
    ptype = ProductType.objects.create(name="Test Type")

    p1 = Product.objects.create(
        name="Test A",
        price=10.00,
        sku="A01",
        product_code="ORDER_CODE_1",
        stock=10,
        category=category,
        type=ptype
    )
    p2 = Product.objects.create(
        name="Test B",
        price=20.00,
        sku="A02",
        product_code="ORDER_CODE_2",
        stock=10,
        category=category,
        type=ptype
    )

    OrderItem.objects.create(order=order, product=p1, unit_price=10.00, quantity=1)
    OrderItem.objects.create(order=order, product=p2, unit_price=10.00, quantity=2)

    total = sum(item.subtotal for item in order.items.all())
    assert round(total, 2) == 30.00
    assert str(order).startswith("Order #")


def test_order_str_output(django_user_model):
    user = django_user_model.objects.create_user(username='orderuser', password='pass')
    order = Order.objects.create(user=user, total_price=10.00)
    assert f"Order #{order.id} for orderuser" in str(order)
