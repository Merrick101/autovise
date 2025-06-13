# apps/orders/views/general.py

from django.contrib import messages
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from apps.orders.models import Order


def checkout_success_view(request):
    # This assumes the session ID was stored during webhook processing
    # or passed as a query parameter after successful payment.
    session_id = request.GET.get('session_id')

    if not session_id:
        messages.warning(request, "We couldn’t locate your order. Please check your email or contact support.")
        return redirect('products:product_list')

    order = Order.objects.filter(stripe_session_id=session_id).first()

    if not order:
        messages.warning(request, "Order not found for this session. Please contact support if this was unexpected.")
        return redirect('products:product_list')

    context = {
        'order': order,
        'support_email': 'hello.autovise@gmail.com',
        'contact_page_url': '/contact/',
    }
    return render(request, 'orders/checkout_success.html', context)
