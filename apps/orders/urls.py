# orders/urls.py

from django.urls import path
from . import views

app_name = 'orders'

urlpatterns = [
    path('add-to-cart/<int:product_id>/', views.add_to_cart_view, name='add_to_cart'),
]
