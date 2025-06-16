# apps/pages/templatetags/featured_tags.py

from django import template
from apps.products.models import Product, Bundle

register = template.Library()


@register.inclusion_tag('include/featured_products.html')
def show_featured_products(limit=4):
    products = Product.objects.filter(featured=True, is_draft=False)[:limit]
    return {'featured_products': products}


@register.inclusion_tag('include/featured_bundles.html')
def show_featured_bundles(limit=4):
    bundles = Bundle.objects.filter(featured=True)[:limit]
    return {'featured_bundles': bundles}
