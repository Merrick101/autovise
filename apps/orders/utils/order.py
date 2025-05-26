# apps/orders/utils/order.py

def create_order_from_stripe_session(session):
    print("Received Stripe session:", session['id'])  # Debug placeholder
