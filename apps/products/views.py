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
    bundle_type = request.GET.get('type')  # e.g., "Pro", "Special", etc.

    if bundle_type in ["Standard", "Pro", "Special"]:
        bundles = Bundle.objects.filter(bundle_type=bundle_type)
    else:
        bundles = Bundle.objects.all()

    context = {
        'bundles': bundles,
        'active_filter': bundle_type,
        'promo_banner': "💡 10% Off All Bundles — Discount Applied Automatically"
    }
    return render(request, 'products/bundle_list.html', context)


def bundle_detail_view(request, bundle_id):
    bundle = get_object_or_404(Bundle, id=bundle_id)
    return render(request, 'products/bundle_detail.html', {'bundle': bundle})
