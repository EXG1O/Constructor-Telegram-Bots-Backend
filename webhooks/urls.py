from django.urls import path

from .views import TelegramAPIView, TriggerWebhookAPIView

app_name = 'webhooks'
urlpatterns = [
    path('bots/<int:bot_id>/telegram/', TelegramAPIView.as_view(), name='telegram'),
    path(
        'triggers/<int:id>/<str:token>/',
        TriggerWebhookAPIView.as_view(),
        name='trigger',
    ),
]
