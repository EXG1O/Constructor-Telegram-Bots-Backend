from django_filters.rest_framework import BaseInFilter, ChoiceFilter, NumberFilter


class NumberInFilter(BaseInFilter, NumberFilter):
    pass


class ChoiceInFilter(BaseInFilter, ChoiceFilter):
    pass
