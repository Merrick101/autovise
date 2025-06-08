# apps/users/urls.py

from django.urls import path
from . import views

urlpatterns = [
    path('profile/', views.profile_view, name='profile'),
    path('save/<int:product_id>/', views.save_product, name='save_product'),
]
