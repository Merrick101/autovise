from django import template
from decimal import Decimal, DivisionByZero

register = template.Library()


@register.filter
def item_key(item):
    product = item.get("product")
    if item.get("is_bundle", False):
        return f"bundle_{product.id}"
    return product.product_code


@register.filter
def div(value, arg):
    try:
        return Decimal(value) / Decimal(arg)
    except (ValueError, ZeroDivisionError, TypeError, DivisionByZero):
        return 0
