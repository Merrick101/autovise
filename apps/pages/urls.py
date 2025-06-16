# apps/pages/urls.py

from django.urls import path
from . import views

app_name = 'pages'

urlpatterns = [
    path("newsletter/subscribe/", views.subscribe_newsletter, name="newsletter_subscribe"),
    path('privacy/', views.privacy_policy, name='privacy'),
    path('terms/', views.terms_and_conditions, name='terms'),
    path('contact/', views.contact, name='contact'),
]
