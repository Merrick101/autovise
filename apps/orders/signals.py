# orders/signals.py

from django.contrib.auth.signals import user_logged_in
from django.dispatch import receiver
from orders.models import CartItem
from orders.utils.cart import get_or_create_cart


@receiver(user_logged_in)
def merge_session_cart(sender, request, user, **kwargs):
    session_cart = request.session.get('cart', {})
    if not session_cart:
        return

    db_cart = get_or_create_cart(user)

    for product_code, item in session_cart.items():
        product_id = item.get('product_id')
        quantity = item.get('quantity', 1)

        # Avoid duplicate CartItems
        existing_item = db_cart.items.filter(product_id=product_id).first()
        if existing_item:
            existing_item.quantity += quantity
            existing_item.save()
        else:
            CartItem.objects.create(cart=db_cart, product_id=product_id, quantity=quantity)

    # Clear session cart after merge
    request.session['cart'] = {}
    request.session.modified = True
