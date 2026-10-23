from .api_request import APIRequestViewSetTestCase, DiagramAPIRequestViewSetTestCase
from .background_task import (
    BackgroundTaskViewSetTestCase,
    DiagramBackgroundTaskViewSetTestCase,
)
from .chat import ChatViewSetTestCase
from .condition import ConditionViewSetTestCase, DiagramConditionViewSetTestCase
from .connection import ConnectionViewSetTestCase
from .database_operation import (
    DatabaseOperationViewSetTestCase,
    DiagramDatabaseOperationViewSetTestCase,
)
from .database_record import DatabaseRecordViewSetTestCase
from .enums import ConnectionObjectTypeTestCase
from .invoice import DiagramInvoiceViewSetTestCase, InvoiceViewSetTestCase
from .message import DiagramMessageViewSetTestCase, MessageViewSetTestCase
from .randomizer import DiagramRandomizerViewSetTestCase, RandomizerViewSetTestCase
from .stats import StatsAPIViewTestCase
from .tasks import (
    MigrateTelegramBotsTaskTestCase,
    RestartTelegramBotTaskTestCase,
    StartTelegramBotTaskTestCase,
    StopTelegramBotTaskTestCase,
)
from .telegram_bot import TelegramBotViewSetTestCase
from .temporary_variable import (
    DiagramTemporaryVariableViewSetTestCase,
    TemporaryVariableViewSetTestCase,
)
from .timer import DiagramTimerViewSetTestCase, TimerViewSetTestCase
from .trigger import DiagramTriggerViewSetTestCase, TriggerViewSetTestCase
from .user import UserViewSetTestCase
from .variable import VariableViewSetTestCase

__all__ = [
    'ConnectionObjectTypeTestCase',
    'StartTelegramBotTaskTestCase',
    'RestartTelegramBotTaskTestCase',
    'StopTelegramBotTaskTestCase',
    'MigrateTelegramBotsTaskTestCase',
    'StatsAPIViewTestCase',
    'TelegramBotViewSetTestCase',
    'ConnectionViewSetTestCase',
    'MessageViewSetTestCase',
    'DiagramMessageViewSetTestCase',
    'ConditionViewSetTestCase',
    'DiagramConditionViewSetTestCase',
    'BackgroundTaskViewSetTestCase',
    'DiagramBackgroundTaskViewSetTestCase',
    'APIRequestViewSetTestCase',
    'DiagramAPIRequestViewSetTestCase',
    'DatabaseOperationViewSetTestCase',
    'DiagramDatabaseOperationViewSetTestCase',
    'TriggerViewSetTestCase',
    'DiagramTriggerViewSetTestCase',
    'InvoiceViewSetTestCase',
    'DiagramInvoiceViewSetTestCase',
    'TemporaryVariableViewSetTestCase',
    'DiagramTemporaryVariableViewSetTestCase',
    'TimerViewSetTestCase',
    'DiagramTimerViewSetTestCase',
    'RandomizerViewSetTestCase',
    'DiagramRandomizerViewSetTestCase',
    'VariableViewSetTestCase',
    'ChatViewSetTestCase',
    'UserViewSetTestCase',
    'DatabaseRecordViewSetTestCase',
]
