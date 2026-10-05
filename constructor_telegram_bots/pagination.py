from rest_framework.pagination import LimitOffsetPagination as BaseLimitOffsetPagination
from rest_framework.response import Response
from rest_framework.views import APIView

from drf_spectacular.plumbing import build_basic_type, build_object_type
from drf_spectacular.types import OpenApiTypes

from typing import Any


class LimitOffsetPagination(BaseLimitOffsetPagination):
    max_limit: int = 150
    default_limit: int = 50

    def get_paginated_response(self, data: list[dict[str, Any]]) -> Response:
        return Response(
            {
                'count': self.count,
                'limit': self.limit,
                'offset': self.offset,
                'results': data,
            }
        )

    def get_schema_operation_parameters(self, view: APIView) -> list[dict[str, Any]]:
        result: list[dict[str, Any]] = super().get_schema_operation_parameters(view)

        for item in result:
            if item['name'] == self.limit_query_param:
                item['schema']['maximum'] = self.max_limit
                item['schema']['default'] = self.default_limit
                break

        return result

    def get_paginated_response_schema(self, schema: dict[str, Any]) -> dict[str, Any]:
        return build_object_type(
            properties={
                'count': build_basic_type(OpenApiTypes.INT),
                'limit': build_basic_type(OpenApiTypes.INT),
                'offset': build_basic_type(OpenApiTypes.INT),
                'results': schema,
            },
            required=['count', 'limit', 'offset', 'results'],
        )
