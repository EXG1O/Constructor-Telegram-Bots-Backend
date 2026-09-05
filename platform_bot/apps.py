from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class PlatformBotConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'platform_bot'
    verbose_name = _('Бот платформы')
