# apps/users/tests/test_models.py

import pytest
from django.contrib.auth.models import User


@pytest.mark.django_db
def test_userprofile_str_returns_username():
    user = User.objects.create_user(username="testuser", password="testpass")
    profile = user.profile  # Use auto-created profile
    assert str(profile) == "testuser's Profile"
