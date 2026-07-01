from django.utils.translation import gettext_lazy as _

import django_stubs_ext

from dotenv import load_dotenv
from yarl import URL

from .enums import Mode

from datetime import timedelta
from pathlib import Path
from typing import Any, Final
import os
import sys

django_stubs_ext.monkeypatch()
load_dotenv()


BASE_DIR: Final[Path] = Path(__file__).resolve().parent.parent
LOGS_DIR: Final[Path] = BASE_DIR / 'logs'
SOCKETS_DIR: Final[Path] = BASE_DIR / 'sockets'

os.makedirs(LOGS_DIR, exist_ok=True)
os.makedirs(SOCKETS_DIR, exist_ok=True)


SECRET_KEY: Final[str] = os.environ['SECRET_KEY']

MODE: Final[Mode] = (
    Mode.TEST if 'test' in sys.argv else Mode(os.getenv('MODE', 'debug').lower())
)
DEBUG: Final[bool] = MODE == Mode.DEBUG

FRONTEND_PATH: Final[Path] = Path(os.environ['FRONTEND_PATH'])

TELEGRAM_BOTS_HUB_PATH: Final[Path] = (
    Path(path)
    if (path := os.getenv('TELEGRAM_BOTS_HUB_PATH'))
    else BASE_DIR / 'telegram-bots-hub-microservice'
)
TELEGRAM_BOTS_HUB_TAG: Final[str] = os.getenv(
    'TELEGRAM_BOTS_HUB_TAG', 'telegram-bots-hub-microservice'
)
TELEGRAM_BOTS_HUB_NETWORK: Final[str | None] = os.getenv('TELEGRAM_BOTS_HUB_NETWORK')
TELEGRAM_BOTS_HUB_REDIS_URL: Final[str] = os.environ['TELEGRAM_BOTS_HUB_REDIS_URL']
TELEGRAM_BOTS_HUB_SOCKETS_VOLUME: Final[str | None] = os.getenv(
    'TELEGRAM_BOTS_HUB_SOCKETS_VOLUME'
)
TELEGRAM_BOTS_HUB_LOGS_VOLUME: Final[str | None] = os.getenv(
    'TELEGRAM_BOTS_HUB_LOGS_VOLUME'
)

TELEGRAM_LOGIN_CLIENT_ID: Final[int] = int(os.environ['TELEGRAM_LOGIN_CLIENT_ID'])
TELEGRAM_LOGIN_CLIENT_SECRET: Final[str] = os.environ['TELEGRAM_LOGIN_CLIENT_SECRET']

SELF_URL: Final[URL] = URL(os.environ['SELF_URL'])
SELF_UNIX_SOCK: Final[Path | None] = (
    Path(path) if (path := os.getenv('SELF_UNIX_SOCK')) else None
)

if not (SELF_URL or SELF_UNIX_SOCK):
    raise ValueError('Either SELF_URL or SELF_UNIX_SOCK must be set.')

POSTGRESQL_DATABASE_NAME: Final[str] = os.environ['POSTGRESQL_DATABASE_NAME']
POSTGRESQL_DATABASE_USER: Final[str] = os.environ['POSTGRESQL_DATABASE_USER']
POSTGRESQL_DATABASE_PASSWORD: Final[str] = os.environ['POSTGRESQL_DATABASE_PASSWORD']
POSTGRESQL_DATABASE_HOST: Final[str] = os.environ['POSTGRESQL_DATABASE_HOST']
POSTGRESQL_DATABASE_PORT: Final[str] = os.environ['POSTGRESQL_DATABASE_PORT']

REDIS_URL: Final[str] = os.environ['REDIS_URL']


ALLOWED_HOSTS: Final[list[str]] = (
    ['constructor.exg1o.org'] if MODE == Mode.PRODUCTION else ['*']
)
CSRF_TRUSTED_ORIGINS: Final[list[str]] = ['https://*.exg1o.org']


CSRF_COOKIE_AGE: Final[int] = 2419200  # 4 weeks
SESSION_COOKIE_AGE: Final[int] = 2419200  # 4 weeks

FILE_UPLOAD_MAX_MEMORY_SIZE: Final[int] = 62914560  # 60M

TELEGRAM_BOT_MAX_TRIGGERS: Final[int] = 250
TELEGRAM_BOT_MAX_MESSAGES: Final[int] = 500
TELEGRAM_BOT_MAX_MESSAGE_KEYBOARD_BUTTONS: Final[int] = 100
TELEGRAM_BOT_MAX_CONDITIONS: Final[int] = 750
TELEGRAM_BOT_MAX_CONDITION_PARTS: Final[int] = 25
TELEGRAM_BOT_MAX_BACKGROUND_TASKS: Final[int] = 25
TELEGRAM_BOT_MAX_API_REQUESTS: Final[int] = 100
TELEGRAM_BOT_MAX_DATABASE_OPERATIONS: Final[int] = 250
TELEGRAM_BOT_MAX_INVOICES: Final[int] = 250
TELEGRAM_BOT_MAX_INVOICE_PRICES: Final[int] = 1
TELEGRAM_BOT_MAX_TEMPORARY_VARIABLES: Final[int] = 1000
TELEGRAM_BOT_MAX_VARIABLES: Final[int] = 100
TELEGRAM_BOT_MAX_DATABASE_RECORDS: Final[int] = 1000

TELEGRAM_BOTS_HUB_MAX_BOTS: Final[int] = 200
TELEGRAM_BOTS_HUB_IDLE_TIMEOUT: Final[timedelta] = timedelta(minutes=30)


