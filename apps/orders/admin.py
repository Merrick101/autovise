# apps/orders/admin.py

from django.contrib import admin
from apps.orders.models import Order, OrderItem, Cart, CartItem


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    readonly_fields = ['subtotal']
    extra = 0


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'created_at', 'total_price', 'is_first_order']
    list_filter = ['created_at', 'is_first_order']
    search_fields = ['user__username']
    date_hierarchy = 'created_at'
    inlines = [OrderItemInline]


@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ['order', 'product', 'quantity', 'unit_price', 'subtotal']
    list_filter = ['product', 'order']
    search_fields = ['product__name']

    def subtotal(self, obj):
        return obj.quantity * obj.unit_price
    subtotal.short_description = 'Subtotal'


@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    list_display = ['user', 'created_at', 'updated_at', 'is_active']
    list_filter = ['is_active']
    search_fields = ['user__username']


@admin.register(CartItem)
class CartItemAdmin(admin.ModelAdmin):
    list_display = ['cart', 'product', 'quantity']
    list_filter = ['product']
    search_fields = ['product__name']
