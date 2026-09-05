from rest_framework.routers import SimpleRouter

from .views import InvoiceViewSet, UserViewSet

router = SimpleRouter(use_regex_path=False)
router.register('users', UserViewSet, basename='user')
router.register(
    'users/<int:user_id>/<str:invoice_type>/invoices',
    InvoiceViewSet,
    basename='invoice',
)

app_name = 'platform-bot'
urlpatterns = router.urls
