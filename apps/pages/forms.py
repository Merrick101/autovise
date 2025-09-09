"""
Forms for user interactions such as newsletter subscription
and contact messages.
Located at apps/pages/forms.py
"""

from django import forms
from .models import NewsletterSubscriber


class NewsletterForm(forms.ModelForm):
    class Meta:
        model = NewsletterSubscriber
        fields = ['email']
        widgets = {
            'email': forms.EmailInput(attrs={
                'placeholder': 'Enter your email',
                'class': 'form-control',
            })
        }


class ContactForm(forms.Form):
    name = forms.CharField(max_length=100, label="Your name")
    email = forms.EmailField(label="Email address")
    subject = forms.CharField(max_length=120, label="Subject")
    message = forms.CharField(
        label="Message", widget=forms.Textarea(attrs={"rows": 5})
    )
    # Honeypot to deter simple bots
    website = forms.CharField(required=False, widget=forms.HiddenInput)

    def clean_website(self):
        if self.cleaned_data.get("website"):
            # Any value means a bot filled it
            raise forms.ValidationError("Please leave this field empty.")
        return ""
