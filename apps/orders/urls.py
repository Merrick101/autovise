# apps/orders/urls.py

from django.urls import path
from apps.orders.views.cart_views import (
    add_to_cart_view, cart_view, update_quantity, remove_item, clear_cart
)
from apps.orders.views.checkout import checkout_view
from apps.orders.views.webhook import stripe_webhook_view

app_name = 'orders'

urlpatterns = [
    path('add-to-cart/<int:product_id>/', add_to_cart_view, name='add_to_cart'),
    path('cart/', cart_view, name='cart'),
    path('cart/update/<int:product_id>/', update_quantity, name='update_quantity'),
    path('cart/remove/<int:product_id>/', remove_item, name='remove_item'),
    path('cart/clear/', clear_cart, name='clear_cart'),
    path('checkout/', checkout_view, name='checkout'),
    path('webhooks/stripe/', stripe_webhook_view, name='stripe_webhook'),
]
