# apps/products/forms.py

from django import forms
from decimal import Decimal
from .models import Bundle


class BundleAdminForm(forms.ModelForm):
    class Meta:
        model = Bundle
        fields = '__all__'

    def clean_discount_percentage(self):
        value = self.cleaned_data.get('discount_percentage')
        if value is None:
            return Decimal('10.0')
        return value
