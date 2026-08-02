from rest_framework.routers import SimpleRouter

from constructor_telegram_bots.routers import DetailRouter

from .views import (
    SubscriptionInvoiceViewSet,
    SubscriptionPriceViewSet,
    SubscriptionViewSet,
)

default_router = SimpleRouter(use_regex_path=False)
default_router.register(
    'subscription-prices', SubscriptionPriceViewSet, basename='subscription-price'
)
default_router.register(
    'subscription-invoices', SubscriptionInvoiceViewSet, basename='subscription-invoice'
)

detail_router = DetailRouter(use_regex_path=False)
detail_router.register('subscriptions', SubscriptionViewSet, basename='subscription')

app_name = 'premium'
urlpatterns = default_router.urls + detail_router.urls
