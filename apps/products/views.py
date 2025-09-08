"""
Views for handling product and bundle listings, details, reviews,
and filtering in the e-commerce application.
Located at apps/products/views.py
"""

from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.db.models import Q
from .models import Product, Bundle, Category, Review
from .forms import ReviewForm


def product_list_view(request):
    # 1) Read all query-params
    category_slug = request.GET.get("category")
    sort_param = request.GET.get("sort")
    tier_param = request.GET.get("tier")
    search_q = request.GET.get("q", "").strip()
    page_number = request.GET.get("page", 1)

    # 2) Base queryset
    qs = Product.objects.filter(is_draft=False)

    # 3) Search filter
    if search_q:
        qs = qs.filter(name__icontains=search_q)
        qs = qs.filter(
            Q(name__icontains=search_q) |
            Q(variant__icontains=search_q) |
            Q(type__name__icontains=search_q)
        )

    # 4) Category filter
    if category_slug:
        qs = qs.filter(category__slug=category_slug)

    # 5) Tier filter (single‐select)
    if tier_param in ("Standard", "Pro"):
        qs = qs.filter(tier=tier_param)

    # 6) Price sort
    if sort_param == "price_asc":
        qs = qs.order_by("price")
    elif sort_param == "price_desc":
        qs = qs.order_by("-price")

    # 7) Paginate (20 per page)
    paginator = Paginator(qs, 20)
    try:
        page_obj = paginator.page(page_number)
    except (PageNotAnInteger, EmptyPage):
        page_obj = paginator.page(1)

    # 8) Build context
    context = {
        "products":         page_obj.object_list,
        "page_obj":         page_obj,
        "categories":       Category.objects.all(),
        "selected_category": category_slug,
        "selected_tier":    tier_param,
        "selected_sort":    sort_param,
        "search_q":         search_q,
    }

    # 9) Render
    return render(request, "products/product_list.html", context)


def product_detail_view(request, pk):
    product = get_object_or_404(Product, pk=pk)
    reviews = product.reviews.select_related('user').all()
    user_review = None
    review_form = None

    if request.user.is_authenticated:
        try:
            user_review = product.reviews.get(user=request.user)
        except Review.DoesNotExist:
            if request.method == "POST":
                review_form = ReviewForm(request.POST)
                if review_form.is_valid():
                    new_review = review_form.save(commit=False)
                    new_review.product = product
                    new_review.user = request.user
                    new_review.save()
                    messages.success(request, "Your review has been submitted.")
                    return redirect('products:product_detail', pk=product.id)
            else:
                review_form = ReviewForm()

    context = {
        'product': product,
        'reviews': reviews,
        'user_review': user_review,
        'review_form': review_form,
    }
    return render(request, 'products/product_detail.html', context)


def bundle_list_view(request):
    bundle_type = request.GET.get('type')  # e.g. "Standard", "Pro", "Special"
    sort_param = request.GET.get('sort')  # "price_asc" or "price_desc"
    search_q = request.GET.get('q', '').strip()  # navbar search query

    # 1) Base queryset & type filter
    qs = Bundle.objects.all()
    if bundle_type in ["Standard", "Pro", "Special"]:
        qs = qs.filter(bundle_type=bundle_type)

    # 2) Global navbar search
    if search_q:
        qs = qs.filter(
            Q(name__icontains=search_q) |
            Q(description__icontains=search_q)
        )

    # 3) Price sorting
    if sort_param == "price_asc":
        qs = qs.order_by("price")
    elif sort_param == "price_desc":
        qs = qs.order_by("-price")

    # 4) Build context
    context = {
        'bundles': qs,
        'active_filter': bundle_type,
        'selected_sort': sort_param,
        'search_q': "",   # clears the search input after submit
        'promo_banner': "💡 10% Off All Bundles — Discount Applied Automatically",
    }
    return render(request, 'products/bundle_list.html', context)


def bundle_detail_view(request, bundle_id):
    bundle = get_object_or_404(Bundle, id=bundle_id)
    reviews = bundle.reviews.select_related('user').all()
    user_review = None
    review_form = None

    if request.user.is_authenticated:
        try:
            user_review = bundle.reviews.get(user=request.user)
        except Review.DoesNotExist:
            if request.method == "POST":
                review_form = ReviewForm(request.POST)
                if review_form.is_valid():
                    new_review = review_form.save(commit=False)
                    new_review.bundle = bundle
                    new_review.user = request.user
                    new_review.save()
                    messages.success(request, "Your review has been submitted.")
                    return redirect('products:bundle_detail', bundle_id=bundle.id)
            else:
                review_form = ReviewForm()

    context = {
        'bundle': bundle,
        'reviews': reviews,
        'user_review': user_review,
        'review_form': review_form,
    }
    return render(request, 'products/bundle_detail.html', context)


@staff_member_required
def review_update_view(request, review_id):
    review = get_object_or_404(Review, pk=review_id)
    if request.method == "POST":
        form = ReviewForm(request.POST, instance=review)
        if form.is_valid():
            form.save()
            messages.success(request, "Review updated.")
            # redirect back to the relevant detail with anchor
            if review.product_id:
                return redirect('products:product_detail', pk=review.product_id)
            return redirect('products:bundle_detail', bundle_id=review.bundle_id)
    else:
        form = ReviewForm(instance=review)
    ctx = {"form": form, "review": review}
    return render(request, "products/review_form.html", ctx)


@staff_member_required
def review_delete_view(request, review_id):
    review = get_object_or_404(Review, pk=review_id)
    if request.method == "POST":
        pid, bid = review.product_id, review.bundle_id
        review.delete()
        messages.success(request, "Review deleted.")
        if pid:
            return redirect('products:product_detail', pk=pid)
        return redirect('products:bundle_detail', bundle_id=bid)
    # simple confirm page (optional)
    return render(request, "products/review_confirm_delete.html", {"review": review})
