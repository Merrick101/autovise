"""
Models for managing products, bundles, categories,
and reviews in the e-commerce application.
Located at apps/products/models.py
"""

from django.db import models
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.urls import reverse
from django.utils.text import slugify
from django.utils import timezone
from django.utils.timezone import now
from django.utils.html import mark_safe
from decimal import Decimal
from ckeditor.fields import RichTextField


class Category(models.Model):
    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True)

    def __str__(self):
        return self.name


class Subcategory(models.Model):
    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True)
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='subcategories')

    class Meta:
        verbose_name = "Subcategory"
        verbose_name_plural = "Subcategories"
        ordering = ['name']

    def __str__(self):
        return f"{self.name} ({self.category.name})"


class ProductType(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name


class Tag(models.Model):
    name = models.CharField(max_length=50)

    def __str__(self):
        return self.name


class Product(models.Model):
    TIER_CHOICES = [
        ('Standard', 'Standard'),
        ('Pro', 'Pro'),
    ]

    name = models.CharField(max_length=100)
    variant = models.CharField(max_length=100)
    description = RichTextField()
    slug = models.SlugField(unique=True, blank=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    type = models.ForeignKey(ProductType, on_delete=models.CASCADE, related_name='products')
    tier = models.CharField(max_length=20, choices=TIER_CHOICES)
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='products')
    subcategory = models.ForeignKey(
        Subcategory,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='products'
    )

    price = models.DecimalField(max_digits=8, decimal_places=2, default=0.00)
    image = models.ImageField(
        upload_to='products/',
        blank=True,
        null=True,
        max_length=255,
        help_text="Upload the product image (optional)."
    )
    stock = models.PositiveIntegerField()
    sku = models.CharField(max_length=50, unique=True)
    product_code = models.CharField(max_length=50, unique=True, default='TEMP_CODE')
    image_type = models.CharField(max_length=50, blank=True, default='')

    tags = models.ManyToManyField(Tag, blank=True)
    bundles = models.ManyToManyField('Bundle', through='ProductBundle', related_name='products')

    featured = models.BooleanField(default=False, help_text="Mark as a featured item.")
    image_ready = models.BooleanField(default=False, help_text="Image has been generated and approved.")
    is_draft = models.BooleanField(default=False, help_text="Hide product from public view (draft mode).")

    class Meta:
        verbose_name = "Product"
        verbose_name_plural = "Products"

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse("products:product_detail", kwargs={"pk": self.pk})

    def __str__(self):
        return f"{self.name} ({self.variant})"

    def image_tag(self):
        if self.image:
            return mark_safe(
                f'<img src="{self.image.url}" width="60" height="60" style="object-fit: cover; border-radius: 4px;" />'
            )
        return "No Image"

    image_tag.short_description = "Image"

    def review_count(self):
        return self.reviews.count()

    def average_rating(self):
        return self.reviews.aggregate(avg=models.Avg('rating'))['avg'] or 0


class Bundle(models.Model):
    BUNDLE_TYPE_CHOICES = [
        ('Standard', 'Standard'),
        ('Pro', 'Pro'),
        ('Special', 'Special'),
    ]

    name = models.CharField(
        max_length=100
    )
    description = RichTextField(
        blank=True
    )
    slug = models.SlugField(
        unique=True, blank=True
    )
    discount_percentage = models.DecimalField(
        max_digits=6, decimal_places=2, default=10.00
    )
    price = models.DecimalField(
        max_digits=8, decimal_places=2, default=0.00
    )
    subtotal_price = models.DecimalField(
        max_digits=8, decimal_places=2, default=0.00
    )
    bundle_type = models.CharField(
        max_length=20, choices=BUNDLE_TYPE_CHOICES, default='Standard'
    )
    featured = models.BooleanField(
        default=False
    )

    sku = models.CharField(
        max_length=50, unique=True, default='TEMP_SKU', help_text="Unique identifier for this bundle"
    )
    bundle_code = models.CharField(
        max_length=50, unique=True, default='TEMP_BUNDLE_CODE', help_text="Internal code used for SEO and tracking"
    )

    image = models.ImageField(
        upload_to='bundles/',
        blank=True,
        null=True,
        max_length=255,
        help_text="Optional: Upload an image directly."
    )
    image_path = models.CharField(
        max_length=255,
        blank=True,
        help_text="Optional: Provide relative S3 path (e.g. bundles/my-image.png)"
    )

    tags = models.ManyToManyField('Tag', blank=True, related_name='bundles')
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        if not self.sku:
            self.sku = f"BNDL-{self.bundle_type[:3].upper()}-{now().strftime('%y%m%d%H%M')}"
        if not self.bundle_code or self.bundle_code == 'TEMP_BUNDLE_CODE':
            self.bundle_code = f"bundle-{slugify(self.name)}"
        if self.image_path:
            self.image.name = self.image_path
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse("products:bundle_detail", kwargs={"bundle_id": self.pk})

    def __str__(self):
        return self.name

    def image_tag(self):
        if self.image:
            return mark_safe(
                f'<img src="{self.image.url}" width="60" height="60" style="object-fit: cover; border-radius: 4px;" />'
            )
        return "No Image"

    image_tag.short_description = "Preview"

    def calculated_price(self):
        total = sum(p.price for p in self.products.all())
        discount = Decimal(self.discount_percentage) if self.discount_percentage else Decimal('10.0')
        final = total * (Decimal('1.00') - discount / Decimal('100.00'))
        return round(final, 2)

    def review_count(self):
        return self.reviews.count()

    def average_rating(self):
        return self.reviews.aggregate(avg=models.Avg('rating'))['avg'] or 0


class ProductBundle(models.Model):
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        help_text="Select a product to include in this bundle."
    )
    bundle = models.ForeignKey(Bundle, on_delete=models.CASCADE)

    class Meta:
        verbose_name = "Bundle Product Link"
        verbose_name_plural = "Included Products"

    def __str__(self):
        return f"{self.product.name} in {self.bundle.name}"


class Review(models.Model):
    RATING_CHOICES = [(i, str(i)) for i in range(1, 6)]

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    product = models.ForeignKey(
        Product, null=True, blank=True, related_name='reviews', on_delete=models.CASCADE
    )
    bundle = models.ForeignKey(
        Bundle, null=True, blank=True, related_name='reviews', on_delete=models.CASCADE
    )

    rating = models.IntegerField(choices=RATING_CHOICES)
    comment = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def clean(self):
        if not self.product and not self.bundle:
            raise ValidationError(
                "Review must be linked to a product or a bundle."
            )
        if self.product and self.bundle:
            raise ValidationError(
                "Review cannot be linked to both a product and a bundle."
            )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["user", "product"], name="uniq_user_product_review"
            ),
            models.UniqueConstraint(
                fields=["user", "bundle"],  name="uniq_user_bundle_review"
            ),
        ]
