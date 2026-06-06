from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class TelegramBotsHubConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'telegram_bots.hub'
    label = 'telegram_bots_hub'
    verbose_name = _('Хабы Telegram ботов')
