from django.db.models import Model, QuerySet
from django.utils.translation import gettext as _

from rest_framework.exceptions import ValidationError
from rest_framework.pagination import LimitOffsetPagination as BaseLimitOffsetPagination
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from drf_spectacular.plumbing import build_basic_type, build_object_type
from drf_spectacular.types import OpenApiTypes

from typing import Any


class LimitOffsetPagination(BaseLimitOffsetPagination):
    max_limit = 100

    def paginate_queryset[TModel: Model, TRow = TModel](
        self,
        queryset: QuerySet[TModel, TRow],
        request: Request,
        view: APIView | None = None,
    ) -> list[TRow] | None:
        result: list[TRow] | None = super().paginate_queryset(queryset, request, view)

        if result is None:
            raise ValidationError(
                {self.limit_query_param: _('Этот параметр запроса обязателен.')}
            )

        return result

    def get_paginated_response(self, data: list[dict[str, Any]]) -> Response:
        return Response({'count': self.count, 'results': data})

    def get_schema_operation_parameters(self, view: APIView) -> list[dict[str, Any]]:
        result: list[dict[str, Any]] = super().get_schema_operation_parameters(view)

        for item in result:
            if item['name'] == self.limit_query_param:
                item['required'] = True
                item['schema']['maximum'] = self.max_limit
                break

        return result

    def get_paginated_response_schema(self, schema: dict[str, Any]) -> dict[str, Any]:
        return build_object_type(
            properties={'count': build_basic_type(OpenApiTypes.INT), 'results': schema},
            required=['count', 'results'],
        )
