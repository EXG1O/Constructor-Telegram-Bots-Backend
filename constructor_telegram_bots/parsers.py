from django.core.files.uploadedfile import UploadedFile
from django.utils.datastructures import MultiValueDict
from django.utils.translation import gettext_lazy as _

from rest_framework.exceptions import ParseError
from rest_framework.parsers import DataAndFiles, MultiPartParser

import orjson

from typing import TYPE_CHECKING, Any, Final

if TYPE_CHECKING:
    from django.http.request import _ImmutableQueryDict

type Multipart = DataAndFiles[_ImmutableQueryDict, MultiValueDict[str, UploadedFile]]


class MultiPartJSONParser(MultiPartParser):
    FILE_ATTACHMENT_PREFIX: Final[str] = 'attach://'
    PAYLOAD_FIELD_NAME: Final[str] = '_data'

    def _resolve_attachments(
        self, data: Any, files: MultiValueDict[str, UploadedFile]
    ) -> Any:
        if isinstance(data, dict):
            return {
                key: self._resolve_attachments(value, files)
                for key, value in data.items()
            }
        elif isinstance(data, list):
            return [self._resolve_attachments(item, files) for item in data]
        elif isinstance(data, str) and data.startswith(self.FILE_ATTACHMENT_PREFIX):
            return files.get(data.removeprefix(self.FILE_ATTACHMENT_PREFIX))
        return data

    def parse(self, *args: Any, **kwargs: Any) -> Multipart:
        multipart: Multipart = super().parse(*args, **kwargs)

        raw_data: str | None = multipart.data.get(self.PAYLOAD_FIELD_NAME)

        if not raw_data:
            return multipart

        try:
            return DataAndFiles(
                self._resolve_attachments(orjson.loads(raw_data), multipart.files),
                multipart.files,
            )
        except orjson.JSONDecodeError as error:
            raise ParseError(
                _("Не удалось проанализировать JSON данные из поля '%(field)s'.")
                % {'field': self.PAYLOAD_FIELD_NAME}
            ) from error
