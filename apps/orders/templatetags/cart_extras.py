# apps/orders/templatetags/cart_extras.py

from django import template
register = template.Library()


@register.filter
def item_key(item):
    """
    Return a stable key for this cart item, whether it's a product or a bundle.
    Used for building update/remove URLs in the cart template.
    """
    # 1) If it's a dict coming from calculate_cart_summary()
    if isinstance(item, dict):
        # bundles carry a 'bundle' key
        bundle = item.get('bundle')
        if bundle is not None:
            return f"bundle_{bundle.id}"
        # otherwise it's a product
        product = item.get('product')
        if product is not None:
            return str(product.id)
        # fallback if 'key' field is added
        return item.get('key', "")

    # 2) If it's a CartItem model instance
    #    (the DB-backed cart before summary conversion)
    if hasattr(item, "product") and item.product:
        return str(item.product.id)
    return ""
