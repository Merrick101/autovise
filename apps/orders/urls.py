# orders/urls.py

from django.urls import path
from . import views

app_name = 'orders'

urlpatterns = [
    path('add-to-cart/<int:product_id>/', views.add_to_cart_view, name='add_to_cart'),
    path('cart/', views.cart_view, name='cart'),
    path('cart/update/<int:product_id>/', views.update_quantity, name='update_quantity'),
    path('cart/remove/<int:product_id>/', views.remove_item, name='remove_item'),
    path('cart/clear/', views.clear_cart, name='clear_cart'),
]
