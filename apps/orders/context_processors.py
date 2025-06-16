from django.db.models import F
from .models import CartItem
from apps.products.models import Product


def cart_data(request):
    """
    Adds `cart_items` (list of CartItem-like objects) and
    `cart_item_count` to every template context.
    """
    items = []
    count = 0

    if request.user.is_authenticated:
        qs = CartItem.objects.filter(
          cart__user=request.user
        ).select_related('product')
        for ci in qs:
            items.append(ci)
        count = sum(ci.quantity for ci in qs)
    else:
        session_cart = request.session.get('cart', {})
        for entry in session_cart.values():
            try:
                prod = Product.objects.get(pk=entry['product_id'])
                qty = entry.get('quantity', 0)
            except Product.DoesNotExist:
                continue
            # Fake a CartItem-like object:
            ci = type('X', (), {
                'product': prod,
                'quantity': qty,
                'get_total_price': lambda self=prod, q=qty: prod.price * q
            })()
            items.append(ci)
            count += qty

    return {
        'cart_items':       items,
        'cart_item_count':  count,
    }
