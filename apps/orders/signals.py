# apps/orders/signals.py

import logging
from django.contrib.auth.signals import user_logged_in
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils.timezone import now  # noqa: F401
from apps.orders.models import Cart, CartItem
from apps.orders.utils.cart import get_or_create_cart

logger = logging.getLogger(__name__)


@receiver(user_logged_in)
def merge_session_cart(sender, request, user, **kwargs):
    session_cart = request.session.get('cart', {}) or {}
    if not session_cart:
        return

    db_cart = get_or_create_cart(user)

    for key, item in session_cart.items():
        # Skip bundles and any non-product entries
        if isinstance(key, str) and key.startswith("bundle_"):
            continue

        product_id = item.get('product_id')
        quantity = int(item.get('quantity', 1) or 1)

        if not product_id or quantity <= 0:
            continue

        existing_item = db_cart.items.filter(product_id=product_id).first()
        if existing_item:
            existing_item.quantity += quantity
            existing_item.save()
            logger.debug(f"[Cart Merge] Updated quantity for product {product_id} in cart {db_cart.id}")
        else:
            CartItem.objects.create(cart=db_cart, product_id=product_id, quantity=quantity)
            logger.debug(f"[Cart Merge] Added product {product_id} to cart {db_cart.id}")

    request.session['cart'] = {}
    request.session.modified = True
    logger.info(f"[Cart Merge] Session cart merged into DB cart for user {user.username}")


@receiver(post_save, sender=Cart)
def log_cart_saved(sender, instance, created, **kwargs):
    if created:
        logger.info(f"[Cart] New cart created for user {instance.user} at {instance.created_at}")
    else:
        logger.debug(f"[Cart] Cart {instance.id} updated at {instance.updated_at}")


@receiver(post_save, sender=CartItem)
def log_cart_item_saved(sender, instance, created, **kwargs):
    action = "added to" if created else "updated in"
    logger.debug(f"[CartItem] Product {instance.product.name} {action} Cart {instance.cart.id} (Qty: {instance.quantity})")
