from httpcore import ConnectionPool

from typing import Final

TELEGRAM_HTTP_POOL: Final[ConnectionPool] = ConnectionPool(
    max_connections=100, max_keepalive_connections=20, keepalive_expiry=6
)
