"""
Models for the 'users' app.
Includes models for user profiles and saved shipping addresses.
Located at apps/users/models.py
"""

from django.db import models
from django.conf import settings
from apps.products.models import Product, Bundle


class UserProfile(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        related_name='profile'
    )
    is_first_time_buyer = models.BooleanField(
        default=True
    )
    address = models.CharField(
        max_length=255, blank=True
    )
    phone_number = models.CharField(
        max_length=20, blank=True
    )
    saved_products = models.ManyToManyField(
        Product, blank=True, related_name='saved_by_users'
    )
    saved_bundles = models.ManyToManyField(
        Bundle, blank=True, related_name='saved_by_users'
    )

    def __str__(self):
        return f"{self.user.username}'s Profile"


class ShippingAddress(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        related_name="shipping_addresses"
    )
    name = models.CharField(
        max_length=255, blank=True, default=""
    )
    line1 = models.CharField(
        max_length=255, blank=True, default=""
    )
    line2 = models.CharField(
        max_length=255, blank=True, default=""
    )
    city = models.CharField(
        max_length=100, blank=True, default=""
    )
    postcode = models.CharField(
        max_length=20,  blank=True, default=""
    )
    country = models.CharField(
        max_length=2,   blank=True, default="GB"
    )
    phone = models.CharField(
        max_length=30,  blank=True, default=""
    )
    is_default = models.BooleanField(
        default=False, help_text="Set as default shipping address"
    )

    class Meta:
        # Portable ordering: default first
        ordering = ("-is_default", "-id")
        # Add indexes commonly queried
        indexes = [
            models.Index(fields=["user", "is_default"]),
        ]

    def save(self, *args, **kwargs):
        # Normalize country to ISO-2 upper
        self.country = (self.country or "GB").upper()

        super_default = False
        if self.is_default and self.user_id:
            # Ensure only ONE default per user
            # Defer own save until others are flipped
            super_default = True

        # Save first so there is a PK to exclude
        super().save(*args, **kwargs)

        if super_default:
            ShippingAddress.objects.filter(
                user=self.user, is_default=True
            ).exclude(pk=self.pk).update(is_default=False)

    def as_order_kwargs(self):
        return {
            "shipping_name":     self.name,
            "shipping_line1":    self.line1,
            "shipping_line2":    self.line2,
            "shipping_city":     self.city,
            "shipping_postcode": self.postcode,
            "shipping_country":  self.country or "GB",
            "shipping_phone":    self.phone,
        }

    def __str__(self):
        return f"{self.user} – {self.name or 'Unnamed'} ({self.postcode})"
