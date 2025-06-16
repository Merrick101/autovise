from django.db import models


class NewsletterSubscriber(models.Model):
    email = models.EmailField(unique=True)
    subscribed_on = models.DateTimeField(auto_now_add=True)
    gdpr_agreed = models.BooleanField(default=True)

    def __str__(self):
        return self.email
