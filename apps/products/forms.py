# apps/products/forms.py

from django import forms
from django.core.exceptions import ValidationError
from .models import Bundle
from decimal import Decimal


class BundleAdminForm(forms.ModelForm):
    class Meta:
        model = Bundle
        fields = '__all__'

    def clean(self):
        cleaned_data = super().clean()
        discount = cleaned_data.get('discount_percentage')

        # Get all related products
        if self.instance.pk:
            products = self.instance.products.all()
        else:
            products = []

        if len(products) < 3:
            raise ValidationError("A bundle must contain at least 3 products.")

        # Calculate default 10% discount if none provided
        if discount in (None, ''):
            total_price = sum(p.price for p in products)
            auto_discount = Decimal('10.0')  # percent
            final_price = total_price * (Decimal('1.0') - auto_discount / Decimal('100'))
            cleaned_data['price'] = final_price.quantize(Decimal('0.01'))
            cleaned_data['discount_percentage'] = auto_discount

        return cleaned_data
