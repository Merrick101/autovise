# apps/users/models.py

from django.db import models
from django.contrib.auth.models import User
from apps.products.models import Product, Bundle


class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    is_first_time_buyer = models.BooleanField(default=True)
    address = models.CharField(max_length=255, blank=True)
    phone_number = models.CharField(max_length=20, blank=True)
    saved_products = models.ManyToManyField(Product, blank=True, related_name='saved_by_users')
    saved_bundles = models.ManyToManyField(Bundle, blank=True, related_name='saved_by_users')

    def __str__(self):
        return f"{self.user.username}'s Profile"
