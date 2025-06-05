# apps/products/admin.py

from django.contrib import admin
from django.contrib.admin import SimpleListFilter
from decimal import Decimal
from .forms import BundleAdminForm
from .models import Product, Category, ProductType, Tag, Bundle, ProductBundle, Subcategory


class StockLevelFilter(SimpleListFilter):
    title = 'Stock Level'
    parameter_name = 'stock_level'

    def lookups(self, request, model_admin):
        return [
            ('low', 'Low Stock (<10)'),
            ('medium', 'Medium Stock (10–49)'),
            ('high', 'High Stock (50+)'),
        ]

    def queryset(self, request, queryset):
        if self.value() == 'low':
            return queryset.filter(stock__lt=10)
        if self.value() == 'medium':
            return queryset.filter(stock__gte=10, stock__lt=50)
        if self.value() == 'high':
            return queryset.filter(stock__gte=50)


# Inline for managing bundle-product relationships within the Bundle admin
class ProductBundleInline(admin.TabularInline):
    model = ProductBundle
    extra = 1
    autocomplete_fields = ['product']


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = [
        'name', 'variant', 'product_code', 'price', 'tier',
        'image_type', 'category', 'subcategory', 'type', 'stock', 'image_tag',
        'bundle_count', 'created_at', 'updated_at'
    ]
    list_filter = ['tier', 'type', 'category', 'subcategory', StockLevelFilter]
    search_fields = ['name', 'variant', 'product_code', 'sku']
    ordering = ['name']
    autocomplete_fields = ['category', 'subcategory', 'type']
    filter_horizontal = ['tags']
    readonly_fields = ['slug', 'created_at', 'updated_at', 'image_tag']

    fieldsets = (
        ("Basic Info", {
            'fields': ('name', 'variant', 'slug', 'description'),
        }),
        ("Classification", {
            'fields': ('tier', 'category', 'type', 'tags'),
            'classes': ['collapse'],
        }),
        ("Pricing & Inventory", {
            'fields': ('price', 'stock', 'sku', 'product_code'),
        }),
        ("Media", {
            'fields': ('image', 'image_tag', 'image_type'),
            'classes': ['collapse'],
        }),
        ("Timestamps", {
            'fields': ('created_at', 'updated_at'),
            'classes': ['collapse'],
        }),
    )

    def bundle_count(self, obj):
        return obj.bundles.count()
    bundle_count.short_description = "Used in Bundles"


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name']
    search_fields = ['name']
    prepopulated_fields = {'slug': ('name',)}
    ordering = ['name']


@admin.register(Subcategory)
class SubcategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'category']
    search_fields = ['name']
    prepopulated_fields = {'slug': ('name',)}
    ordering = ['name']


@admin.register(ProductType)
class ProductTypeAdmin(admin.ModelAdmin):
    list_display = ['name']
    search_fields = ['name']
    ordering = ['name']


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ['name']
    search_fields = ['name']


@admin.register(Bundle)
class BundleAdmin(admin.ModelAdmin):
    form = BundleAdminForm
    list_display = ['name', 'price', 'discount_percentage', 'product_count']
    search_fields = ['name']
    inlines = [ProductBundleInline]
    readonly_fields = ['created_at', 'updated_at', 'calculated_price']

    fieldsets = (
        ("Basic Info", {
            'fields': ('name', 'description'),
        }),
        ("Pricing", {
            'fields': ('price', 'discount_percentage'),
        }),
        ("Preview", {
            'fields': ('calculated_price',),
            'classes': ['collapse'],
        }),
        ("Timestamps", {
            'fields': ('created_at', 'updated_at'),
            'classes': ['collapse'],
        }),
    )

    def product_count(self, obj):
        return obj.products.count()
    product_count.short_description = 'Number of Products'

    def calculated_price(self, obj):
        if obj.pk:
            total = sum(p.price for p in obj.products.all())
            return round(total * Decimal('0.90'), 2)  # 10% discount
        return "N/A"

    calculated_price.short_description = "Auto Price (10% Off)"


@admin.register(ProductBundle)
class ProductBundleAdmin(admin.ModelAdmin):
    list_display = ['bundle', 'product']
