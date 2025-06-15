# apps/products/templatetags/qstring.py

from django import template
register = template.Library()


@register.simple_tag(takes_context=True)
def qs_with(context, **kwargs):
    params = context['request'].GET.copy()
    for k, v in kwargs.items():
        if v is None:
            params.pop(k, None)
        else:
            params[k] = v
    return "?"+params.urlencode()
