from django.db.models import IntegerChoices, Model, TextChoices
from django.utils.translation import gettext_lazy as _

from enum import nonmember


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
    TIMER = 'timer', _('Таймер')
    RANDOMIZER = 'randomizer', _('Рандомайзер')

    SOURCE_CHOICES = nonmember(
        [
            TRIGGER,
            MESSAGE,
            MESSAGE_KEYBOARD_BUTTON,
            CONDITION,
            BACKGROUND_TASK,
            API_REQUEST,
            DATABASE_OPERATION,
            INVOICE,
            TEMPORARY_VARIABLE,
            TIMER,
            RANDOMIZER,
        ]
    )
    TARGET_CHOICES = nonmember(
        [
            TRIGGER,
            MESSAGE,
            CONDITION,
            API_REQUEST,
            DATABASE_OPERATION,
            INVOICE,
            TEMPORARY_VARIABLE,
            TIMER,
            RANDOMIZER,
        ]
    )

    _OBJECT_TYPE_MAP = nonmember(
        {
            'telegram_bots.trigger': TRIGGER[0],
            'telegram_bots.message': MESSAGE[0],
            'telegram_bots.messagekeyboardbutton': MESSAGE_KEYBOARD_BUTTON[0],
            'telegram_bots.condition': CONDITION[0],
            'telegram_bots.backgroundtask': BACKGROUND_TASK[0],
            'telegram_bots.apirequest': API_REQUEST[0],
            'telegram_bots.databaseoperation': DATABASE_OPERATION[0],
            'telegram_bots.invoice': INVOICE[0],
            'telegram_bots.temporaryvariable': TEMPORARY_VARIABLE[0],
            'telegram_bots.timer': TIMER[0],
            'telegram_bots.randomizer': RANDOMIZER[0],
        }
    )

    @staticmethod
    def from_model(model: type[Model]) -> ConnectionObjectType:
        return ConnectionObjectType(
            ConnectionObjectType._OBJECT_TYPE_MAP[model._meta.label_lower]
        )


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
