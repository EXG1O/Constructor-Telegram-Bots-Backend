from django.conf import settings

import httpx

telegram_client = httpx.Client(
    base_url='https://api.telegram.org',
    headers={'User-Agent': settings.APP_USER_AGENT},
    limits=httpx.Limits(
        max_connections=25, max_keepalive_connections=10, keepalive_expiry=6
    ),
    trust_env=False,
)
