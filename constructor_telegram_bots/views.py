from django.conf import settings
from django.http import HttpRequest, HttpResponse
from django.shortcuts import render
from django.utils import translation

from typing import Any
import json


def frontend(request: HttpRequest) -> HttpResponse:
    path: str = request.path_info
    translation_data: dict[str, Any] = {}

    with open(
        settings.STATIC_ROOT
        / 'frontend/locale'
        / translation.get_language()
        / 'global.json'
    ) as file:
        file_data: Any = json.load(file)

        if isinstance(file_data, dict):
            translation_data.update(file_data)

    return render(
        request,
        'frontend/index.html',
        {
            'path_without_lang': (
                path[3:]
                if path.startswith(
                    tuple(f'/{code}' for code, label in settings.LANGUAGES)
                )
                else path
            ),
            'seo': translation_data.get('seo'),
        },
    )
