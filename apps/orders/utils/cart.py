# orders/utils/cart.py

from orders.models import Cart, CartItem
from apps.products.models import Product


def get_or_create_cart(user):
    """Returns the active cart for a user or creates one if it doesn't exist."""
    cart, created = Cart.objects.get_or_create(user=user, is_active=True)
    return cart


def get_active_cart(request):
    """
    Returns a tuple: (cart object, 'db') for authenticated users,
    or (session cart dict, 'session') for guests.
    """
    if request.user.is_authenticated:
        return get_or_create_cart(request.user), 'db'
    else:
        cart = request.session.get('cart', {})
        return cart, 'session'


def save_cart(request, cart_data):
    request.session['cart'] = cart_data
    request.session.modified = True


def clear_session_cart(request):
    request.session['cart'] = {}
    request.session.modified = True
