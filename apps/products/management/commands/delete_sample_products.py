# apps/products/management/commands/delete_sample_products.py

from django.core.management.base import BaseCommand
from apps.products.models import Product, Category, ProductType, Tag, Bundle, ProductBundle
from django.db.models import Q


class Command(BaseCommand):
    help = "Delete sample data created by the load_sample_products script."

    def handle(self, *args, **kwargs):
        # Identify sample product names (match only these exact test entries)
        sample_product_names = [
            "Seat Organizer",
            "Phone Mount",
            "Vent Clip Air Freshener",
            "Glass Cleaner Spray",
            "Interior Detail Kit",
            "Leather Cleaner"
        ]

        # Delete ProductBundle links
        bundles = Bundle.objects.filter(name="Starter Accessory Pack")
        if bundles.exists():
            ProductBundle.objects.filter(bundle__in=bundles).delete()
            bundles.delete()
            self.stdout.write(self.style.SUCCESS("Deleted sample bundle and related ProductBundle entries."))

        # Delete Products by name
        deleted_count, _ = Product.objects.filter(name__in=sample_product_names).delete()
        self.stdout.write(self.style.SUCCESS(f"Deleted {deleted_count} sample product entries."))

        # Optionally delete sample categories/types/tags (if unused)
        cleanup_tags = ["Best Seller", "New Arrival"]
        Tag.objects.filter(name__in=cleanup_tags).delete()
        ProductType.objects.filter(name__in=["Accessory", "Cleaner"]).delete()
        Category.objects.filter(slug__in=["accessories", "cleaning-care"]).delete()

        self.stdout.write(self.style.SUCCESS("Deleted sample categories, types, and tags where applicable."))
        self.stdout.write(self.style.SUCCESS("Sample data cleanup complete."))
