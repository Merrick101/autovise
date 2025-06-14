from django import template

register = template.Library()


@register.filter
def item_key(item):
    product = item.get("product")
    if item.get("is_bundle", False):
        return f"bundle_{product.id}"
    return product.product_code
