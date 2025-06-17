# apps/orders/tests/test_constraints.py

import pytest
from django.db import IntegrityError
from apps.orders.models import Order, OrderItem
from apps.products.models import Product, Bundle, Category, ProductType


@pytest.mark.django_db
def test_orderitem_product_bundle_xor_constraint(django_user_model):
    user = django_user_model.objects.create_user(username='user4', password='pass')
    order = Order.objects.create(user=user, total_price=0)
    category = Category.objects.create(name="Test Category", slug="test-category")
    ptype = ProductType.objects.create(name="Test Type")

    product = Product.objects.create(
        name="Test Product",
        price=10,
        sku="X01",
        stock=10,
        category=category,
        type=ptype
    )

    bundle = Bundle.objects.create(name="Test Bundle", discount_percentage=10)

    # Product only — should work
    OrderItem.objects.create(order=order, product=product, unit_price=10, quantity=1)

    # Bundle only — should work
    OrderItem.objects.create(order=order, bundle=bundle, unit_price=20, quantity=1)

    # Both product & bundle — should raise IntegrityError
    with pytest.raises(IntegrityError):
        OrderItem.objects.create(order=order, product=product, bundle=bundle, unit_price=15)
