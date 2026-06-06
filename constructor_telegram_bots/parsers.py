from django.core.files.uploadedfile import UploadedFile
from django.http import QueryDict
from django.utils.datastructures import MultiValueDict
from django.utils.translation import gettext_lazy as _

from rest_framework.exceptions import ParseError
from rest_framework.parsers import DataAndFiles, MultiPartParser

from json import JSONDecodeError
from typing import Any
import json
import re

MEDIA_DATA_FIELD_PATTERN: re.Pattern[str] = re.compile(
    r'^(?P<name>\w+)(:(?P<index>\d+))?:data$', re.IGNORECASE
)


class MultiPartJSONParser(MultiPartParser):
    """Parser for JSON data in multipart form data with support for files and their data."""

    def _parse_json(self, field: str, value: str) -> dict[str, Any]:
        try:
            return json.loads(value)
        except JSONDecodeError as error:
            raise ParseError(
                _("Не удалось проанализировать JSON данные для поля '%(field)s'.")
                % {'field': field}
            ) from error

    def parse(self, *args: Any, **kwargs: Any) -> dict[str, Any]:  # type: ignore [override]
        """Parses the incoming bytestream as a multipart encoded form, and returns a dict object."""

        multipart: DataAndFiles[QueryDict, MultiValueDict[str, UploadedFile]] = (
            super().parse(*args, **kwargs)  # type: ignore [assignment]
        )

        result: dict[str, Any] = (
            self._parse_json('data', raw_data)
            if (raw_data := multipart.data.get('data'))
            else {}
        )

        for key, value in multipart.data.items():
            if not isinstance(value, str):
                continue

            match: re.Match[str] | None = MEDIA_DATA_FIELD_PATTERN.fullmatch(key)

            if not match:
                continue

            name, index = match.group('name', 'index')

            media_data: dict[str, Any] = self._parse_json(key, value)
            media_data['file'] = multipart.files.get(
                f'{name}:{index}' if index else name
            )

            if index:
                media: list[dict[str, Any]] = result.setdefault(name, [])
                media.append(media_data)
            else:
                result[name] = media_data

        return result
