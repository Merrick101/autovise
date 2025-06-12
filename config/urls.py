# config/urls.py

from django.contrib import admin
from django.urls import path, include
from apps.orders.views.webhook import stripe_webhook_view

urlpatterns = [
    path('admin/', admin.site.urls),
    # Allauth URLs
    path('accounts/', include('allauth.urls')),
    # Placeholder routes for each core app
    path('products/', include('apps.products.urls')),
    path('orders/', include('apps.orders.urls')),
    path('users/', include('apps.users.urls')),
    path('', include('apps.pages.urls')),
    path('assets/', include('apps.assets.urls')),
    path("orders/webhook/", stripe_webhook_view, name="stripe_webhook"),
]
