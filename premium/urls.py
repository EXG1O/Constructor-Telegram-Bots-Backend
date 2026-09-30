from rest_framework.routers import SimpleRouter

from .views import SubscriptionInvoiceViewSet, SubscriptionPriceViewSet

router = SimpleRouter(use_regex_path=False)
router.register(
    'subscription-prices', SubscriptionPriceViewSet, basename='subscription-price'
)
router.register(
    'subscription-invoices', SubscriptionInvoiceViewSet, basename='subscription-invoice'
)

app_name = 'premium'
urlpatterns = router.urls
