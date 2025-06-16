from django.contrib.sitemaps import Sitemap
from .models import Product, Category, ProductType, Bundle


class ProductSitemap(Sitemap):
    changefreq = "weekly"
    priority = 0.9

    def items(self):
        return Product.objects.all()

    def location(self, item):
        return item.get_absolute_url()


class CategorySitemap(Sitemap):
    changefreq = "monthly"
    priority = 0.6

    def items(self):
        return Category.objects.all()

    def location(self, item):
        return f"/products/category/{item.slug}/"


class ProductTypeSitemap(Sitemap):
    changefreq = "monthly"
    priority = 0.5

    def items(self):
        return ProductType.objects.all()

    def location(self, item):
        return f"/products/type/{item.name.lower()}/"


class BundleSitemap(Sitemap):
    changefreq = "monthly"
    priority = 0.7

    def items(self):
        return Bundle.objects.all()

    def location(self, item):
        return f"/products/bundles/{item.slug}/"
