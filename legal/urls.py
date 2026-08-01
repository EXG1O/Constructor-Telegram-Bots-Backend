from rest_framework.routers import SimpleRouter

from .views import DocumentViewSet

router = SimpleRouter(use_regex_path=False)
router.register('documents', DocumentViewSet, basename='document')

app_name = 'legal'
urlpatterns = router.urls
