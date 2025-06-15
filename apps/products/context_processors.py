# apps/products/context_processors.py

from .models import Category


def all_categories(request):
    return {
        'categories': Category.objects.all()
    }
