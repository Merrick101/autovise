# apps/orders/context_processors.py

from django.db.models import F  # NOQA
from types import SimpleNamespace
from apps.orders.models import CartItem
from apps.products.models import Product, Bundle


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
        items.extend(qs)
        count = sum(ci.quantity for ci in qs)
    else:
        session_cart = request.session.get('cart', {}) or {}

        for key, entry in session_cart.items():
            # Bundle entry: key like "bundle_<id>"
            if isinstance(key, str) and key.startswith("bundle_"):
                try:
                    bundle_id = int(key.split("_", 1)[1])
                    bundle = Bundle.objects.get(pk=bundle_id)
                except (ValueError, Bundle.DoesNotExist):
                    continue
                qty = int(entry.get('quantity', 0)) or 0
                if qty <= 0:
                    continue
                # CartItem-like shape with .bundle and .quantity
                obj = SimpleNamespace(
                    product=None,
                    bundle=bundle,
                    quantity=qty,
                    get_total_price=lambda b=bundle, q=qty: b.price * q,
                )
                items.append(obj)
                count += qty
                continue

            # Product entry (session shape)
            prod_id = entry.get('product_id')
            qty = int(entry.get('quantity', 0)) or 0
            if not prod_id or qty <= 0:
                continue
            try:
                prod = Product.objects.get(pk=prod_id)
            except Product.DoesNotExist:
                continue

            obj = SimpleNamespace(
                product=prod,
                bundle=None,
                quantity=qty,
                get_total_price=lambda p=prod, q=qty: p.price * q,
            )
            items.append(obj)
            count += qty

    return {
        'cart_items': items,
        'cart_item_count': count,
    }
