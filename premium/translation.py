from modeltranslation.translator import TranslationOptions, register

from .models import SubscriptionPrice


@register(SubscriptionPrice)
class SubscriptionPriceTranslationOptions(TranslationOptions):
    fields = ['badge']
