from django.conf import settings
from django.conf.urls.i18n import i18n_patterns
from django.contrib import admin
from django.urls import URLPattern, URLResolver, include, path, re_path
from django.views.generic import RedirectView

import django_stubs_ext

from rest_framework.generics import GenericAPIView

from .enums import Mode
from .views import frontend

django_stubs_ext.monkeypatch(extra_classes=[GenericAPIView])


urlpatterns: list[URLPattern | URLResolver] = [
    path(
        'api/',
        include(
            (
                [
                    path('users/', include('users.urls')),
                    path('webhooks/', include('webhooks.urls')),
                    path('telegram-bots/', include('telegram_bots.urls')),
                    path(
                        'telegram-bots-hub/telegram-bots/',
                        include('telegram_bots.hub.urls'),
                    ),
                    path('donation/', include('donation.urls')),
                    path('instruction/', include('instruction.urls')),
                    path('privacy-policy/', include('privacy_policy.urls')),
                    path('terms-of-service/', include('terms_of_service.urls')),
                ],
                'api',
            )
        ),
    ),
]

if settings.MODE == Mode.DEBUG:
    from django.conf.urls.static import static

    urlpatterns.extend(static(settings.STATIC_URL, document_root=settings.STATIC_ROOT))
    urlpatterns.extend(static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT))
    urlpatterns.append(path('silk/', include('silk.urls', namespace='silk')))

urlpatterns.extend(
    i18n_patterns(
        path('admin/login/', RedirectView.as_view(url='/')),
        path('admin/', admin.site.urls),
    )
)
urlpatterns.append(re_path(r'^.*', frontend))
