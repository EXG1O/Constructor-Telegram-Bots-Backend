from django.core.exceptions import ValidationError
from django.core.validators import MaxLengthValidator, RegexValidator, URLValidator
from django.db.models import JSONField
from django.utils.deconstruct import deconstructible
from django.utils.translation import gettext_lazy as _

from collections.abc import Callable
from ipaddress import (
    IPv4Address,
    IPv4Network,
    IPv6Address,
    IPv6Network,
    ip_address,
    ip_network,
)
from typing import Any
from urllib.parse import urlparse
import json


@deconstructible
class PublicURLValidator:
    validate_url: Callable[[str | None], None] = URLValidator()
    private_networks: list[IPv4Network | IPv6Network] = [
        ip_network('127.0.0.0/8'),
        ip_network('10.0.0.0/8'),
        ip_network('172.16.0.0/12'),
        ip_network('192.168.0.0/16'),
        ip_network('169.254.0.0/16'),
        ip_network('::1/128'),
        ip_network('fc00::/7'),
        ip_network('fe80::/10'),
    ]

    def __call__(self, url: str | None) -> None:
        self.validate_url(url)
        assert url

        hostname: str | None = urlparse(url).hostname
        assert hostname

        try:
            ip: IPv4Address | IPv6Address = ip_address(hostname)
        except ValueError:
            return

        for network in self.private_networks:
            if ip in network:
                raise ValidationError(
                    URLValidator.message, code=URLValidator.code, params={'value': url}
                )


@deconstructible
class StrictJSONValidator:
    code = 'invalid'
    message = JSONField.default_error_messages[code]

    def __init__(
        self,
        max_length: int,
        allowed_types: tuple[type[dict[Any, Any]] | type[list[Any]], ...],
    ):
        self.allowed_types = allowed_types
        self.validate_max_length = MaxLengthValidator(max_length)

    def __call__(self, value: Any) -> None:
        if not isinstance(value, self.allowed_types):
            raise ValidationError(self.message, code=self.code)

        self.validate_max_length(json.dumps(value))


validate_no_special_chars = RegexValidator(
    regex=r'^[\w ]+$', message=_('Разрешены только буквы, цифры, пробел и _.')
)
