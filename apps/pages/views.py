from django.shortcuts import render


def home(request):
    context = {
        'promo_banner': "🎁 Free Delivery on First-Time Orders | 🚚 Orders over £40 ship free"
    }
    return render(request, 'pages/home.html', context)
