# apps/products/forms.py

from django.core.exceptions import ValidationError
from django import forms
from decimal import Decimal
from .models import Bundle, Product


class ProductAdminForm(forms.ModelForm):
    image_path = forms.CharField(
        label="Image Path (S3 relative)",
        required=False,
        help_text="Optional: Skip file upload and directly assign S3 image path (e.g. products/accessories/filename.png)"
    )

    class Meta:
        model = Product
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.image:
            self.fields['image_path'].initial = self.instance.image.name

    def clean(self):
        cleaned_data = super().clean()
        image_path = cleaned_data.get('image_path')
        if image_path:
            # Override file upload with manual path if provided
            self.instance.image.name = image_path
        return cleaned_data


class BundleAdminForm(forms.ModelForm):
    class Meta:
        model = Bundle
        fields = '__all__'

    def clean_discount_percentage(self):
        value = self.cleaned_data.get('discount_percentage')
        return Decimal('10.0') if value is None else value

    def clean(self):
        cleaned_data = super().clean()
        bundle_type = cleaned_data.get("bundle_type")
        instance = self.instance  # only works if editing an existing bundle
        product_set = instance.products.all() if instance.pk else []

        if len(product_set) < 3:
            raise ValidationError("A bundle must include at least 3 products.")

        if bundle_type == "Pro" and not any(p.tier == "Pro" for p in product_set):
            raise ValidationError("Pro-tier bundles must include at least one Pro product.")

        if len(product_set) != len(set(product_set)):
            raise ValidationError("A bundle cannot contain duplicate products.")
