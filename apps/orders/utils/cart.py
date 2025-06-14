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
    Returns structured summary dictionary for use in views.
    """

    items = []
    total = Decimal("0.00")
    bundle_discount_total = Decimal("0.00")
    cart_discount_total = Decimal("0.00")
    first_time_discount = False

    def is_bundle_product(product):
        return product.type and product.type.name.lower() == "bundle"

    if cart_type == 'db':
        for item in cart_data.items.select_related('product'):
            product = item.product
            quantity = item.quantity
            unit_price = product.price
            subtotal = Decimal(quantity) * unit_price

            if is_bundle_product(product):
                bundle_discount_total += subtotal * Decimal("0.10")

            discounted_price = subtotal / quantity if quantity > 0 else unit_price
            discount_percent = ((unit_price - discounted_price) / unit_price * Decimal("100.00")) if unit_price > 0 and discounted_price < unit_price else Decimal("0.00")

            items.append({
                'product': product,
                'quantity': quantity,
                'subtotal': subtotal,
                'tier': product.tier,
                'is_bundle': is_bundle_product(product),
                'unit_price': unit_price,
                'discounted_price': discounted_price,
                'discount_percent': discount_percent,
            })

            total += subtotal

    else:
        for key, item in cart_data.items():
            if item.get('type') == 'bundle':
                try:
                    bundle_id = int(key.split('_')[1])  # from "bundle_7"
                    bundle = Bundle.objects.get(id=bundle_id)
                    quantity = item['quantity']
                    unit_price = Decimal(bundle.subtotal_price)
                    discounted_price = Decimal(item['price'])
                    subtotal = Decimal(quantity) * discounted_price
                    discount_percent = ((unit_price - discounted_price) / unit_price * Decimal("100.00")) if unit_price > 0 and discounted_price < unit_price else Decimal("0.00")

                    items.append({
                        'product': bundle,
                        'quantity': quantity,
                        'subtotal': subtotal,
                        'tier': bundle.bundle_type,
                        'is_bundle': True,
                        'unit_price': unit_price,
                        'discounted_price': discounted_price,
                        'discount_percent': discount_percent,
                    })

                    total += subtotal
                except (IndexError, ValueError, Bundle.DoesNotExist):
                    continue
                continue

            try:
                product_id = item.get('product_id')
                if not product_id:
                    continue
                product = Product.objects.get(id=product_id)
                quantity = item['quantity']
                unit_price = product.price
                discounted_price = Decimal(item.get('price', unit_price))
                subtotal = Decimal(quantity) * discounted_price
                is_bundle = is_bundle_product(product)

                if is_bundle:
                    bundle_discount_total += subtotal * Decimal("0.10")

                discount_percent = ((unit_price - discounted_price) / unit_price * Decimal("100.00")) if unit_price > 0 and discounted_price < unit_price else Decimal("0.00")

                items.append({
                    'product': product,
                    'quantity': quantity,
                    'subtotal': subtotal,
                    'tier': product.tier,
                    'is_bundle': is_bundle,
                    'unit_price': unit_price,
                    'discounted_price': discounted_price,
                    'discount_percent': discount_percent,
                })

                total += subtotal

            except (Product.DoesNotExist, KeyError):
                continue

    total_before_discount = total
    total -= bundle_discount_total

    if request.user.is_authenticated and is_first_time_user(request.user):
        first_time_discount = True
        cart_discount_total = total * Decimal("0.10")
        total -= cart_discount_total

    delivery_fee = Decimal("4.99")
    free_delivery = first_time_discount or total_before_discount >= Decimal("40.00")
    if free_delivery:
        delivery_fee = Decimal("0.00")

    grand_total = total + delivery_fee
    estimated_delivery = date.today() + timedelta(days=2)

    logger.debug(
        f"[CART] Items: {len(items)} | "
        f"Subtotal: {total_before_discount:.2f} | "
        f"Bundle Discount: {bundle_discount_total:.2f} | "
        f"First-Time Discount: {cart_discount_total:.2f} | "
        f"Final: {total:.2f} | Delivery: {delivery_fee:.2f} | Grand: {grand_total:.2f}"
    )

    return {
        'cart_items': items,
        'cart_type': cart_type,
        'cart_total': total,
        'total_before_discount': total_before_discount,
        'bundle_discount': bundle_discount_total,
        'cart_discount': cart_discount_total,
        'first_time_discount': first_time_discount,
        'free_delivery': free_delivery,
        'delivery_fee': delivery_fee,
        'grand_total': grand_total,
        'estimated_delivery': estimated_delivery,
    }
