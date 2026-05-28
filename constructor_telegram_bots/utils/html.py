from django.utils.html import format_html


def format_html_link(url: str, text: str | None = None) -> str:
    return format_html(
        f'<a href="{url}" target="_blank" style="font-weight: 600;">{text or url}</a>'
    )
