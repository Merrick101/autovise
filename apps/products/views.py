# apps/products/views.py

from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from django.shortcuts import render, get_object_or_404
from .models import Product, Bundle, Category


def product_list_view(request):
    # 1) Read all query-params
    category_slug = request.GET.get("category")
    sort_param = request.GET.get("sort")
    tier_param = request.GET.get("tier")
    page_number = request.GET.get("page", 1)

    # 2) Base queryset
    qs = Product.objects.filter(is_draft=False)

    # 3) Category filter
    if category_slug:
        qs = qs.filter(category__slug=category_slug)

    # 4) Tier filter (single‐select)
    if tier_param in ("Standard", "Pro"):
        qs = qs.filter(tier=tier_param)

    # 5) Price sort
    if sort_param == "price_asc":
        qs = qs.order_by("price")
    elif sort_param == "price_desc":
        qs = qs.order_by("-price")

    # 6) Paginate (20 per page)
    paginator = Paginator(qs, 20)
    try:
        page_obj = paginator.page(page_number)
    except (PageNotAnInteger, EmptyPage):
        page_obj = paginator.page(1)

    # 7) Build context
    context = {
        "products":         page_obj.object_list,
        "page_obj":         page_obj,
        "categories":       Category.objects.all(),
        "selected_category": category_slug,
        "selected_tier":    tier_param,
        "selected_sort":    sort_param,
    }

    # 8) Render
    return render(request, "products/product_list.html", context)


def product_detail_view(request, pk):
    product = get_object_or_404(Product, pk=pk)
    return render(
        request, 'products/product_detail.html', {'product': product}
    )


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
