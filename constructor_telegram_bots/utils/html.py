from django.utils.html import format_html


def format_html_link(url: str, text: str | None = None) -> str:
    return format_html(
        '<a href="{url}" target="_blank" style="font-weight: 500;">{text}</a>',
        url=url,
        text=text or url,
    )
