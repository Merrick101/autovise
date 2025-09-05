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
    pre_total = Decimal("0.00")
    post_total = Decimal("0.00")

    bundle_discount_total = Decimal("0.00")  # only for display
    cart_discount_total = Decimal("0.00")
    first_time_discount = False

    def is_bundle_product(product):
        return product.type and product.type.name.lower() == "bundle"

    # 1) DB-backed cart
    if cart_type == "db":
        for ci in cart_data.items.select_related("product"):
            product = ci.product
            quantity = int(ci.quantity or 0)
            if quantity <= 0:
                continue

            unit_price = Decimal(product.price).quantize(Decimal("0.01"))
            discounted_unit = unit_price  # no implicit product discounts in DB cart

            line_unit_total = unit_price * quantity
            line_disc_total = discounted_unit * quantity
            line_discount_amount = (
               (line_unit_total - line_disc_total) if line_disc_total < line_unit_total else Decimal("0.00")
            )

            discount_percent = Decimal("0.00")
            is_bundle = False  # DB cart contains Products, not Bundles

            items.append({
                "product": product,
                "bundle":  None,
                "quantity": quantity,
                "unit_price": unit_price,
                "discounted_price": discounted_unit,
                "discount_percent": discount_percent,
                "subtotal": line_disc_total,
                "line_subtotal_before_discount": line_unit_total,
                "line_subtotal_after_discount": line_disc_total,
                "line_discount_amount": line_discount_amount,
                "tier": product.tier,
                "is_bundle": is_bundle,
            })

            pre_total += line_unit_total
            post_total += line_disc_total

    # 2) Session-backed cart
    else:
        for key, entry in (cart_data or {}).items():
            # --- bundle entry if key starts with "bundle_"
            if isinstance(key, str) and key.startswith("bundle_"):
                try:
                    bundle_id = int(key.split("_", 1)[1])
                    bundle = Bundle.objects.get(pk=bundle_id)
                except (ValueError, Bundle.DoesNotExist):
                    continue

                try:
                    quantity = int(entry.get("quantity", 0) or 0)
                except (TypeError, ValueError):
                    quantity = 0
                if quantity <= 0:
                    continue

                # Prefer model fields
                raw_base = getattr(bundle, "subtotal_price", None)
                raw_disc_pct = getattr(bundle, "discount_percentage", Decimal("10.00"))

                try:
                    base_price = Decimal(raw_base) if raw_base is not None else Decimal(bundle.price)
                except Exception:
                    base_price = Decimal(bundle.price)

                # derive discount percent (e.g. 10.00 -> 0.10)
                try:
                    disc_pct = (Decimal(raw_disc_pct) / Decimal("100")).quantize(Decimal("0.0001"))
                except Exception:
                    disc_pct = Decimal("0.10")

                # discounted unit: prefer session-provided price, else model price, else base*(1-disc)
                if entry.get("price") is not None:
                    try:
                        discounted_unit = Decimal(entry["price"])
                    except Exception:
                        discounted_unit = base_price * (Decimal("1.00") - disc_pct)
                else:
                    try:
                        discounted_unit = Decimal(bundle.price)
                    except Exception:
                        discounted_unit = base_price * (Decimal("1.00") - disc_pct)

                # normalise
                base_price = base_price.quantize(Decimal("0.01"))
                discounted_unit = discounted_unit.quantize(Decimal("0.01"))

                line_unit_total = base_price * quantity
                line_disc_total = discounted_unit * quantity
                line_discount_amount = (
                   (line_unit_total - line_disc_total) if line_disc_total < line_unit_total else Decimal("0.00")
                )

                # track discount for display/evidence
                if discounted_unit < base_price:
                    bundle_discount_total += (base_price - discounted_unit) * quantity

                discount_percent = (
                    ((base_price - discounted_unit) / base_price * Decimal("100.00"))
                    if base_price > 0 and discounted_unit < base_price
                    else Decimal("0.00")
                )

                items.append({
                    "product": None,
                    "bundle":  bundle,
                    "quantity": quantity,
                    "unit_price": base_price,
                    "discounted_price": discounted_unit,
                    "discount_percent": discount_percent,
                    "subtotal": line_disc_total,
                    "line_subtotal_before_discount": line_unit_total,
                    "line_subtotal_after_discount": line_disc_total,
                    "line_discount_amount": line_discount_amount,
                    "tier": getattr(bundle, "bundle_type", None),
                    "is_bundle": True,
                })

                pre_total += line_unit_total
                post_total += line_disc_total
                continue

            prod_id = entry.get("product_id")
            try:
                quantity = int(entry.get("quantity", 0) or 0)
            except (TypeError, ValueError):
                quantity = 0
            if not prod_id or quantity <= 0:
                continue

            try:
                product = Product.objects.get(pk=prod_id)
            except Product.DoesNotExist:
                continue

            unit_price = Decimal(product.price)

            try:
                discounted_unit = Decimal(entry.get("price", unit_price))
            except Exception:
                discounted_unit = unit_price

            discounted_unit = discounted_unit.quantize(Decimal("0.01"))
            unit_price = unit_price.quantize(Decimal("0.01"))

            line_unit_total = unit_price * quantity
            line_disc_total = discounted_unit * quantity
            line_discount_amount = (
                (line_unit_total - line_disc_total) if line_disc_total < line_unit_total else Decimal("0.00")
            )

            discount_percent = (
                ((unit_price - discounted_unit) / unit_price * Decimal("100.00"))
                if unit_price > 0 and discounted_unit < unit_price
                else Decimal("0.00")
            )

            items.append({
                "product": product,
                "bundle": None,
                "quantity": quantity,
                "unit_price": unit_price,
                "discounted_price": discounted_unit,
                "discount_percent": discount_percent,
                "subtotal": line_disc_total,
                "line_subtotal_before_discount": line_unit_total,
                "line_subtotal_after_discount": line_disc_total,
                "line_discount_amount": line_discount_amount,
                "tier": product.tier,
                "is_bundle": False,
            })

            pre_total += line_unit_total
            post_total += line_disc_total

    # 3) totals & discounts
    total_before_discount = pre_total
    total = post_total

    if request.user.is_authenticated and is_first_time_user(request.user):
        first_time_discount = True
        cart_discount_total = (total * Decimal("0.10")).quantize(Decimal("0.01"))
        total -= cart_discount_total

    # 4) delivery fee & grand total
    delivery_fee = Decimal("0.00") if (
        first_time_discount or total_before_discount >= Decimal("40.00")
    ) else Decimal("4.99")

    grand_total = (total + delivery_fee).quantize(Decimal("0.01"))
    estimated_delivery = date.today() + timedelta(days=2)
    total_saved = (bundle_discount_total + cart_discount_total).quantize(Decimal("0.01"))

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
