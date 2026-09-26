from django.db.models import Count, Q
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page

from rest_framework import serializers, status
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from drf_spectacular.utils import extend_schema, inline_serializer

from ..models import TelegramBot, User


class StatsAPIView(APIView):
    authentication_classes = []
    permission_classes = []

    @extend_schema(
        responses={
            status.HTTP_200_OK: inline_serializer(
                name='TelegramBotStatsResponse',
                fields={
                    'telegram_bots': inline_serializer(
                        name='TelegramBotStats',
                        fields={
                            'total': serializers.IntegerField(read_only=True),
                            'enabled': serializers.IntegerField(read_only=True),
                        },
                    ),
                    'users': inline_serializer(
                        name='UserStats',
                        fields={
                            'total': serializers.IntegerField(read_only=True),
                        },
                    ),
                },
            )
        },
    )
    @method_decorator(cache_page(3600))
    def get(self, request: Request) -> Response:
        return Response(
            {
                'telegram_bots': TelegramBot.objects.aggregate(
                    total=Count('id'),
                    enabled=Count('id', filter=Q(must_be_enabled=True)),
                ),
                'users': {
                    'total': User.objects.count(),
                },
            }
        )
