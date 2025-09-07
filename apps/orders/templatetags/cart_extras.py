"""
Custom template filters for cart-related functionality.
Located at apps/orders/templatetags/cart_extras.py
"""

from django import template

register = template.Library()


@register.filter
def item_key(item):
    """
    Return the canonical key for a cart line, matching how we store it:
      - Bundles (session cart):   "bundle_<id>"
      - Products (session cart):  product.product_code (fallback to product.id)
      - CartItem (DB cart):       product.product_code (fallback to product.id)

    This ensures update/remove URLs target the correct key for both guests and
    authenticated users.
    """
    # Dict coming from calculate_cart_summary()
    if isinstance(item, dict):
        bundle = item.get("bundle")
        if bundle is not None:
            return f"bundle_{bundle.id}"

        product = item.get("product")
        if product is not None:
            key = getattr(product, "product_code", None) or product.id
            return str(key)

        # If you ever add raw 'key' into the summary dicts
        return str(item.get("key", ""))

    # CartItem model instance (DB cart before summary conversion)
    product = getattr(item, "product", None)
    if product is not None:
        key = getattr(product, "product_code", None) or product.id
        return str(key)

    return ""
