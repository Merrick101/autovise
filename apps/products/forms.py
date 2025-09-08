"""
Forms for managing products, bundles, and reviews
in the e-commerce application.
Located at apps/products/forms.py
"""

from django import forms
from decimal import Decimal
from .models import Bundle, Product, Review


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

        if 'created_at' in self.fields:
            self.fields['created_at'].required = False
        if 'updated_at' in self.fields:
            self.fields['updated_at'].required = False

        if 'bundles' in self.fields:
            self.fields.pop('bundles')

        # Pre-fill image_path if an image is present
        if self.instance and self.instance.image:
            self.fields['image_path'].initial = self.instance.image.name

    def clean(self):
        cleaned_data = super().clean()
        image_path = cleaned_data.get('image_path')
        if image_path:
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
        # Allow blank input so clean_discount_percentage can default it to 10.0
        if 'discount_percentage' in self.fields:
            self.fields['discount_percentage'].required = False

        if self.instance and self.instance.image:
            self.fields['image_path'].initial = self.instance.image.name

    def clean_discount_percentage(self):
        value = self.cleaned_data.get('discount_percentage')
        # Default to 10.0 when empty/None
        return Decimal('10.0') if value in (None, '') else value

    def clean(self):
        cleaned_data = super().clean()
        image_path = cleaned_data.get("image_path")
        if image_path:
            self.instance.image.name = image_path
        return cleaned_data


class ReviewForm(forms.ModelForm):
    class Meta:
        model = Review
        fields = ['rating', 'comment']
        widgets = {
            'rating': forms.RadioSelect(choices=[(i, f'{i} ★') for i in range(1, 6)]),
            'comment': forms.Textarea(attrs={
                'rows': 3,
                'placeholder': 'Leave a comment...',
                'class': 'form-control'
            }),
        }
        labels = {
            'rating': 'Your Rating',
            'comment': 'Your Review'
        }
        error_messages = {
            'rating': {
                'required': 'Please select a star rating (1–5) before submitting.'
            }
        }
