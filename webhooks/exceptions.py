from rest_framework.exceptions import PermissionDenied


class TelegramBotDisabledError(PermissionDenied):
    default_detail = 'Telegram bot is disabled.'
    default_code = 'tg_bot_disabled'
