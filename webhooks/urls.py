from django.urls import path

from .views import TriggerWebhookAPIView

app_name = 'webhooks'
urlpatterns = [
    path(
        'triggers/<int:id>/<str:token>/',
        TriggerWebhookAPIView.as_view(),
        name='trigger',
    )
]
