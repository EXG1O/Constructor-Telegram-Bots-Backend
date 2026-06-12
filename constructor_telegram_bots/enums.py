from enum import StrEnum


class Mode(StrEnum):
    TEST = 'test'
    DEBUG = 'debug'
    LOCALE = 'locale'
    PRODUCTION = 'production'
