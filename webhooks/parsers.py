from django.conf import settings

from rest_framework.parsers import BaseParser

from constructor_telegram_bots.exceptions import ContentTooLargeError

from collections.abc import Mapping
from typing import IO, Any


class TriggerWebhookParser(BaseParser):
    media_type = '*/*'
    MAX_SIZE = 4096

    def parse(  # type: ignore [override]
        self,
        stream: IO[Any],
        media_type: str | None = None,
        parser_context: Mapping[str, Any] | None = None,
    ) -> str:
        raw_data: bytes = stream.read(self.MAX_SIZE + 1)

        if len(raw_data) > self.MAX_SIZE:
            raise ContentTooLargeError(max_size=self.MAX_SIZE)

        encoding: str = (parser_context or {}).get('encoding', settings.DEFAULT_CHARSET)
        return raw_data.decode(encoding, errors='replace')
