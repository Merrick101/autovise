"""
Admin configuration for the orders app.
Located at apps/orders/admin.py
"""

from datetime import timedelta
import logging

from django.conf import settings
from django.contrib import admin, messages
from django.utils.html import format_html
from django.utils.timezone import now

import stripe

from apps.orders.models import Order, OrderItem, Cart, CartItem
from apps.orders.utils.order import update_order_from_stripe_session

logger = logging.getLogger(__name__)

stripe.api_key = getattr(settings, "STRIPE_SECRET_KEY", None)
stripe.api_version = getattr(settings, "STRIPE_API_VERSION", None)


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ("product", "bundle", "quantity", "unit_price", "line_subtotal")
    fields = ("product", "bundle", "quantity", "unit_price", "line_subtotal")

    def line_subtotal(self, obj):
        return obj.quantity * obj.unit_price
    line_subtotal.short_description = "Subtotal"


class AbandonedCartFilter(admin.SimpleListFilter):
    title = "abandoned carts"
    parameter_name = "abandoned"

    def lookups(self, request, model_admin):
        return [("yes", "Abandoned (30+ min)")]

    def queryset(self, request, queryset):
        if self.value() == "yes":
            cutoff = now() - timedelta(minutes=30)
            return queryset.filter(updated_at__lt=cutoff, is_active=True)
        return queryset


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "user",
        "created_at",
        "total_price",
        "status_badge",
        "paid_at",
        "short_pi",
        "is_first_order",
    )
    list_filter = (
        "payment_status",
        "is_paid",
        "is_first_order",
        "created_at",
    )
    search_fields = (
        "id",
        "user__username",
        "user__email",
        "contact_email",
        "stripe_payment_intent",
        "stripe_session_id",
    )
    date_hierarchy = "created_at"
    ordering = ("-id",)

    inlines = [OrderItemInline]

    readonly_fields = (
        # order meta
        "created_at",
        "is_first_order",
        # amounts
        "total_amount",
        "discount_total",
        "delivery_fee",
        "total_price",
        # payment tracking
        "is_paid",
        "payment_status",
        "paid_at",
        "stripe_session_id",
        "stripe_payment_intent",
        "stripe_latest_event",
        "stripe_last_error",
        # shipping snapshot
        "shipping_name",
        "shipping_line1",
        "shipping_line2",
        "shipping_city",
        "shipping_postcode",
        "shipping_country",
        "shipping_phone",
        "contact_email",
    )

    fieldsets = (
        ("Order", {
            "fields": ("user", "created_at", "is_first_order", "contact_email")
        }),
        ("Amounts", {
            "fields": ("total_amount", "discount_total", "delivery_fee", "total_price")
        }),
        ("Payment", {
            "fields": (
                "is_paid", "payment_status", "paid_at",
                "stripe_payment_intent", "stripe_session_id",
                "stripe_latest_event", "stripe_last_error",
            )
        }),
        ("Shipping (snapshot)", {
            "fields": (
                "shipping_name", "shipping_line1", "shipping_line2",
                "shipping_city", "shipping_postcode", "shipping_country",
                "shipping_phone",
            )
        }),
    )

    actions = ["sync_from_stripe"]

    # --- Permissions (keep superuser-only policy) ---
    def has_view_permission(self, request, obj=None):
        return request.user.is_superuser

    def has_module_permission(self, request):
        return request.user.is_superuser

    def has_change_permission(self, request, obj=None):
        return request.user.is_superuser

    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser

    def has_add_permission(self, request):
        return request.user.is_superuser

    # --- Styled status badge ---
    def status_badge(self, obj: Order):
        status = (obj.payment_status or "pending").lower()
        color = {
            "succeeded": "#16a34a",        # green
            "failed": "#dc2626",           # red
            "canceled": "#dc2626",
            "requires_action": "#d97706",  # amber
            "processing": "#2563eb",       # blue
            "pending": "#6b7280",          # gray
        }.get(status, "#6b7280")
        return format_html(
            '<span style="padding:2px 6px;border-radius:10px;background:{};color:#fff;font-size:12px;">{}</span>',
            color, status.replace("_", " ").title()
        )
    status_badge.short_description = "Payment"

    def short_pi(self, obj: Order):
        if not obj.stripe_payment_intent:
            return "-"
        # Show only tail of PI for readability
        return f"...{obj.stripe_payment_intent[-8:]}"
    short_pi.short_description = "PI"

    # --- Admin action: sync from Stripe ---
    def sync_from_stripe(self, request, queryset):
        ok = 0
        missing = 0
        errors = 0

        for order in queryset:
            try:
                payload = None
                if order.stripe_payment_intent:
                    payload = stripe.PaymentIntent.retrieve(order.stripe_payment_intent)
                elif order.stripe_session_id:
                    payload = stripe.checkout.Session.retrieve(order.stripe_session_id)

                if not payload:
                    missing += 1
                    continue

                update_order_from_stripe_session(payload)
                ok += 1
            except Exception as e:
                errors += 1
                logger.exception("Admin sync failed for Order #%s: %s", order.id, e)

        if ok:
            messages.success(request, f"Synchronized {ok} order(s) from Stripe.")
        if missing:
            messages.warning(request, f"{missing} order(s) had no Stripe reference to sync.")
        if errors:
            messages.error(request, f"Errors syncing {errors} order(s); see logs.")
    sync_from_stripe.short_description = "Sync selected orders from Stripe"


@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ("order", "product", "bundle", "quantity", "unit_price", "subtotal")
    list_filter = ("product", "bundle", "order")
    search_fields = ("product__name", "bundle__name", "order__id")

    def subtotal(self, obj):
        return obj.quantity * obj.unit_price
    subtotal.short_description = "Subtotal"


@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    list_display = ("user", "created_at", "updated_at", "is_active")
    list_filter = ("is_active", AbandonedCartFilter)
    search_fields = ("user__username", "user__email")


@admin.register(CartItem)
class CartItemAdmin(admin.ModelAdmin):
    list_display = ("cart", "product", "quantity")
    list_filter = ("product",)
    search_fields = ("product__name", "cart__user__username")
