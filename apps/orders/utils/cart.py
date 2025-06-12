# apps/orders/utils/cart.py

from apps.orders.models import Cart, CartItem
from apps.products.models import Product
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
    total = 0
    bundle_discount_total = 0
    cart_discount_total = 0
    first_time_discount = False

    def is_bundle(product):
        return product.type and product.type.name.lower() == "bundle"

    if cart_type == 'db':
        for item in cart_data.items.select_related('product'):
            product = item.product
            subtotal = item.quantity * product.price
            if is_bundle(product):
                bundle_discount_total += subtotal * 0.10
            items.append({
                'product': product,
                'quantity': item.quantity,
                'subtotal': subtotal,
                'tier': product.tier,
                'is_bundle': True if is_bundle(product) else False,
            })
            total += subtotal
    else:
        for _, item in cart_data.items():
            try:
                product = Product.objects.get(id=item['product_id'])
            except Product.DoesNotExist:
                continue
            subtotal = item['quantity'] * product.price
            if is_bundle(product):
                bundle_discount_total += subtotal * 0.10
            items.append({
                'product': product,
                'quantity': item['quantity'],
                'subtotal': subtotal,
                'tier': product.tier,
                'is_bundle': is_bundle(product),
            })
            total += subtotal

    total_before_discount = total
    total -= bundle_discount_total

    if request.user.is_authenticated and is_first_time_user(request.user):
        first_time_discount = True
        cart_discount_total = total * 0.10
        total -= cart_discount_total

    delivery_fee = 4.99
    free_delivery = first_time_discount or total_before_discount >= 40
    if free_delivery:
        delivery_fee = 0.00

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
