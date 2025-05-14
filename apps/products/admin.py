from django.contrib import admin
from .models import Product, Category, ProductType, Tag, Bundle, ProductBundle

admin.site.register(Product)
admin.site.register(Category)
admin.site.register(ProductType)
admin.site.register(Tag)
admin.site.register(Bundle)
admin.site.register(ProductBundle)
