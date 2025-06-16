# apps/pages/views.py

from django.shortcuts import render
from apps.products.models import Product, Bundle
from django.views.decorators.http import require_POST
from django.shortcuts import redirect
from .forms import NewsletterForm


def home(request):
    context = {
        'promo_banner': "🎁 Free Delivery on First-Time Orders | 🚚 Orders over £40 ship free",
        'featured_bundles': Bundle.objects.all()[:4],
        'popular_products': Product.objects.all()[:4],
    }
    return render(request, 'pages/home.html', context)


@require_POST
def subscribe_newsletter(request):
    form = NewsletterForm(request.POST)
    if form.is_valid():
        form.save()
    return redirect(request.META.get("HTTP_REFERER", "/"))


def privacy_policy(request):
    return render(request, 'pages/privacy.html')


def terms_and_conditions(request):
    return render(request, 'pages/terms.html')


def contact(request):
    return render(request, 'pages/contact.html')
