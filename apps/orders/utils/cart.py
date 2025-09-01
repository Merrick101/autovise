# apps/orders/utils/cart.py

from apps.orders.models import Cart, CartItem
from apps.products.models import Product, Bundle
from decimal import Decimal
from datetime import date, timedelta
import logging

logger = logging.getLogger(__name__)


def is_first_time_user(user):
    return hasattr(user, 'profile') and user.profile.is_first_time_buyer


def add_to_cart(request, product_id, quantity=1):
    """
    Add a product to the active user's cart or session cart.
    If the product is already present, increase its quantity.
    """
    product = Product.objects.get(id=product_id)

    if request.user.is_authenticated:
        cart = get_or_create_cart(request.user)
        item, created = CartItem.objects.get_or_create(cart=cart, product=product)
        item.quantity = item.quantity + quantity if not created else quantity
        item.save()
    else:
        cart = request.session.get('cart', {})
        product_code = product.product_code
        if product_code in cart:
            cart[product_code]['quantity'] += quantity
        else:
            cart[product_code] = {
                'product_id': product.id,
                'name': product.name,
                'quantity': quantity,
                'price': float(product.price),
                'image_type': product.image_type,
            }
        save_cart(request, cart)


def get_or_create_cart(user):
    return Cart.objects.get_or_create(user=user, is_active=True)[0]


def get_active_cart(request):
    return (get_or_create_cart(request.user), 'db') if request.user.is_authenticated else (request.session.get('cart', {}), 'session')


def save_cart(request, cart_data):
    request.session['cart'] = cart_data
    request.session.modified = True


def clear_session_cart(request):
    request.session['cart'] = {}
    request.session.modified = True


def calculate_cart_summary(request, cart_data, cart_type):
    """
    Calculate full cart breakdown including:
    - Bundle and first-time discounts
    - Delivery fee logic
    - Grand total and estimated delivery date

    Returns a structured summary dict for use in views.
    """

    items = []
    total = Decimal("0.00")
    bundle_discount_total = Decimal("0.00")
    cart_discount_total = Decimal("0.00")
    first_time_discount = False

    def is_bundle_product(product):
        return product.type and product.type.name.lower() == "bundle"

    # 1) DB-backed cart: same as before, but record both product/bundle keys
    if cart_type == "db":
        for ci in cart_data.items.select_related("product"):
            product = ci.product
            quantity = ci.quantity
            unit_price = product.price
            subtotal = unit_price * quantity

            # accumulate raw bundle discount (10% of line subtotal)
            if is_bundle_product(product):
                bundle_discount_total += subtotal * Decimal("0.10")

            # compute any per-line discounted price (e.g. bundle/subtotal logic)
            discounted_price = subtotal / quantity if quantity > 0 else unit_price
            discount_percent = (
                (unit_price - discounted_price) / unit_price * Decimal("100.00")
                if unit_price > 0 and discounted_price < unit_price
                else Decimal("0.00")
            )

            is_bundle = is_bundle_product(product)
            items.append({
                "product": None if is_bundle else product,
                "bundle":  product if is_bundle else None,
                "quantity": quantity,
                "unit_price": unit_price,
                "discounted_price": discounted_price,
                "discount_percent": discount_percent,
                "subtotal": subtotal,
                "tier": product.tier,
                "is_bundle": is_bundle,
            })
            total += subtotal

    # 2) Session-backed cart: detect bundles by key prefix "bundle_<id>"
    else:
        for key, entry in cart_data.items():
            # --- bundle entry if key starts with "bundle_" ---
            if key.startswith("bundle_"):
                try:
                    bundle_id = int(key.split("_", 1)[1])
                    bundle = Bundle.objects.get(pk=bundle_id)
                except (ValueError, Bundle.DoesNotExist):
                    continue

                quantity = int(entry.get("quantity", 0) or 0)
                if quantity <= 0:
                    continue

                # Fallback: if subtotal_price isn't present, use bundle.price
                raw_base = getattr(bundle, "subtotal_price", None)
                try:
                    base_price = Decimal(raw_base) if raw_base is not None else Decimal(bundle.price)
                except Exception:
                    base_price = Decimal(bundle.price)

                # entry["price"] may be a string; convert robustly, default to base_price
                try:
                    discounted_price = Decimal(entry.get("price", base_price))
                except Exception:
                    discounted_price = base_price

                subtotal = discounted_price * quantity

                bundle_discount_total += base_price * quantity * Decimal("0.10")
                discount_percent = (
                    (base_price - discounted_price) / base_price * Decimal("100.00")
                    if base_price > 0 and discounted_price < base_price
                    else Decimal("0.00")
                )

                items.append({
                    "product": None,
                    "bundle":  bundle,
                    "quantity": quantity,
                    "unit_price": base_price,
                    "discounted_price": discounted_price,
                    "discount_percent": discount_percent,
                    "subtotal": subtotal,
                    "tier": getattr(bundle, "bundle_type", None),
                    "is_bundle": True,
                })
                total += subtotal
                continue
            # --- otherwise treat as a normal Product entry ---
            prod_id = entry.get("product_id")
            if not prod_id:
                continue
            try:
                product = Product.objects.get(pk=prod_id)
            except Product.DoesNotExist:
                continue

            quantity = entry.get("quantity", 0)
            unit_price = product.price
            discounted_price = Decimal(entry.get("price", unit_price))
            subtotal = discounted_price * quantity

            # accumulate bundle discount if this ProductType is actually a bundle
            is_bundle = is_bundle_product(product)
            if is_bundle:
                bundle_discount_total += unit_price * quantity * Decimal("0.10")

            discount_percent = (
                (unit_price - discounted_price) / unit_price * Decimal("100.00")
                if unit_price > 0 and discounted_price < unit_price
                else Decimal("0.00")
            )

            items.append({
                "product": product,
                "bundle": None,
                "quantity": quantity,
                "unit_price": unit_price,
                "discounted_price": discounted_price,
                "discount_percent": discount_percent,
                "subtotal": subtotal,
                "tier": product.tier,
                "is_bundle": is_bundle,
            })
            total += subtotal

    # 3) apply bundle & first-time discounts
    total_before_discount = total
    total -= bundle_discount_total

    if request.user.is_authenticated and is_first_time_user(request.user):
        first_time_discount = True
        cart_discount_total = total * Decimal("0.10")
        total -= cart_discount_total

    # 4) delivery fee & grand total
    delivery_fee = Decimal("0.00") if (
        first_time_discount or total_before_discount >= Decimal("40.00")
    ) else Decimal("4.99")

    grand_total = total + delivery_fee
    estimated_delivery = date.today() + timedelta(days=2)
    total_saved = bundle_discount_total + cart_discount_total

    logger.debug(
        f"[CART] Items:{len(items)} Sub:{total_before_discount:.2f} "
        f"BundleDisc:{bundle_discount_total:.2f} "
        f"FirstTimeDisc:{cart_discount_total:.2f} "
        f"Final:{total:.2f} Delivery:{delivery_fee:.2f} "
        f"Grand:{grand_total:.2f}"
    )

    return {
        "cart_items": items,
        "cart_type": cart_type,
        "cart_total": total,
        "total_before_discount": total_before_discount,
        "bundle_discount": bundle_discount_total,
        "cart_discount": cart_discount_total,
        "first_time_discount": first_time_discount,
        "free_delivery": delivery_fee == 0,
        "delivery_fee": delivery_fee,
        "grand_total": grand_total,
        "estimated_delivery": estimated_delivery,
        "total_saved": total_saved,
    }
