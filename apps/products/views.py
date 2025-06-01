# apps/products/views.py

from django.shortcuts import render
from .models import Product, Bundle


def product_list_view(request):
    products = Product.objects.all()
    return render(request, 'products/product_list.html', {'products': products})


def bundle_list_view(request):
    bundles = Bundle.objects.all()
    return render(request, 'products/bundle_list.html', {'bundles': bundles})
