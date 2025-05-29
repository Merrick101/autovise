# apps/users/models.py

from django.db import models
from django.contrib.auth.models import User


class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    is_first_time_buyer = models.BooleanField(default=True)
    address = models.CharField(max_length=255, blank=True)
    phone_number = models.CharField(max_length=20, blank=True)
    preferences = models.TextField(blank=True)

    def __str__(self):
        return f"{self.user.username}'s Profile"
