# orders/views.py

from django.shortcuts import redirect, get_object_or_404
from django.contrib import messages
from apps.products.models import Product
from orders.utils.cart import add_to_cart


def add_to_cart_view(request, product_id):
    product = get_object_or_404(Product, id=product_id)

    if request.method == 'POST':
        quantity = int(request.POST.get('quantity', 1))
        add_to_cart(request, product_id, quantity)
        messages.success(request, f"Added {product.name} to your cart.")

    return redirect(request.META.get('HTTP_REFERER', 'products:product_list'))
