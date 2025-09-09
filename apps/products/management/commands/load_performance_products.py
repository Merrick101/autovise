from django.core.management.base import BaseCommand
from django.utils.text import slugify
from django.utils import timezone
from apps.products.models import Product, Category, ProductType
from decimal import Decimal, InvalidOperation

FILE_PATH = "products_performance.txt"


class Command(BaseCommand):
    help = "Load Performance products from a structured text file"

    def handle(self, *args, **kwargs):
        try:
            category, _ = Category.objects.get_or_create(name="Performance", slug="performance")
        except Exception as e:
            self.stderr.write(self.style.ERROR(f"Category error: {str(e)}"))
            return

        created_count = 0
        current_product = {}

        try:
            with open(FILE_PATH, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue  # skip empty lines

                    if line.startswith("Name:"):
                        if current_product:
                            self.create_product(current_product, category)
                            created_count += 1
                            current_product = {}
                        current_product['name'] = line.split("Name:")[1].strip()
                    elif line.startswith("Variant:"):
                        current_product['variant'] = line.split("Variant:")[1].strip()
                    elif line.startswith("Type:"):
                        current_product['type'] = line.split("Type:")[1].strip()
                    elif line.startswith("Tier:"):
                        current_product['tier'] = line.split("Tier:")[1].strip()
                    elif line.startswith("Price:"):
                        price_str = line.split("Price:")[1].strip().replace('£', '')
                        try:
                            current_product['price'] = Decimal(price_str)
                        except InvalidOperation:
                            self.stderr.write(f"Invalid price for {current_product.get('name', 'UNKNOWN')}")
                            continue
                    elif line.startswith("Product Code:"):
                        current_product['product_code'] = line.split("Product Code:")[1].strip()
                    elif line.startswith("SKU:"):
                        current_product['sku'] = line.split("SKU:")[1].strip()

                if current_product:
                    self.create_product(current_product, category)
                    created_count += 1

            self.stdout.write(self.style.SUCCESS(f"Successfully imported {created_count} Performance products."))

        except FileNotFoundError:
            self.stderr.write(self.style.ERROR(f"File not found: {FILE_PATH}"))

    def create_product(self, data, category):
        product_type, _ = ProductType.objects.get_or_create(name=data['type'])
        stock = 50 if data['tier'] == "Standard" else 20
        slug = slugify(data['name'])

        Product.objects.update_or_create(
            sku=data['sku'],  # match by unique SKU to avoid duplicates
            defaults={
                "name": data['name'],
                "variant": data['variant'],
                "slug": slug,
                "type": product_type,
                "tier": data['tier'],
                "category": category,
                "price": data['price'],
                "stock": stock,
                "product_code": data['product_code'],
                "created_at": timezone.now(),
                "updated_at": timezone.now(),
            }
        )
