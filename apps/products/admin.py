# apps/products/admin.py

from django.contrib import admin
from django.contrib.admin import SimpleListFilter
from django.utils.html import format_html
from django.core.exceptions import ValidationError
from decimal import Decimal, InvalidOperation
from .forms import BundleAdminForm, ProductAdminForm
from .models import Product, Category, ProductType, Tag, Bundle, ProductBundle, Subcategory, Review


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
    classes = ['tab-general']
    readonly_fields = ['product_price', 'product_tier']

    def product_price(self, obj):
        if obj.product:
            return f"£{obj.product.price:.2f}"
        return "-"
    product_price.short_description = "Price"

    def product_tier(self, obj):
        if obj.product and obj.product.tier:
            return obj.product.tier
        return "-"
    product_tier.short_description = "Tier"

    def clean(self):
        super().clean()
        included = [
            form.cleaned_data['product']
            for form in self.forms
            if form.cleaned_data and not form.cleaned_data.get('DELETE', False)
        ]

        if len(included) < 3:
            raise ValidationError("A bundle must include at least 3 products.")

        if len(set(included)) != len(included):
            raise ValidationError("A bundle cannot contain duplicate products.")

        parent = self.instance
        if parent.bundle_type == "Pro" and not any(p.tier == "Pro" for p in included):
            raise ValidationError("Pro-tier bundles must include at least one Pro product.")


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    form = ProductAdminForm
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
            'fields': ('image', 'image_tag', 'image_path', 'image_type'),
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
    list_display = [
        'name', 'bundle_type', 'bundle_code', 'sku',
        'price', 'discount_percentage', 'product_count', 'tag_list', 'featured',
    ]
    search_fields = ['name', 'bundle_code', 'sku', 'tags__name']
    inlines = [ProductBundleInline]
    readonly_fields = [
        'slug', 'created_at', 'updated_at',
        'subtotal_price', 'calculated_price',
        'bundle_info_note', 'image_tag'
    ]
    actions = ['recalculate_prices']  # Custom action to recalculate bundle prices

    fieldsets = (
        ("Basic Info", {
            'fields': ('name', 'slug', 'description'),
            'classes': ['tab-general'],
        }),
        ("Pricing", {
            'fields': ('price', 'discount_percentage'),
            'classes': ['tab-pricing'],
        }),
        ("Identifiers", {
            'fields': ('sku', 'bundle_code'),
            'classes': ['tab-general', 'collapse'],
        }),
        ("Media", {
            'fields': ('image', 'image_path', 'image_tag'),
            'classes': ['tab-media'],
        }),
        ("Bundle Type", {
            'fields': ('bundle_type', 'tags'),
            'classes': ['tab-general', 'collapse'],
        }),
        ("Status Flags", {
            'fields': ['featured'],
            'classes': ['tab-status', 'collapse'],
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

    def tag_list(self, obj):
        return ", ".join(tag.name for tag in obj.tags.all())
    tag_list.short_description = "Tags"

    def product_count(self, obj):
        return obj.products.count()
    product_count.short_description = 'Number of Products'

    def save_related(self, request, form, formsets, change):
        super().save_related(request, form, formsets, change)
        bundle = form.instance
        if bundle.pk:
            total = sum(p.price for p in bundle.products.all())
            discount = bundle.discount_percentage or Decimal('10.0')
            bundle.subtotal_price = total
            bundle.price = round(total * (Decimal('1.00') - discount / Decimal('100.00')), 2)
            bundle.save()

    def formatted_price(self, obj):
        try:
            price = Decimal(obj.price)
            return format_html("£{0:.2f}", price)
        except (TypeError, InvalidOperation, ValueError):
            return "-"

    def subtotal_price(self, obj):
        if obj.pk:
            total = sum(p.price for p in obj.products.all())
            return format_html("£{0:.2f}", total)
        return format_html("<em>Save to calculate</em>")
    subtotal_price.short_description = "Subtotal (No Discount)"

    def calculated_price(self, obj):
        if obj.pk:
            total = sum(p.price for p in obj.products.all())
            discount = obj.discount_percentage or Decimal('10.0')
            final = total * (Decimal('1.00') - discount / Decimal('100.00'))
            return format_html("£{0:.2f}", final)
        return format_html("<em>Save to calculate</em>")
    calculated_price.short_description = "Discounted Price"

    def bundle_info_note(self, obj):
        return "Note: Bundles may include products from any category."
    bundle_info_note.short_description = "Info"

    @admin.action(description="Recalculate bundle prices")
    def recalculate_prices(self, request, queryset):
        for bundle in queryset:
            total = sum(p.price for p in bundle.products.all())
            bundle.subtotal_price = total
            bundle.price = round(total * (Decimal('1.00') - bundle.discount_percentage / Decimal('100.00')), 2)
            bundle.save()


@admin.register(ProductBundle)
class ProductBundleAdmin(admin.ModelAdmin):
    list_display = ['bundle', 'product']


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ('product', 'user', 'rating', 'created_at')
    list_filter = ('rating', 'created_at')
    search_fields = ('user__username', 'product__name', 'comment')
    ordering = ('-created_at',)
