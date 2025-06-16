# config/urls.py

from django.contrib import admin
from django.urls import path, include
from apps.pages.views import home
from apps.orders.views.webhook import stripe_webhook_view
from django.contrib.sitemaps.views import sitemap
from apps.products.sitemaps import (
    ProductSitemap,
    CategorySitemap,
    ProductTypeSitemap,
    BundleSitemap,
)

sitemaps = {
    'products': ProductSitemap,
    'categories': CategorySitemap,
    'product_types': ProductTypeSitemap,
    'bundles': BundleSitemap,
}

urlpatterns = [
    # Homepage
    path('', home, name='home'),
    # Admin URL
    path('admin/', admin.site.urls),
    # Allauth URLs
    path('accounts/', include('allauth.urls')),
    # Placeholder routes for each core app
    path('products/', include('apps.products.urls')),
    path('orders/', include('apps.orders.urls', namespace='orders')),
    path('users/', include('apps.users.urls')),
    path('pages/', include('apps.pages.urls', namespace='pages')),
    path('assets/', include('apps.assets.urls')),
    path("orders/webhook/", stripe_webhook_view, name="stripe_webhook"),
    path("sitemap.xml", sitemap, {'sitemaps': sitemaps}, name='sitemap'),
]
