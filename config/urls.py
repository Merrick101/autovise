# config/urls.py

from django.contrib import admin
from django.urls import path, include
from django.views.generic import TemplateView
from apps.pages.views import home
from apps.orders.views.webhook import stripe_webhook_view
from config.views_sitemap import sitemap_index_xml, sitemap_section_xml
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
    path('products/', include('apps.products.urls', namespace='products')),
    path('orders/', include('apps.orders.urls', namespace='orders')),
    path('users/', include('apps.users.urls', namespace='users')),
    path('pages/', include('apps.pages.urls', namespace='pages')),
    path("orders/webhook/", stripe_webhook_view, name="stripe_webhook"),
    # Robots.txt
    path("robots.txt", TemplateView.as_view(template_name="robots.txt", content_type="text/plain")),
    path(
        "sitemap.xml",
        sitemap_index_xml,
        {"sitemaps": sitemaps, "sitemap_url_name": "sitemap_section"},
        name="sitemap",
    ),
    path(
        "sitemap-<section>.xml",
        sitemap_section_xml,
        {"sitemaps": sitemaps},
        name="sitemap_section",
    ),
]

# Custom error handlers
handler404 = "apps.pages.views.custom_404"
handler500 = "apps.pages.views.custom_500"
