# orders/utils/cart.py

from orders.models import Cart


def get_or_create_cart(user):
    cart, created = Cart.objects.get_or_create(user=user, is_active=True)
    return cart
