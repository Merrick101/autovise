# apps/orders/utils/order.py

from django.contrib.auth import get_user_model
from apps.orders.models import Order, OrderItem, Cart
from apps.products.models import Product
from django.core.mail import send_mail
from django.template.loader import render_to_string
import logging

logger = logging.getLogger(__name__)


def create_order_from_stripe_session(session):
    """
    Creates an Order instance from a completed Stripe session object.
    Handles both guest and authenticated users, cart cleanup, and email notification.
    """

    user_id = session.get('metadata', {}).get('user_id')
    User = get_user_model()
    user = None

    if user_id and user_id != "guest":
        try:
            user = User.objects.get(id=user_id)
            logger.info(f"[ORDER] Authenticated user found: {user.email}")
        except User.DoesNotExist:
            logger.warning(f"[ORDER] User ID {user_id} not found. Proceeding as guest.")
    else:
        logger.info("[ORDER] Guest checkout session detected.")

    # Create the order
    order = Order.objects.create(
        user=user,
        stripe_session_id=session['id'],
        stripe_payment_intent=session.get('payment_intent'),
        total_amount=(int(float(session['amount_total'] or 0)) / 100.0),
        is_paid=True
    )

    # Optional: extract product IDs from metadata (preferred) or session
    product_ids = session.get('metadata', {}).get('product_ids', '')
    product_ids = product_ids.split(',') if product_ids else []

    for product_id in product_ids:
        try:
            product = Product.objects.get(id=product_id)
            OrderItem.objects.create(
                order=order,
                product=product,
                quantity=1  # Assuming quantity is 1 for simplicity
            )
        except Product.DoesNotExist:
            logger.warning(f"[ORDER] Product ID {product_id} not found in DB. Skipping.")

    # Optional: clean up user cart
    if user:
        Cart.objects.filter(user=user).delete()
        profile = getattr(user, 'profile', None)
        if profile and profile.is_first_time_buyer:
            profile.is_first_time_buyer = False
            profile.save()
            logger.info(f"[PROFILE] First-time buyer flag reset for user {user}.")
    # Optional: send confirmation email
    if user and user.email:
        subject = f"Your Autovise Order #{order.id} Confirmation"
        message = render_to_string("emails/order_confirmation.txt", {
            "user": user,
            "order": order,
        })
        try:
            send_mail(
                subject,
                message,
                "no-reply@autovise.co.uk",  # From email
                [user.email],
                fail_silently=True,
            )
        except Exception as e:
            logger.error(f"[EMAIL] Failed to send confirmation to {user.email}: {e}")
