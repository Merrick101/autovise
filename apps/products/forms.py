# apps/products/forms.py

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
    image_path = forms.CharField(
        label="Image Path (S3 relative)",
        required=False,
        help_text="Optional: Directly assign S3 image path (e.g. bundles/filename.png)"
    )

    class Meta:
        model = Bundle
        fields = [
            'name', 'slug', 'description',
            'discount_percentage', 'price', 'bundle_type',
            'sku', 'bundle_code', 'image', 'image_path'
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.image:
            self.fields['image_path'].initial = self.instance.image.name

    def clean_discount_percentage(self):
        value = self.cleaned_data.get('discount_percentage')
        return Decimal('10.0') if value is None else value

    def clean(self):
        cleaned_data = super().clean()
        image_path = cleaned_data.get("image_path")
        if image_path:
            self.instance.image.name = image_path
        return cleaned_data
