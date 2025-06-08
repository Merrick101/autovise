# apps/products/views.py

from django.shortcuts import render, get_object_or_404
from .models import Product, Bundle


def product_list_view(request):
    products = Product.objects.all()
    return render(request, 'products/product_list.html', {'products': products})


def product_detail_view(request, pk):
    product = get_object_or_404(Product, pk=pk)
    return render(request, 'products/product_detail.html', {'product': product})


def bundle_list_view(request):
    bundles = Bundle.objects.all()
    return render(request, 'products/bundle_list.html', {'bundles': bundles})
