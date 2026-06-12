from constructor_telegram_bots.settings import LOGS_DIR, SOCKETS_DIR

from multiprocessing import cpu_count
from typing import Final

workers: Final[int] = cpu_count() * 2 + 1
max_requests: Final[int] = 1000
max_requests_jitter: Final[int] = 100

bind: Final[str] = f'unix:{SOCKETS_DIR / "main.sock"}'

capture_output: Final[bool] = True
accesslog: Final[str] = str(LOGS_DIR / 'gunicorn_info.log')
errorlog: Final[str] = str(LOGS_DIR / 'gunicorn_info.log')
