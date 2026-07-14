from django.http import HttpRequest, HttpResponse
from django.utils import translation
from django.utils.cache import patch_vary_headers
from django.utils.deprecation import MiddlewareMixin


class LocaleMiddleware(MiddlewareMixin):
    def process_request(self, request: HttpRequest) -> None:
        translation.activate(
            translation.get_language_from_request(request, check_path=True)
        )
        request.LANGUAGE_CODE = translation.get_language()

    def process_response(
        self, request: HttpRequest, response: HttpResponse
    ) -> HttpResponse:
        response.headers.setdefault('Content-Language', translation.get_language())
        patch_vary_headers(response, ['Accept-Language'])
        return response
