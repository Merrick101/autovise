# apps/pages/views.py

from django.conf import settings
from django.shortcuts import render, redirect
from django.contrib import messages
from apps.products.models import Product, Bundle
from django.views.decorators.http import require_POST
from django.core.mail import send_mail
from django.utils.html import strip_tags
from .models import NewsletterSubscriber, ContactMessage
from .forms import NewsletterForm, ContactForm


def home(request):
    featured_products = Product.objects.filter(featured=True, is_draft=False)[:4]
    featured_bundles = Bundle.objects.filter(featured=True)[:4]

    context = {
        'promo_banner': "🎁 Free Delivery on First-Time Orders | 🚚 Orders over £40 ship free",
        'featured_products': featured_products,
        'featured_bundles': featured_bundles,
        'newsletter_form': NewsletterForm(),
    }
    return render(request, 'pages/home.html', context)


@require_POST
def subscribe_newsletter(request):
    form = NewsletterForm(request.POST)
    if form.is_valid():
        email = form.cleaned_data['email']
        NewsletterSubscriber.objects.get_or_create(email=email)

    messages.success(request, "Thanks for subscribing to our newsletter!")

    return redirect(request.META.get("HTTP_REFERER", "/"))


def privacy_policy(request):
    return render(request, 'pages/privacy.html')


def terms_and_conditions(request):
    return render(request, 'pages/terms.html')


def _client_ip(request):
    xff = request.META.get("HTTP_X_FORWARDED_FOR")
    if xff:
        # typical format: "client, proxy1, proxy2"
        return xff.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR")


def contact(request):
    if request.method == "POST":
        form = ContactForm(request.POST)
        if form.is_valid():
            cd = form.cleaned_data

            # 1) Save submission
            ContactMessage.objects.create(
                name=cd["name"],
                email=cd["email"],
                subject=cd["subject"],
                message=cd["message"],
                user=request.user if request.user.is_authenticated else None,
                ip_address=_client_ip(request),
                user_agent=(request.META.get("HTTP_USER_AGENT") or "")[:500],
            )

            # 2) Send notification email
            subj = f"[Autovise Contact] {cd['subject']}"
            body = (
                f"From: {cd['name']} <{cd['email']}>\n"
                f"Path: {request.get_full_path()}\n"
                f"User: {request.user if request.user.is_authenticated else 'Anonymous'}\n\n"
                f"{strip_tags(cd['message'])}"
            )

            # Configure in settings
            recipients = getattr(
                settings, "CONTACT_RECIPIENTS",
                [getattr(settings, "DEFAULT_FROM_EMAIL", "hello.autovise@gmail.com")]
            )
            from_email = getattr(settings, "DEFAULT_FROM_EMAIL", cd["email"])

            try:
                send_mail(
                    subject=subj,
                    message=body,
                    from_email=from_email,
                    recipient_list=recipients,
                    fail_silently=False,
                    reply_to=[cd["email"]],
                )
                messages.success(request, "Thanks! Your message has been sent.")
                return redirect("pages:contact")
            except Exception:
                messages.error(
                    request,
                    "We couldn’t send your message right now. "
                    "Please email us directly at hello.autovise@gmail.com."
                )
    else:
        form = ContactForm()

    return render(
        request, "pages/contact.html", {"form": form, "support_email": "hello.autovise@gmail.com"}
    )


def custom_404(request, exception):
    return render(request, "404.html", status=404)


def custom_500(request):
    return render(request, "500.html", status=500)
