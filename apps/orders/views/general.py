# apps/orders/views/general.py

from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from apps.orders.models import Order


def checkout_success_view(request):
    # This assumes the session ID was stored during webhook processing
    # or passed as a query parameter after successful payment.
    session_id = request.GET.get('session_id')
    order = Order.objects.filter(stripe_session_id=session_id).first()

    context = {
        'order': order,
        'support_email': 'hello.autovise@gmail.com',
        'contact_page_url': '/contact/',
    }
    return render(request, 'orders/checkout_success.html', context)


@login_required
def order_history_view(request):
    return render(request, 'orders/order_history.html')
