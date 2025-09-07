"""
Context processors for orders app.
Adds cart data to every template context.
Located at apps/orders/context_processors.py
"""

from types import SimpleNamespace
from decimal import Decimal

from apps.orders.models import CartItem
from apps.products.models import Product, Bundle


def cart_data(request):
    """
    Adds `cart_items` (list of CartItem-like objects) and `cart_item_count`
    to every template context.

    - Authenticated users:
        * Products come from the DB cart (CartItem)
        * Bundles are merged from the session cart (key "bundle_<id>")
          using the discounted session price if provided.
    - Guests:
        * Everything comes from the session cart.
    """
    items = []
    count = 0

    if request.user.is_authenticated:
        # DB products
        qs = (
            CartItem.objects
            .filter(cart__user=request.user)
            .select_related("product")
        )
        items.extend(qs)
        count += sum(ci.quantity for ci in qs)

        # Merge session bundles (do not merge session products to avoid dupes)
        session_cart = (getattr(request, "session", None) or {}).get("cart", {}) or {}
        for key, entry in session_cart.items():
            if not (isinstance(key, str) and key.startswith("bundle_")):
                continue
            # Resolve bundle
            try:
                bundle_id = int(key.split("_", 1)[1])
                bundle = Bundle.objects.get(pk=bundle_id)
            except (ValueError, Bundle.DoesNotExist):
                continue

            # Quantity
            try:
                qty = int(entry.get("quantity", 0) or 0)
            except (TypeError, ValueError):
                qty = 0
            if qty <= 0:
                continue

            # Use session price if present,
            # (this is typically the discounted unit)
            unit = entry.get("price", None)
            try:
                unit = Decimal(str(unit)) if unit is not None else Decimal(bundle.price)
            except Exception:
                unit = Decimal(bundle.price)

            total = unit * qty  # precompute to avoid late-binding in lambda

            # CartItem-like shape for the navbar template
            items.append(
                SimpleNamespace(
                    product=None,
                    bundle=bundle,
                    quantity=qty,
                    get_total_price=lambda t=total: t,
                )
            )
            count += qty

        return {
            "cart_items": items,
            "cart_item_count": count,
        }

    # Guest users: read everything from session cart
    session_cart = request.session.get("cart", {}) or {}

    for key, entry in session_cart.items():
        # Bundles
        if isinstance(key, str) and key.startswith("bundle_"):
            try:
                bundle_id = int(key.split("_", 1)[1])
                bundle = Bundle.objects.get(pk=bundle_id)
            except (ValueError, Bundle.DoesNotExist):
                continue

            try:
                qty = int(entry.get("quantity", 0) or 0)
            except (TypeError, ValueError):
                qty = 0
            if qty <= 0:
                continue

            unit = entry.get("price", None)
            try:
                unit = Decimal(str(unit)) if unit is not None else Decimal(bundle.price)
            except Exception:
                unit = Decimal(bundle.price)

            items.append(
                SimpleNamespace(
                    product=None,
                    bundle=bundle,
                    quantity=qty,
                    get_total_price=lambda u=unit, q=qty: u * q,
                )
            )
            count += qty
            continue

        # Products
        prod_id = entry.get("product_id")
        try:
            qty = int(entry.get("quantity", 0) or 0)
        except (TypeError, ValueError):
            qty = 0
        if not prod_id or qty <= 0:
            continue

        try:
            prod = Product.objects.get(pk=prod_id)
        except Product.DoesNotExist:
            continue

        # Prefer session unit price if present; else model price
        unit = entry.get("price", None)
        try:
            unit = Decimal(str(unit)) if unit is not None else Decimal(prod.price)
        except Exception:
            unit = Decimal(prod.price)

        items.append(
            SimpleNamespace(
                product=prod,
                bundle=None,
                quantity=qty,
                get_total_price=lambda u=unit, q=qty: u * q,
            )
        )
        count += qty

    return {
        "cart_items": items,
        "cart_item_count": count,
    }
