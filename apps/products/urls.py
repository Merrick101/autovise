# apps/products/urls.py

from django.urls import path
from .views import product_list_view, product_detail_view, bundle_list_view

app_name = 'products'

urlpatterns = [
    path('', product_list_view, name='product_list'),
    path('<int:pk>/', product_detail_view, name='product_detail'),
    path('bundles/', bundle_list_view, name='bundle_list'),
]
