# apps/products/urls.py

from django.urls import path
from . import views

app_name = 'products'

urlpatterns = [
    path('', views.product_list_view, name='product_list'),
    path('<int:pk>/', views.product_detail_view, name='product_detail'),
    path('bundles/', views.bundle_list_view, name='bundle_list'),
    path('bundles/<int:bundle_id>/', views.bundle_detail_view, name='bundle_detail'),
]
