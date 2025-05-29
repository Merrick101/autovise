# apps/users/urls.py

from django.urls import path
from . import views
from .views import profile_view

urlpatterns = [
    path('profile/', profile_view, name='profile'),
]
