"""
Admin configuration for user-related models and social accounts.
Located at: apps/users/admin.py
"""

from django.contrib import admin
from allauth.socialaccount.models import SocialAccount
from apps.users.models import UserProfile, ShippingAddress

# Unregister the default SocialAccount admin
admin.site.unregister(SocialAccount)


# Re-register with custom admin
@admin.register(SocialAccount)
class CustomSocialAccountAdmin(admin.ModelAdmin):
    list_display = ('user', 'provider', 'uid', 'last_login')
    search_fields = ('user__username', 'provider', 'uid')
    list_filter = ('provider',)


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'is_first_time_buyer')


@admin.register(ShippingAddress)
class ShippingAddressAdmin(admin.ModelAdmin):
    list_display = ("user", "name", "postcode", "country", "is_default")
    list_filter = ("is_default", "country")
    search_fields = ("user__username", "name", "postcode")
