"""
Adapter to customize django-allauth's social login behavior.
Located at apps/users/adapters.py
"""

from django.contrib.auth import get_user_model
from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from allauth.account.utils import perform_login, user_email

User = get_user_model()


class AutoviseSocialAdapter(DefaultSocialAccountAdapter):
    def pre_social_login(self, request, sociallogin):
        # If this social account is already linked, let allauth proceed.
        if sociallogin.is_existing:
            return

        # If the user is already logged in,
        # connect this new social account to it.
        if request.user.is_authenticated:
            sociallogin.connect(request, request.user)
            return

        # Try to match an existing user by email.
        email = (user_email(sociallogin.user) or "").strip()
        if not email:
            return

        try:
            existing = User.objects.get(email__iexact=email)
        except User.DoesNotExist:
            return

        # Only autolink if the provider confirms the email is verified.
        verified = (
            sociallogin.account.extra_data.get("email_verified") is True
            or any(
              getattr(
                e, "verified", False
              ) for e in sociallogin.email_addresses
            )
        )
        if not verified:
            # Fall back to allauth’s default flow
            return

        # Attach and log user in.
        sociallogin.connect(request, existing)
        perform_login(request, existing, email_verification="optional")
