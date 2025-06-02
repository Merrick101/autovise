# apps/products/management/commands/load_sample_products.py

from django.core.management.base import BaseCommand
from apps.products.models import Product, Category, ProductType, Tag, Bundle, ProductBundle
from django.utils.text import slugify
from django.utils import timezone
import random
import uuid


class Command(BaseCommand):
    help = "Load sample products, categories, types, tags, and a bundle for development/testing."

    def handle(self, *args, **kwargs):
        # Create Categories
        accessories, _ = Category.objects.get_or_create(name="Accessories", slug="accessories")
        cleaning, _ = Category.objects.get_or_create(name="Cleaning & Care", slug="cleaning-care")

        # Create Product Types
        type_accessory, _ = ProductType.objects.get_or_create(name="Accessory")
        type_cleaner, _ = ProductType.objects.get_or_create(name="Cleaner")

        # Create Tags
        tag1, _ = Tag.objects.get_or_create(name="Best Seller")
        tag2, _ = Tag.objects.get_or_create(name="New Arrival")

        # Sample Products
        sample_products = [
            {
                "name": "Seat Organizer",
                "variant": "Compact",
                "tier": "Standard",
                "category": accessories,
                "type": type_accessory,
                "price": 9.99,
                "stock": 25,
                "image_type": "#A2"
            },
            {
                "name": "Phone Mount",
                "variant": "Dashboard Clip",
                "tier": "Pro",
                "category": accessories,
                "type": type_accessory,
                "price": 14.99,
                "stock": 15,
                "image_type": "#E7"
            },
            {
                "name": "Vent Clip Air Freshener",
                "variant": "Vanilla Breeze",
                "tier": "Standard",
                "category": accessories,
                "type": type_accessory,
                "price": 3.49,
                "stock": 50,
                "image_type": "#A1"
            },
            {
                "name": "Glass Cleaner Spray",
                "variant": "500ml",
                "tier": "Standard",
                "category": cleaning,
                "type": type_cleaner,
                "price": 5.99,
                "stock": 30,
                "image_type": "#C2"
            },
            {
                "name": "Interior Detail Kit",
                "variant": "Pro Bundle",
                "tier": "Pro",
                "category": cleaning,
                "type": type_cleaner,
                "price": 19.99,
                "stock": 10,
                "image_type": "#C9"
            },
            {
                "name": "Leather Cleaner",
                "variant": "Spray Foam",
                "tier": "Pro",
                "category": cleaning,
                "type": type_cleaner,
                "price": 11.99,
                "stock": 20,
                "image_type": "#C3"
            },
        ]

        created_products = []
        for entry in sample_products:
            slug = slugify(f"{entry['name']}-{entry['variant']}")
            sku = str(uuid.uuid4())[:8].upper()
            code = f"TEST-{random.randint(1000, 9999)}"
            product, created = Product.objects.get_or_create(
                name=entry["name"],
                variant=entry["variant"],
                defaults={
                    "description": f"Sample product: {entry['name']} - {entry['variant']}",
                    "slug": slug,
                    "type": entry["type"],
                    "tier": entry["tier"],
                    "category": entry["category"],
                    "price": entry["price"],
                    "image": "product_images/sample.jpg",  # Placeholder path
                    "stock": entry["stock"],
                    "sku": sku,
                    "product_code": code,
                    "image_type": entry["image_type"],
                    "created_at": timezone.now(),
                    "updated_at": timezone.now()
                }
            )
            if created:
                product.tags.add(tag1, tag2)
                created_products.append(product)
                self.stdout.write(self.style.SUCCESS(f"Created: {product.name} ({product.variant})"))

        # Create Bundle and link 3 products
        if created_products:
            bundle, _ = Bundle.objects.get_or_create(
                name="Starter Accessory Pack",
                defaults={
                    "description": "Sample bundle of useful accessories",
                    "discount_percentage": 10.00,
                    "price": 25.00,
                    "created_at": timezone.now(),
                    "updated_at": timezone.now()
                }
            )
            for p in created_products[:3]:
                ProductBundle.objects.get_or_create(product=p, bundle=bundle)
            self.stdout.write(self.style.SUCCESS(f"Created bundle: {bundle.name} with {bundle.products.count()} products"))

        self.stdout.write(self.style.SUCCESS("Sample data loading complete."))
