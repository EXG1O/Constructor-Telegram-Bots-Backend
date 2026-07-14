from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from django.views.decorators.vary import vary_on_headers

from rest_framework.mixins import ListModelMixin
from rest_framework.viewsets import GenericViewSet

from constructor_telegram_bots.pagination import LimitOffsetPagination

from .models import Donation, Method, Section
from .serializers import DonationSerializer, MethodSerializer, SectionSerializer


@method_decorator(cache_page(3600), name='dispatch')
class DonationViewSet(ListModelMixin, GenericViewSet[Donation]):
    authentication_classes = []
    permission_classes = []
    queryset = Donation.objects.all()
    serializer_class = DonationSerializer
    pagination_class = LimitOffsetPagination


@method_decorator(cache_page(3600), name='dispatch')
@method_decorator(vary_on_headers('Accept-Language'), name='dispatch')
class SectionViewSet(ListModelMixin, GenericViewSet[Section]):
    authentication_classes = []
    permission_classes = []
    queryset = Section.objects.all()
    serializer_class = SectionSerializer


@method_decorator(cache_page(3600), name='dispatch')
class MethodViewSet(ListModelMixin, GenericViewSet[Method]):
    authentication_classes = []
    permission_classes = []
    queryset = Method.objects.all()
    serializer_class = MethodSerializer
