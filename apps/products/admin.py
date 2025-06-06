# apps/products/admin.py

from django.contrib import admin
from django.contrib.admin import SimpleListFilter
from django.utils.html import format_html
from django.core.exceptions import ValidationError
from decimal import Decimal, InvalidOperation
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
    verbose_name = "Included Product"
    verbose_name_plural = "Included Products"
    extra = 1
    autocomplete_fields = ['product']


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = [
        'name', 'variant', 'product_code', 'price', 'tier',
        'image_type', 'category', 'subcategory', 'type', 'stock', 'image_tag',
        'bundle_count', 'created_at', 'updated_at', 'featured', 'image_ready', 'is_draft'
    ]
    list_filter = ['tier', 'type', 'category', 'subcategory', 'featured', 'image_ready', 'is_draft', StockLevelFilter]
    search_fields = ['name', 'variant', 'product_code', 'sku']
    ordering = ['name']
    autocomplete_fields = ['category', 'subcategory', 'type']
    filter_horizontal = ['tags']
    readonly_fields = ['slug', 'created_at', 'updated_at', 'image_tag']

    fieldsets = (
        ("Basic Info", {
            'fields': ('name', 'variant', 'slug', 'description'),
            'classes': ['tab-general'],
        }),
        ("Classification", {
            'fields': ('tier', 'category', 'subcategory', 'type', 'tags'),
            'classes': ['tab-general', 'collapse'],
        }),
        ("Pricing & Inventory", {
            'fields': ('price', 'stock', 'sku', 'product_code'),
            'classes': ['tab-inventory'],
        }),
        ("Media", {
            'fields': ('image', 'image_tag', 'image_type'),
            'classes': ['tab-media', 'collapse'],
        }),
        ("Status Flags", {
            'fields': ('featured', 'image_ready', 'is_draft'),
            'classes': ['tab-status', 'collapse'],
        }),
        ("Timestamps", {
            'fields': ('created_at', 'updated_at'),
            'classes': ['tab-status', 'collapse'],
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
    list_display = ['name', 'slug', 'formatted_price', 'discount_percentage', 'product_count']
    search_fields = ['name', 'slug']
    prepopulated_fields = {'slug': ('name',)}
    inlines = [ProductBundleInline]
    readonly_fields = ['created_at', 'updated_at', 'calculated_price', 'bundle_info_note']

    fieldsets = (
        ("Basic Info", {
            'fields': ('name', 'description'),
            'classes': ['tab-general'],
        }),
        ("Pricing", {
            'fields': ('price', 'discount_percentage'),
            'classes': ['tab-pricing'],
        }),
        ("Preview", {
            'fields': ('calculated_price',),
            'classes': ['tab-pricing', 'collapse'],
        }),
        ("Timestamps", {
            'fields': ('created_at', 'updated_at'),
            'classes': ['tab-meta', 'collapse'],
        }),
        ("Info", {
            'fields': ('bundle_info_note',),
            'classes': ['tab-meta', 'collapse'],
        }),
    )

    def product_count(self, obj):
        return obj.products.count()
    product_count.short_description = 'Number of Products'

    def formatted_price(self, obj):
        try:
            price = Decimal(obj.price)
            return format_html("£{0:.2f}", price)
        except (TypeError, InvalidOperation, ValueError):
            return "-"

    def calculated_price(self, obj):
        if obj.pk:
            total = sum(p.price for p in obj.products.all())
            return round(total * Decimal('0.90'), 2)  # 10% discount
        return "N/A"
    calculated_price.short_description = "Auto Price (10% Off)"

    def bundle_info_note(self, obj):
        return "Note: Bundles may include products from any category."
    bundle_info_note.short_description = "Info"

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)

        product_set = obj.products.all()

        if len(product_set) < 3:
            raise ValidationError("A bundle must include at least 3 products.")

        if obj.bundle_type == "Pro":
            has_pro_item = any(p.tier == "Pro" for p in product_set)
            if not has_pro_item:
                raise ValidationError("Pro-tier bundles must include at least one Pro product.")

        if len(product_set) != len(set(product_set)):
            raise ValidationError("A bundle cannot contain duplicate products.")


@admin.register(ProductBundle)
class ProductBundleAdmin(admin.ModelAdmin):
    list_display = ['bundle', 'product']
