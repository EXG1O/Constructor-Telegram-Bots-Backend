from enum import StrEnum


class TextType(StrEnum):
    HTML = 'HTML'
    MARKDOWN = 'MarkdownV2'


class KeyboardButtonStyle(StrEnum):
    DEFAULT = 'default'
    PRIMARY = 'primary'
    SUCCESS = 'success'
    DANGER = 'danger'