JWT_REFRESH_TOKEN_LIFETIME: Final[timedelta] = timedelta(weeks=4)
JWT_ACCESS_TOKEN_LIFETIME: Final[timedelta] = timedelta(minutes=15)


CELERY_BROKER_URL: Final[str] = REDIS_URL
CELERY_RESULT_BACKEND: Final[str] = REDIS_URL
CELERY_ACCEPT_CONTENT: Final[list[str]] = ['application/json']
CELERY_RESULT_SERIALIZER: Final[str] = 'json'
CELERY_TASK_SERIALIZER: Final[str] = 'json'
CELERY_BEAT_SCHEDULE: Final[dict[str, dict[str, Any]]] = {
    'delete_expired_tokens_schedule': {
        'task': 'users.tasks.delete_expired_tokens',
        'schedule': 86400,  # 24h
    },
    'delete_users_not_accepted_terms_schedule': {
        'task': 'users.tasks.delete_users_not_accepted_terms',
        'schedule': 86400,  # 24h
    },
    'ensure_idle_telegram_bots_hubs_schedule': {
        'task': 'telegram_bots.hub.tasks.ensure_idle_telegram_bots_hubs',
        'schedule': 3600,  # 1h
    },
    'delete_expired_telegram_bots_hubs_schedule': {
        'task': 'telegram_bots.hub.tasks.delete_expired_telegram_bots_hubs',
        'schedule': TELEGRAM_BOTS_HUB_IDLE_TIMEOUT.total_seconds(),
    },
}

if MODE == Mode.TEST:
    CELERY_TASK_ALWAYS_EAGER = True
    CELERY_TASK_EAGER_PROPAGATES = True


INSTALLED_APPS: Final[list[str]] = [
    'rest_framework',
    'django_filters',
    'drf_standardized_errors',
    'modeltranslation',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'adminsortable2',
    'languages',
    'users',
    'webhooks',
    'telegram_bots',
    'telegram_bots.hub',
    'instruction',
    'donation',
    'privacy_policy',
    'terms_of_service',
]

if MODE == Mode.DEBUG:
    INSTALLED_APPS.append('silk')

REST_FRAMEWORK: Final[dict[str, Any]] = {
    'EXCEPTION_HANDLER': 'drf_standardized_errors.handler.exception_handler'
}


MIDDLEWARE: Final[list[str]] = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'django.middleware.locale.LocaleMiddleware',
]

if MODE == Mode.DEBUG:
    MIDDLEWARE.append('silk.middleware.SilkyMiddleware')


TEMPLATES: Final[list[dict[str, Any]]] = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [FRONTEND_PATH / 'dist'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

AUTHENTICATION_BACKENDS: Final[list[str]] = ['users.backends.TelegramBackend']

AUTH_USER_MODEL: Final[str] = 'users.User'
ROOT_URLCONF: Final[str] = 'constructor_telegram_bots.urls'
WSGI_APPLICATION: Final[str] = 'constructor_telegram_bots.wsgi.application'


CACHES: Final[dict[str, dict[str, Any]]] = {
    'default': {
        'BACKEND': 'django.core.cache.backends.redis.RedisCache',
        'LOCATION': REDIS_URL,
    }
}


DATABASES: Final[dict[str, dict[str, Any]]] = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': POSTGRESQL_DATABASE_NAME,
        'USER': POSTGRESQL_DATABASE_USER,
        'PASSWORD': POSTGRESQL_DATABASE_PASSWORD,
        'HOST': POSTGRESQL_DATABASE_HOST,
        'PORT': POSTGRESQL_DATABASE_PORT,
    },
}
DEFAULT_AUTO_FIELD: Final[str] = 'django.db.models.BigAutoField'


USE_I18N: Final[bool] = True
USE_L10N: Final[bool] = True

LANGUAGE_COOKIE_NAME: Final[str] = 'lang'

LANGUAGES: Final[list[tuple[str, Any]]] = [
    ('en', _('Английский')),
    ('uk', _('Украинский')),
    ('ru', _('Русский')),
]
LANGUAGE_CODE: Final[str] = 'ru-ru'
MODELTRANSLATION_DEFAULT_LANGUAGE: Final[str] = 'ru'
LOCALE_PATHS: Final[list[Path]] = [BASE_DIR / 'locale']


TIME_ZONE: Final[str] = 'UTC'
USE_TZ: Final[bool] = True


STATIC_URL: Final[str] = '/static/'
STATIC_ROOT: Final[Path] = BASE_DIR / 'static'
STATICFILES_DIRS: Final[list[Path | str]] = [FRONTEND_PATH / 'dist']

MEDIA_URL: Final[str] = '/media/'
MEDIA_ROOT: Final[Path] = BASE_DIR / 'media'


LOGGING: Final[dict[str, Any]] = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '[{asctime}]: {levelname}: {name} > {funcName} || {message}',
            'style': '{',
        },
        'simple': {
            'format': '[{asctime}]: {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
            'formatter': 'simple',
        },
        'info_file': {
            'level': 'DEBUG',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': LOGS_DIR / 'app_info.log',
            'maxBytes': 10485760,
            'backupCount': 10,
            'formatter': 'verbose',
        },
        'error_file': {
            'level': 'WARNING',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': LOGS_DIR / 'app_error.log',
            'maxBytes': 10485760,
            'backupCount': 10,
            'formatter': 'verbose',
        },
    },
    'loggers': {
        'root': {
            'handlers': ['console', 'info_file', 'error_file'],
            'level': 'DEBUG' if MODE == Mode.DEBUG else 'INFO',
        }
    },
}
