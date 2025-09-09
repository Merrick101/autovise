"""
Sitemaps for products, categories, product types, and bundles.
These sitemaps help search engines index the product-related pages effectively.
Located at apps/products/sitemaps.py
"""

from django.contrib.sitemaps import Sitemap
from django.urls import reverse
from .models import Product, Category, ProductType, Bundle


class ProductSitemap(Sitemap):
    changefreq = "weekly"
    priority = 0.9

    def items(self):
        # Only public products
        return Product.objects.filter(is_draft=False).order_by("pk")

    def location(self, item):
        # Uses Product.get_absolute_url (pk-based)
        return item.get_absolute_url()

    def lastmod(self, item):
        return item.updated_at


class CategorySitemap(Sitemap):
    changefreq = "monthly"
    priority = 0.6

    def items(self):
        # Categories that actually have public products
        return Category.objects.filter(products__is_draft=False).distinct().order_by("pk")

    def location(self, item):
        # Filter categories via a query param in product_list
        return f"{reverse('products:product_list')}?category={item.slug}"


class ProductTypeSitemap(Sitemap):
    changefreq = "monthly"
    priority = 0.5

    def items(self):
        return ProductType.objects.all().order_by("pk")

    def location(self, item):
        return f"{reverse('products:product_list')}?q={item.name}"


class BundleSitemap(Sitemap):
    changefreq = "monthly"
    priority = 0.7

    def items(self):
        return Bundle.objects.all().order_by("pk")

    def location(self, item):
        # Your bundle detail uses numeric ID, not slug
        return reverse("products:bundle_detail", kwargs={"bundle_id": item.pk})

    def lastmod(self, item):
        return item.updated_at
