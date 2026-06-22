from django.urls import path

from rest_framework.routers import SimpleRouter

from .views import (
    APIRequestViewSet,
    BackgroundTaskViewSet,
    ChatViewSet,
    ConditionViewSet,
    ConnectionViewSet,
    DatabaseOperationViewSet,
    DatabaseRecordViewSet,
    DiagramAPIRequestViewSet,
    DiagramBackgroundTaskViewSet,
    DiagramConditionViewSet,
    DiagramDatabaseOperationViewSet,
    DiagramInvoiceViewSet,
    DiagramMessageViewSet,
    DiagramTemporaryVariableViewSet,
    DiagramTriggerViewSet,
    InvoiceViewSet,
    MessageViewSet,
    StatsAPIView,
    TelegramBotViewSet,
    TemporaryVariableViewSet,
    TriggerViewSet,
    UserViewSet,
    VariableViewSet,
)

base_path: str = '<int:telegram_bot_id>'
base_name: str = 'telegram-bot'

base_diagram_path: str = f'{base_path}/diagram'
base_diagram_name: str = f'{base_name}-diagram'

router = SimpleRouter(use_regex_path=False)
router.register('', TelegramBotViewSet, basename=base_name)
router.register(
    f'{base_path}/connections',
    ConnectionViewSet,
    basename=f'{base_name}-connection',
)

router.register(
    f'{base_path}/triggers',
    TriggerViewSet,
    basename=f'{base_name}-trigger',
)
router.register(
    f'{base_diagram_path}/triggers',
    DiagramTriggerViewSet,
    basename=f'{base_diagram_name}-trigger',
)

router.register(
    f'{base_path}/messages',
    MessageViewSet,
    basename=f'{base_name}-message',
)
router.register(
    f'{base_diagram_path}/messages',
    DiagramMessageViewSet,
    basename=f'{base_diagram_name}-message',
)

router.register(
    f'{base_path}/conditions',
    ConditionViewSet,
    basename=f'{base_name}-condition',
)
router.register(
    f'{base_diagram_path}/conditions',
    DiagramConditionViewSet,
    basename=f'{base_diagram_name}-condition',
)

router.register(
    f'{base_path}/background-tasks',
    BackgroundTaskViewSet,
    basename=f'{base_name}-background-task',
)
router.register(
    f'{base_diagram_path}/background-tasks',
    DiagramBackgroundTaskViewSet,
    basename=f'{base_diagram_name}-background-task',
)

router.register(
    f'{base_path}/api-requests',
    APIRequestViewSet,
    basename=f'{base_name}-api-request',
)
router.register(
    f'{base_diagram_path}/api-requests',
    DiagramAPIRequestViewSet,
    basename=f'{base_diagram_name}-api-request',
)

router.register(
    f'{base_path}/database-operations',
    DatabaseOperationViewSet,
    basename=f'{base_name}-database-operation',
)
router.register(
    f'{base_diagram_path}/database-operations',
    DiagramDatabaseOperationViewSet,
    basename=f'{base_diagram_name}-database-operation',
)

router.register(
    f'{base_path}/invoices',
    InvoiceViewSet,
    basename=f'{base_name}-invoice',
)
router.register(
    f'{base_diagram_path}/invoices',
    DiagramInvoiceViewSet,
    basename=f'{base_diagram_name}-invoice',
)

router.register(
    f'{base_path}/temporary-variables',
    TemporaryVariableViewSet,
    basename=f'{base_name}-temporary-variable',
)
router.register(
    f'{base_diagram_path}/temporary-variables',
    DiagramTemporaryVariableViewSet,
    basename=f'{base_diagram_name}-temporary-variable',
)

router.register(
    f'{base_path}/variables',
    VariableViewSet,
    basename=f'{base_name}-variable',
)
router.register(f'{base_path}/chats', ChatViewSet, basename=f'{base_name}-chat')
router.register(f'{base_path}/users', UserViewSet, basename=f'{base_name}-user')
router.register(
    f'{base_path}/database-records',
    DatabaseRecordViewSet,
    basename=f'{base_name}-database-record',
)

app_name = 'telegram-bots'
urlpatterns = [path('stats/', StatsAPIView.as_view(), name='stats')] + router.urls
