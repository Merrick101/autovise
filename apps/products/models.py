# app/products/models.py

from django.db import models
from django.utils.text import slugify
from django.utils import timezone
from django.utils.html import mark_safe
from ckeditor.fields import RichTextField


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

    type = models.ForeignKey('ProductType', on_delete=models.CASCADE, related_name='products')
    tier = models.CharField(max_length=20, choices=TIER_CHOICES)
    category = models.ForeignKey('Category', on_delete=models.CASCADE, related_name='products')

    price = models.DecimalField(max_digits=8, decimal_places=2, default=0.00)
    image = models.ImageField(upload_to='product_images/')
    stock = models.PositiveIntegerField()
    sku = models.CharField(max_length=50, unique=True)
    product_code = models.CharField(max_length=50, unique=True, default='TEMP_CODE')
    image_type = models.CharField(max_length=50, blank=True, default='')

    tags = models.ManyToManyField('Tag', blank=True)
    bundles = models.ManyToManyField('Bundle', through='ProductBundle', related_name='products')

    class Meta:
        verbose_name = "Product"
        verbose_name_plural = "Products"

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(f"{self.name}-{self.variant}")
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.name} ({self.variant})"

    def image_tag(self):
        if self.image:
            return mark_safe(f'<img src="{self.image.url}" width="60" height="60" style="object-fit: cover; border-radius: 4px;" />')
        return "No Image"

    image_tag.short_description = "Image"


class Category(models.Model):
    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True)

    def __str__(self):
        return self.name


class ProductType(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name


class Tag(models.Model):
    name = models.CharField(max_length=50)

    def __str__(self):
        return self.name


class Bundle(models.Model):
    BUNDLE_TYPE_CHOICES = [
        ('Standard', 'Standard'),
        ('Pro', 'Pro'),
        ('Special', 'Special'),
    ]

    name = models.CharField(max_length=100)
    description = RichTextField(blank=True)
    discount_percentage = models.DecimalField(max_digits=5, decimal_places=2)
    price = models.DecimalField(max_digits=8, decimal_places=2, default=0.00)
    bundle_type = models.CharField(max_length=20, choices=BUNDLE_TYPE_CHOICES, default='Standard')
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name


class ProductBundle(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    bundle = models.ForeignKey(Bundle, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.product.name} in {self.bundle.name}"
