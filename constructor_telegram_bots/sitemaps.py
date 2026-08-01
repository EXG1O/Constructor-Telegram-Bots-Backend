from django.contrib.sitemaps import Sitemap
from django.utils import translation


class MainSitemap(Sitemap[str]):
    priority = 0.5
    changefreq = 'daily'
    i18n = True
    alternates = True

    def items(self) -> list[str]:
        return [
            '/',
            '/instruction/',
            '/terms-of-service/',
            '/privacy-policy/',
        ]

    def location(self, item: str) -> str:
        language: str = translation.get_language()

        if language == 'en':
            return item

        return f'/{language}{item}'
