from django_filters.rest_framework import BaseInFilter, NumberFilter


class NumberInFilter(BaseInFilter, NumberFilter):
    pass
