"""
Models for the orders app.
Contains Order, OrderItem, Cart, and CartItem models.
Located at apps/orders/models.py
"""

from django.conf import settings
from django.db import models
from apps.products.models import Product, Bundle


class Order(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        null=True,
        blank=True
    )
    created_at = models.DateTimeField(
        auto_now_add=True
    )
    total_price = models.DecimalField(
        max_digits=8, decimal_places=2
    )
    total_amount = models.DecimalField(
        max_digits=8, decimal_places=2, blank=True, null=True
    )
    delivery_fee = models.DecimalField(
        max_digits=5, decimal_places=2, default=0.00
    )
    discount_total = models.DecimalField(
        max_digits=6, decimal_places=2, default=0.00
    )
    is_first_order = models.BooleanField(
        default=False
    )
    stripe_session_id = models.CharField(
        max_length=255, blank=True, null=True, unique=True
    )
    stripe_payment_intent = models.CharField(
        max_length=255, blank=True, null=True, db_index=True, unique=True
    )
    is_paid = models.BooleanField(
        default=False
    )
    # Shipping (one address per order)
    shipping_name = models.CharField(
        "Recipient name", max_length=255, blank=True, default=""
    )
    shipping_line1 = models.CharField(
        "Address line 1", max_length=255, blank=True, default=""
    )
    shipping_line2 = models.CharField(
        "Address line 2", max_length=255, blank=True, default=""
    )
    shipping_city = models.CharField(
        "City / Town", max_length=100, blank=True, default=""
    )
    shipping_postcode = models.CharField(
        "Postcode", max_length=20, blank=True, default=""
    )
    shipping_country = models.CharField(
        "Country (ISO-2)", max_length=2, blank=True, default="GB",
        help_text="Two-letter country code, e.g. GB, US."
    )
    shipping_phone = models.CharField(
        "Contact phone", max_length=30, blank=True, default=""
    )

    # (optional) store guest email on the order for reference
    contact_email = models.EmailField(
        blank=True, default=""
    )

    PAYMENT_STATUS_CHOICES = (
        ("pending", "Pending"),
        ("succeeded", "Succeeded"),
        ("failed", "Failed"),
        ("canceled", "Canceled"),
        ("requires_action", "Requires Action"),
    )

    payment_status = models.CharField(
        max_length=32, choices=PAYMENT_STATUS_CHOICES,
        default="pending", db_index=True
    )
    paid_at = models.DateTimeField(
        blank=True, null=True
    )
    stripe_latest_event = models.CharField(
        max_length=64, blank=True, default=""
    )
    stripe_last_error = models.TextField(
        blank=True, default=""
    )

    def has_shipping(self) -> bool:
        return bool(self.shipping_line1)

    def shipping_for_stripe(self):
        """Shape the address for Stripe's PaymentIntent.shipping."""
        if not self.shipping_line1:
            return None
        return {
            "name": self.shipping_name or None,
            "phone": self.shipping_phone or None,
            "address": {
                "line1": self.shipping_line1,
                "line2": self.shipping_line2 or None,
                "city": self.shipping_city or None,
                "postal_code": self.shipping_postcode or None,
                "country": (self.shipping_country or "GB"),
            },
        }

    def formatted_shipping(self) -> str:
        parts = [
            self.shipping_name,
            self.shipping_line1,
            self.shipping_line2,
            f"{self.shipping_city} {self.shipping_postcode}".strip(),
            self.shipping_country,
        ]
        return ", ".join([p for p in parts if p])

    def save(self, *args, **kwargs):
        if self.shipping_country:
            self.shipping_country = self.shipping_country.upper()
        super().save(*args, **kwargs)

    def __str__(self):
        who = self.user.username if self.user else "Guest"
        return f"Order #{self.id} for {who}"


class OrderItem(models.Model):
    order = models.ForeignKey(
        Order, on_delete=models.CASCADE, related_name='items'
    )
    product = models.ForeignKey(
       Product, on_delete=models.PROTECT,
       null=True, blank=True,
    )
    bundle = models.ForeignKey(
       Bundle, on_delete=models.PROTECT,
       null=True, blank=True,
       help_text="If this line is a bundle, store it here.",
    )
    quantity = models.PositiveIntegerField(
        default=1
    )
    unit_price = models.DecimalField(
        max_digits=8, decimal_places=2
    )

    class Meta:
        constraints = [
            models.CheckConstraint(
                condition=(
                    models.Q(product__isnull=False, bundle__isnull=True) |
                    models.Q(product__isnull=True,  bundle__isnull=False)
                ),
                name="orderitem_product_xor_bundle",
            ),
        ]

    def __str__(self):
        name = self.bundle.name if self.bundle else self.product.name
        return f"{self.quantity} × {name} @ £{self.unit_price}"

    @property
    def subtotal(self):
        return self.quantity * self.unit_price


class Cart(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='carts'
    )
    created_at = models.DateTimeField(
        auto_now_add=True
    )
    updated_at = models.DateTimeField(
        auto_now=True
    )
    is_active = models.BooleanField(
        default=True
    )

    def __str__(self):
        return f"Cart for {self.user.username} (Active: {self.is_active})"

    def total(self):
        return sum(item.subtotal() for item in self.items.all())


class CartItem(models.Model):
    cart = models.ForeignKey(
        Cart,
        on_delete=models.CASCADE,
        related_name='items'
    )
    product = models.ForeignKey(
        Product, on_delete=models.CASCADE
    )
    quantity = models.PositiveIntegerField(
        default=1
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["cart", "product"],
                name="unique_cart_product"
            )
        ]

    def __str__(self):
        return f"{self.quantity} × {self.product.name}"

    def subtotal(self):
        return self.quantity * self.product.price
