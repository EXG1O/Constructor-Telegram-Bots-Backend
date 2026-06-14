from users.models import User

from ..enums import ChatType, ConditionPartOperatorType, ConditionPartType
from ..models import (
    APIRequest,
    BackgroundTask,
    Condition,
    ConditionPart,
    DatabaseCreateOperation,
    DatabaseOperation,
    DatabaseRecord,
    Invoice,
    InvoicePrice,
    Message,
    MessageSettings,
    TelegramBot,
    TemporaryVariable,
    Trigger,
    TriggerCommand,
    Variable,
)
from ..models import Chat as BotChat
from ..models import User as BotUser

from typing import TYPE_CHECKING
from unittest.mock import patch


class TelegramBotMixin:
    if TYPE_CHECKING:
        user: User

    def setUp(self) -> None:
        super().setUp()  # type: ignore [misc]

        self.patcher_bot_update_username = patch.object(TelegramBot, 'update_username')
        self.mock_bot_update_username = self.patcher_bot_update_username.start()

        self.telegram_bot: TelegramBot = self.user.telegram_bots.create(api_token='Hi!')

    def tearDown(self) -> None:
        super().tearDown()  # type: ignore [misc]
        self.patcher_bot_update_username.stop()


class TriggerMixin:
    if TYPE_CHECKING:
        telegram_bot: TelegramBot

    def setUp(self) -> None:
        super().setUp()  # type: ignore [misc]
        self.trigger: Trigger = self.telegram_bot.triggers.create(name='Test name')
        self.trigger_command: TriggerCommand = TriggerCommand.objects.create(
            trigger=self.trigger, command='start'
        )


class MessageMixin:
    if TYPE_CHECKING:
        telegram_bot: TelegramBot

    def setUp(self) -> None:
        super().setUp()  # type: ignore [misc]
        self.message: Message = self.telegram_bot.messages.create(
            name='Test name', text='...'
        )
        self.message_settings: MessageSettings = MessageSettings.objects.create(
            message=self.message
        )


class ConditionMixin:
    if TYPE_CHECKING:
        telegram_bot: TelegramBot

    def setUp(self) -> None:
        super().setUp()  # type: ignore [misc]
        self.condition: Condition = self.telegram_bot.conditions.create(
            name='Test name'
        )
        self.condition_part: ConditionPart = self.condition.parts.create(
            type=ConditionPartType.POSITIVE,
            first_value='first_value',
            operator=ConditionPartOperatorType.NOT_EQUAL,
            second_value='second_value',
        )


class BackgroundTaskMixin:
    if TYPE_CHECKING:
        telegram_bot: TelegramBot

    def setUp(self) -> None:
        super().setUp()  # type: ignore [misc]
        self.background_task: BackgroundTask = (
            self.telegram_bot.background_tasks.create(name='Test name', interval=1)
        )


class APIRequestMixin:
    if TYPE_CHECKING:
        telegram_bot: TelegramBot

    def setUp(self) -> None:
        super().setUp()  # type: ignore [misc]
        self.api_request: APIRequest = self.telegram_bot.api_requests.create(
            name='Test name', url='https://example.com'
        )


class DatabaseOperationMixin:
    if TYPE_CHECKING:
        telegram_bot: TelegramBot

    def setUp(self) -> None:
        super().setUp()  # type: ignore [misc]
        self.database_operation: DatabaseOperation = (
            self.telegram_bot.database_operations.create(name='Test name')
        )
        self.database_create_operation: DatabaseCreateOperation = (
            DatabaseCreateOperation.objects.create(
                operation=self.database_operation, data={'key': 'value'}
            )
        )


class InvoiceMixin:
    if TYPE_CHECKING:
        telegram_bot: TelegramBot

    def setUp(self) -> None:
        super().setUp()  # type: ignore [misc]
        self.invoice: Invoice = self.telegram_bot.invoices.create(
            name='Test name', title='Test title', description='...'
        )
        self.invoice_price: InvoicePrice = self.invoice.prices.create(
            label='My love', amount=9999999
        )


class TemporaryVariableMixin:
    if TYPE_CHECKING:
        telegram_bot: TelegramBot

    def setUp(self) -> None:
        super().setUp()  # type: ignore [misc]
        self.temporary_variable: TemporaryVariable = (
            self.telegram_bot.temporary_variables.create(
                name='test_name', value='value'
            )
        )


class VariableMixin:
    if TYPE_CHECKING:
        telegram_bot: TelegramBot

    def setUp(self) -> None:
        super().setUp()  # type: ignore [misc]
        self.variable: Variable = self.telegram_bot.variables.create(
            name='Test name', value='The test value :)', description='The test variable'
        )


class BotChatMixin:
    if TYPE_CHECKING:
        telegram_bot: TelegramBot

    def setUp(self) -> None:
        super().setUp()  # type: ignore [misc]
        self.bot_chat: BotChat = self.telegram_bot.chats.create(
            telegram_id=123456789,
            type=ChatType.PRIVATE,
            title='Test Chat',
        )


class BotUserMixin:
    if TYPE_CHECKING:
        telegram_bot: TelegramBot

    def setUp(self) -> None:
        super().setUp()  # type: ignore [misc]
        self.bot_user: BotUser = self.telegram_bot.users.create(telegram_id=123456789)


class DatabaseRecordMixin:
    if TYPE_CHECKING:
        telegram_bot: TelegramBot

    def setUp(self) -> None:
        super().setUp()  # type: ignore [misc]
        self.database_record: DatabaseRecord = (
            self.telegram_bot.database_records.create(data={'key': 'value'})
        )
