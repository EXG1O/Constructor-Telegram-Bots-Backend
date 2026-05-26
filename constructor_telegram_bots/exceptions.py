from django.utils.translation import gettext_lazy as _

from rest_framework import status
from rest_framework.exceptions import APIException


class ContentTooLargeError(APIException):
    status_code = status.HTTP_413_REQUEST_ENTITY_TOO_LARGE
    default_detail = _('Максимально допустимый размер {max_size} байт.')
    default_code = 'content_too_large'

    def __init__(
        self,
        detail: str | None = None,
        max_size: int | None = None,
        code: str | None = None,
    ) -> None:
        if detail is None:
            detail = self.default_detail.format(max_size=max_size)
        super().__init__(detail, code)
