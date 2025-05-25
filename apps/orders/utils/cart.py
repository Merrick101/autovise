# orders/utils/cart.py

from apps.orders.models import Cart, CartItem
from apps.products.models import Product


def add_to_cart(request, product_id, quantity=1):
    product = Product.objects.get(id=product_id)

    if request.user.is_authenticated:
        cart = get_or_create_cart(request.user)
        item, created = CartItem.objects.get_or_create(cart=cart, product=product)
        if not created:
            item.quantity += quantity
        else:
            item.quantity = quantity
        item.save()
    else:
        cart = request.session.get('cart', {})
        product_code = product.product_code
        if product_code in cart:
            cart[product_code]['quantity'] += quantity
        else:
            cart[product_code] = {
                'product_id': product.id,
                'name': product.name,
                'quantity': quantity,
                'price': float(product.price),
                'image_type': product.image_type,
            }
        save_cart(request, cart)


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
