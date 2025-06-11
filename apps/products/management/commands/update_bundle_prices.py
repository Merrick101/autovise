# products/management/commands/update_bundle_prices.py

from django.core.management.base import BaseCommand
from decimal import Decimal
from apps.products.models import Bundle


class Command(BaseCommand):
    help = "Update subtotal and discounted prices for all bundles"

    def handle(self, *args, **kwargs):
        updated = 0
        for bundle in Bundle.objects.all():
            total = sum(p.price for p in bundle.products.all())
            discount = bundle.discount_percentage or Decimal('10.0')
            bundle.subtotal_price = total
            bundle.price = round(total * (Decimal('1.00') - discount / Decimal('100.00')), 2)
            bundle.save()
            updated += 1

        self.stdout.write(self.style.SUCCESS(f"Updated {updated} bundles."))
