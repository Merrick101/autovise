# apps/users/urls.py

from django.urls import path, include
from . import views
from .views import profile_view

urlpatterns = [
    path("accounts/", include("allauth.urls")),
    path('profile/', profile_view, name='profile'),
]
