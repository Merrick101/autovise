from django.contrib import admin
from .models import NewsletterSubscriber


@admin.register(NewsletterSubscriber)
class NewsletterSubscriberAdmin(admin.ModelAdmin):
    list_display = ('email', 'subscribed_on', 'gdpr_agreed')
    search_fields = ('email',)
    list_filter = ('subscribed_on', 'gdpr_agreed')
