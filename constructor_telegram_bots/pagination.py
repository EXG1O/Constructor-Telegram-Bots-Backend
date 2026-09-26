from rest_framework.pagination import LimitOffsetPagination as BaseLimitOffsetPagination
from rest_framework.response import Response

from drf_spectacular.plumbing import build_basic_type, build_object_type
from drf_spectacular.types import OpenApiTypes

from typing import Any


class LimitOffsetPagination(BaseLimitOffsetPagination):
    def get_paginated_response(self, data: list[dict[str, Any]]) -> Response:
        return Response({'count': self.count, 'results': data})

    def get_paginated_response_schema(self, schema: dict[str, Any]) -> dict[str, Any]:
        return build_object_type(
            properties={'count': build_basic_type(OpenApiTypes.INT), 'results': schema},
            required=['count', 'results'],
        )
