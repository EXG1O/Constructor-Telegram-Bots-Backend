from django.db.models import IntegerChoices, TextChoices
from django.utils.translation import gettext_lazy as _

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from django.utils.functional import _StrPromise
else:
    _StrPromise = str


class APIRequestMethod(TextChoices):
    GET = 'get', 'GET'
    POST = 'post', 'POST'
    PUT = 'put', 'PUT'
    PATCH = 'patch', 'PATCH'
    DELETE = 'delete', 'DELETE'


class ConnectionHandlePosition(TextChoices):
    LEFT = 'left', _('Слева')
    RIGHT = 'right', _('Справа')


class ConnectionObjectType(TextChoices):
    TRIGGER = 'trigger', _('Триггер')
    MESSAGE = 'message', _('Сообщение')
    MESSAGE_KEYBOARD_BUTTON = (
        'message_keyboard_button',
        _('Кнопка клавиатуры сообщения'),
    )
    CONDITION = 'condition', _('Условие')
    BACKGROUND_TASK = 'background_task', _('Фоновая задача')
    API_REQUEST = 'api_request', _('API-запрос')
    DATABASE_OPERATION = 'database_operation', _('Операция базы данных')
    INVOICE = 'invoice', _('Счёт')
    TEMPORARY_VARIABLE = 'temporary_variable', _('Временная переменная')

    @staticmethod
    def source_choices() -> list[tuple[str, _StrPromise]]:
        return [
            (item.value, item.label)
            for item in [
                ConnectionObjectType.TRIGGER,
                ConnectionObjectType.MESSAGE,
                ConnectionObjectType.MESSAGE_KEYBOARD_BUTTON,
                ConnectionObjectType.CONDITION,
                ConnectionObjectType.BACKGROUND_TASK,
                ConnectionObjectType.API_REQUEST,
                ConnectionObjectType.DATABASE_OPERATION,
                ConnectionObjectType.INVOICE,
                ConnectionObjectType.TEMPORARY_VARIABLE,
            ]
        ]

    @staticmethod
    def target_choices() -> list[tuple[str, _StrPromise]]:
        return [
            (item.value, item.label)
            for item in [
                ConnectionObjectType.TRIGGER,
                ConnectionObjectType.MESSAGE,
                ConnectionObjectType.CONDITION,
                ConnectionObjectType.API_REQUEST,
                ConnectionObjectType.DATABASE_OPERATION,
                ConnectionObjectType.INVOICE,
                ConnectionObjectType.TEMPORARY_VARIABLE,
            ]
        ]


class KeyboardType(TextChoices):
    DEFAULT = 'default', _('Обычный')
    INLINE = 'inline', _('Встроенный')
    PAYMENT = 'payment', _('Платёжный')


class KeyboardButtonStyle(TextChoices):
    DEFAULT = 'default', _('По умолчанию')
    PRIMARY = 'primary', _('Основной')
    SUCCESS = 'success', _('Успех')
    DANGER = 'danger', _('Опасность')


class ConditionPartType(TextChoices):
    POSITIVE = '+', _('Положительный')
    NEGATIVE = '-', _('Отрицательный')


class ConditionPartOperatorType(TextChoices):
    EQUAL = '==', _('Равно')
    NOT_EQUAL = '!=', _('Не равно')
    GREATER = '>', _('Больше')
    GREATER_OR_EQUAL = '>=', _('Больше или равно')
    LESS = '<', _('Меньше')
    LESS_OR_EQUAL = '<=', _('Меньше или равно')


class ConditionPartNextPartOperator(TextChoices):
    AND = '&&', _('И')
    OR = '||', _('ИЛИ')


class BackgroundTaskInterval(IntegerChoices):
    DAY_1 = 1, _('1 день')
    DAYS_3 = 3, _('3 дня')
    DAYS_7 = 7, _('7 дней')
    DAYS_14 = 14, _('14 дней')
    DAYS_28 = 28, _('28 дней')


class ChatType(TextChoices):
    PRIVATE = 'private', _('Приватный')
    GROUP = 'group', _('Группа')
    SUPERGROUP = 'supergroup', _('Супергруппа')
    CHANNEL = 'channel', _('Канал')
