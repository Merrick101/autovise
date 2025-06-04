# apps/products/admin.py

from django.contrib import admin, SimpleListFilter
from .models import Product, Category, ProductType, Tag, Bundle, ProductBundle


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
        'image_type', 'category', 'type', 'stock'
    ]
    list_filter = ['tier', 'type', 'category', StockLevelFilter]
    search_fields = ['name', 'variant', 'product_code', 'sku']
    ordering = ['name']
    autocomplete_fields = ['category', 'type']
    filter_horizontal = ['tags']  # Easier tag assignment
    readonly_fields = ['slug', 'created_at', 'updated_at', 'image_tag']


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name']
    search_fields = ['name']
    prepopulated_fields = {'slug': ('name',)}


@admin.register(ProductType)
class ProductTypeAdmin(admin.ModelAdmin):
    list_display = ['name']
    search_fields = ['name']


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ['name']
    search_fields = ['name']


@admin.register(Bundle)
class BundleAdmin(admin.ModelAdmin):
    list_display = ['name', 'price', 'discount_percentage', 'product_count']
    search_fields = ['name']
    inlines = [ProductBundleInline]
    readonly_fields = ['created_at', 'updated_at']

    def product_count(self, obj):
        return obj.products.count()
    product_count.short_description = 'Number of Products'


@admin.register(ProductBundle)
class ProductBundleAdmin(admin.ModelAdmin):
    list_display = ['bundle', 'product']
