from django.contrib import admin
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.timezone import now
from .models import NewsletterSubscriber


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
