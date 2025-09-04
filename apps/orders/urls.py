# apps/orders/urls.py

from django.urls import include, path
from apps.orders.views.cart_views import (
    add_to_cart_view, add_bundle_to_cart_view, cart_view, update_quantity, remove_item, clear_cart
)
from apps.orders.views.checkout import checkout_view
from apps.orders.views import payment
from apps.orders.views import webhook as webhook_views
from apps.orders.views.general import checkout_success_view, order_history_view, checkout_cancel_view

app_name = 'orders'

urlpatterns = [
    path('add-to-cart/<int:product_id>/', add_to_cart_view, name='add_to_cart'),
    path('cart/add_bundle/<int:bundle_id>/', add_bundle_to_cart_view, name='add_bundle_to_cart'),
    path('cart/', cart_view, name='cart'),
    path("update/<str:item_key>/", update_quantity, name="update_quantity"),
    path("remove/<str:item_key>/", remove_item, name="remove_item"),
    path('cart/clear/', clear_cart, name='clear_cart'),
    path("payments/create-intent/", payment.create_payment_intent, name="create_payment_intent"),
    path('checkout/', checkout_view, name='checkout'),
    path('orders/success/', checkout_success_view, name='success'),
    path("checkout/cancel/", checkout_cancel_view, name="checkout_cancel"),
    path('order-history/', order_history_view, name='order_history'),
    path("payments/webhook/", webhook_views.stripe_webhook_view, name="webhook"),
]
