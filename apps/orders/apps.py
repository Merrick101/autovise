# apps/orders/apps.py

from django.apps import AppConfig


class OrdersConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.orders'


def ready(self):
    import apps.orders.signals  # noqa: F401
