# apps/users/forms.py

from django import forms
from django.contrib.auth.models import User
from .models import UserProfile  # NOQA


class UserForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email']
