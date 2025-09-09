"""
Admin configuration for NewsletterSubscriber and ContactMessage models.
Includes custom admin actions for sending test newsletters
and managing contact message statuses.
Located at apps/pages/admin.py
"""

from django.contrib import admin
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.timezone import now
from .models import NewsletterSubscriber, ContactMessage


@admin.action(description="Send test newsletter to selected subscribers")
def send_test_newsletter(modeladmin, request, queryset):
    from_email = "hello.autovise@gmail.com"
    subject = "🚗 Autovise – Latest Updates & Offers"

    sent = 0
    for subscriber in queryset:
        html_content = render_to_string("emails/newsletter_email.html", {
            "subscriber": subscriber,
            "current_year": now().year,
        })

        send_mail(
            subject=subject,
            message="(View in HTML format)",  # fallback plain message
            html_message=html_content,
            from_email=from_email,
            recipient_list=[subscriber.email],
            fail_silently=False
        )
        sent += 1

    modeladmin.message_user(request, f" Newsletter sent to {sent} subscribers.")


@admin.register(NewsletterSubscriber)
class NewsletterSubscriberAdmin(admin.ModelAdmin):
    list_display = ['email', 'subscribed_on', 'gdpr_agreed']
    actions = [send_test_newsletter]
    list_filter = ('subscribed_on', 'gdpr_agreed')


@admin.register(ContactMessage)
class ContactMessageAdmin(admin.ModelAdmin):
    list_display = ("id", "subject", "email", "name", "status", "created_at")
    list_filter = ("status", "created_at")
    search_fields = ("subject", "email", "name", "message")
    readonly_fields = ("created_at", "updated_at", "ip_address", "user_agent", "user")
    date_hierarchy = "created_at"
    ordering = ("-created_at",)

    @admin.action(description="Mark selected as New")
    def mark_new(self, request, queryset):
        updated = queryset.update(status="new")
        self.message_user(request, f"{updated} message(s) marked as New.")

    @admin.action(description="Mark selected as Open")
    def mark_open(self, request, queryset):
        updated = queryset.update(status="open")
        self.message_user(request, f"{updated} message(s) marked as Open.")

    @admin.action(description="Mark selected as Resolved")
    def mark_resolved(self, request, queryset):
        updated = queryset.update(status="resolved")
        self.message_user(request, f"{updated} message(s) marked as Resolved.")

    actions = ["mark_new", "mark_open", "mark_resolved"]
