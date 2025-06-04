# apps/products/forms.py

from django import forms
from django.core.exceptions import ValidationError
from .models import Bundle


class BundleAdminForm(forms.ModelForm):
    class Meta:
        model = Bundle
        fields = '__all__'

    def clean(self):
        cleaned_data = super().clean()
        bundle = self.instance
        if bundle.pk and bundle.products.count() < 3:
            raise ValidationError("A bundle must contain at least 3 products.")
        return cleaned_data
