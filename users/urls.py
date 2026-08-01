from django.urls import path

from rest_framework.routers import SimpleRouter

from constructor_telegram_bots.routers import DetailRouter

from .views import StatsAPIView, TokenViewSet, UserViewSet

user_router = DetailRouter(use_regex_path=False)
user_router.register('', UserViewSet, basename='user')

default_router = SimpleRouter(use_regex_path=False)
default_router.register('tokens', TokenViewSet, basename='token')

app_name = 'users'
urlpatterns = (
    [path('stats/', StatsAPIView.as_view(), name='stats')]
    + user_router.urls
    + default_router.urls
)
