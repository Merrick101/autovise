# apps/orders/models.py

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
        max_length=255, blank=True, null=True
    )
    is_paid = models.BooleanField(
        default=False
    )

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
                check=(
                    models.Q(product__isnull=False, bundle__isnull=True) |
                    models.Q(product__isnull=True,  bundle__isnull=False)
                ),
                name="orderitem_product_xor_bundle"
            )
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
