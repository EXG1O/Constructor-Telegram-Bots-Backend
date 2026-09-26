from drf_standardized_errors.openapi import AutoSchema as BaseAutoSchema

from typing import Final
import re


class AutoSchema(BaseAutoSchema):
    _ACTION_MAP: Final[dict[str, str]] = {
        'list': 'get',
        'retrieve': 'get',
        'destroy': 'delete',
    }
    _METHOD_MAP: Final[dict[str, str]] = {
        'put': 'update',
        'patch': 'partial_update',
    }

    def _with_prefix(self, value: str) -> str:
        return f'{self.get_tags()[0]}-{value}'

    def get_operation_id(self) -> str:
        name: str = re.sub(r'(ViewSet|APIView|View)$', '', self.view.__class__.__name__)
        action: str | None = getattr(self.view, 'action', None)
        method_lower: str = self.method.lower()
        mapped_method: str = self._METHOD_MAP.get(method_lower, method_lower)

        if action:
            if action not in (
                'list',
                'retrieve',
                'create',
                'update',
                'partial_update',
                'destroy',
            ):
                return self._with_prefix(f'{mapped_method}_{name}_{action}')

            parts: list[str] = [self._ACTION_MAP.get(action, action), name]

            if action == 'list':
                parts.append('list')

            return self._with_prefix('_'.join(parts))

        return self._with_prefix(f'{mapped_method}_{name}')

    def get_tags(self) -> list[str]:
        tags: list[str] = super().get_tags()
        tags[0] = tags[0].replace('-', '_')
        return tags
