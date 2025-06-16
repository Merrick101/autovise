# apps/users/urls.py

from django.urls import path
from . import views

app_name = 'users'

urlpatterns = [
    path('profile/', views.profile_view, name='profile'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('delete/', views.delete_account, name='delete_account'),
    path('save/<int:product_id>/', views.save_product, name='save_product'),
    path('save-bundle/<int:bundle_id>/', views.save_bundle, name='save_bundle'),
]
