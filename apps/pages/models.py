"""
Models for the pages app, including newsletter subscribers
and contact messages.
Located at apps/pages/models.py
"""

from django.db import models
from django.conf import settings


class NewsletterSubscriber(models.Model):
    email = models.EmailField(unique=True)
    subscribed_on = models.DateTimeField(auto_now_add=True)
    gdpr_agreed = models.BooleanField(default=True)

    def __str__(self):
        return self.email


class ContactMessage(models.Model):
    STATUS_CHOICES = [
        ("new", "New"),
        ("open", "Open"),
        ("resolved", "Resolved"),
    ]

    name = models.CharField(max_length=100)
    email = models.EmailField()
    subject = models.CharField(max_length=200)
    message = models.TextField()

    # Metadata
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True,
        on_delete=models.SET_NULL, related_name="contact_messages"
    )
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True, default="")

    status = models.CharField(
        max_length=10, choices=STATUS_CHOICES, default="new"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("-created_at",)
        indexes = [models.Index(fields=["status", "created_at"])]

    def __str__(self) -> str:
        return f"{self.subject} — {self.email}"
