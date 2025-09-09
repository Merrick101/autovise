"""
Sitemaps for products, categories, product types, and bundles.
These sitemaps help search engines index the product-related pages effectively.
Located at apps/products/sitemaps.py
"""

from django.contrib.sitemaps import Sitemap
from django.urls import reverse
from .models import Product, Category, Bundle


class ProductSitemap(Sitemap):
    changefreq = "weekly"
    priority = 0.9

    def items(self):
        # Only index public products
        return Product.objects.filter(is_draft=False)

    def lastmod(self, obj):
        return obj.updated_at

    def location(self, obj):
        # /products/<pk>/
        return reverse("products:product_detail", kwargs={"pk": obj.pk})


class BundleSitemap(Sitemap):
    changefreq = "weekly"
    priority = 0.7

    def items(self):
        return Bundle.objects.all()

    def lastmod(self, obj):
        return obj.updated_at

    def location(self, obj):
        # /products/bundles/<bundle_id>/
        return reverse("products:bundle_detail", kwargs={"bundle_id": obj.pk})


class CategorySitemap(Sitemap):
    changefreq = "weekly"
    priority = 0.6

    def items(self):
        # Limit to categories that actually have (public) products
        return Category.objects.filter(products__is_draft=False).distinct()

    def location(self, obj):
        # Link to the product list filtered by category query param
        base = reverse("products:product_list")
        return f"{base}?category={obj.slug}"
